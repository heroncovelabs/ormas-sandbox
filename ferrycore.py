"""FerryCore island car-ferry boarding controller, Python implementation.

Replaces the retired legacy controller (see ``legacy/README.md``). Reads
boarding-day commands on stdin (``V`` registers a vehicle with its deck
span, ``Q`` joins the quay queue, ``G`` runs a sailing, ``K`` runs the
seasonal squaring), writes the reply lines for each command and an ``X``
trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy controller's behavior is the contract).
"""

from __future__ import annotations

import sys

DECK_CAP = 40  # deck units available per sailing
SENTINEL = "????????"

_REGISTRATION_LEVY = 2
_FIT_CREDIT = 1
_FIT_STREAK = 3
_PRIORITY_EVERY = 3


def _valid_id(tok: str) -> bool:
    return 1 <= len(tok) <= 8 and tok.isascii() and tok.isalnum()


def _parse_span(tok: str) -> int | None:
    if not (tok.isascii() and tok.isdigit() and 1 <= len(tok) <= 2):
        return None
    value = int(tok)
    return value if 1 <= value <= 20 else None


class Vehicle:
    def __init__(self, vid: str, span: int, reg: int) -> None:
        self.id = vid
        self.span = span
        self.reg = reg  # registration order, 0-based
        self.lean = 0  # standing lean (internal; never printed)
        self.queued = False
        self.aboard = False  # boarded the most recent sailing
        self.misses = 0
        self.wait = 0
        self.priority = False
        self.streak = 0
        self.join_seq = 0


class Engine:
    """Boarding controller with registration, queueing, sailings, and
    seasonal squarings."""

    def __init__(self, out=None):
        self.vehicles: dict[str, Vehicle] = {}
        self.order: list[Vehicle] = []  # registration order
        self.c_sail = 0
        self.c_sq = 0
        self.c_rej = 0
        self.join_clock = 0
        self.registration_ties = False
        self.ledger: list[tuple[int, int]] = []
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, echo: str, code: str) -> None:
        self.c_rej += 1
        self._emit(f"N {echo} {code}")

    def _echo(self, parts: list[str]) -> str:
        return parts[1] if len(parts) > 1 and _valid_id(parts[1]) else SENTINEL

    def handle(self, line: str) -> None:
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        kind = parts[0]
        if kind == "V":
            self._register(parts)
        elif kind == "Q":
            self._join(parts)
        elif kind == "G":
            self._sail(parts)
        elif kind == "K":
            self._square(parts)
        else:
            self._reject(self._echo(parts), "FMT")

    # ------------------------------------------------------------ commands

    def _register(self, parts: list[str]) -> None:
        if len(parts) != 3 or not _valid_id(parts[1]):
            self._reject(self._echo(parts), "FMT")
            return
        span = _parse_span(parts[2])
        if span is None:
            self._reject(parts[1], "SPAN")
            return
        if parts[1] in self.vehicles:
            self._reject(parts[1], "DUP")
            return
        v = Vehicle(parts[1], span, len(self.order))
        v.lean = _REGISTRATION_LEVY * self.c_sq
        self.vehicles[parts[1]] = v
        self.order.append(v)
        self.ledger.append((0, v.reg))
        self._emit(f"OK {len(self.order)}")

    def _join(self, parts: list[str]) -> None:
        if len(parts) != 2 or not _valid_id(parts[1]):
            self._reject(self._echo(parts), "FMT")
            return
        v = self.vehicles.get(parts[1])
        if v is None:
            self._reject(parts[1], "UNKNOWN")
            return
        if v.queued or v.aboard:
            self._reject(parts[1], "QUEUED")
            return
        v.queued = True
        self.join_clock += 1
        v.join_seq = self.join_clock
        self.registration_ties = False
        self.ledger.append((1, v.reg))
        self._emit(f"Q {v.id}")

    def _sail(self, parts: list[str]) -> None:
        if len(parts) != 1:
            self._reject(self._echo(parts), "FMT")
            return
        self.c_sail += 1
        for v in self.order:
            v.aboard = False  # last crossing's passengers disembark
        waiting = [v for v in self.order if v.queued]
        # An outstanding priority flag wins first.  Lean is next; before a
        # squaring, equal vehicles retain their latest queue order.
        waiting.sort(
            key=lambda v: (
                -int(v.priority),
                v.reg if v.priority else -v.lean,
                v.reg if self.registration_ties else v.join_seq,
            )
        )
        used = 0
        boarded = []
        for v in waiting:
            span = v.span
            if v.streak >= _FIT_STREAK:
                span = max(1, span - _FIT_CREDIT)
            if used + span <= DECK_CAP:
                used += span
                boarded.append(v)
                self._emit(f"G {v.id}")
        for v in boarded:
            if v.lean == 0:
                v.streak += 1
            v.lean = 0
            v.queued = False
            v.aboard = True
            v.priority = False
        left = 0
        for v in waiting:
            if v.queued:  # left behind at this sailing
                left += 1
                if v.priority:
                    v.priority = False
                v.wait += 1
                v.lean += v.span + v.wait
                v.misses += 1
                if _PRIORITY_EVERY and v.misses == _PRIORITY_EVERY:
                    v.priority = True
        self.ledger.append((2, 0))
        self._emit(f"GEND {len(boarded)} {left}")

    def _square(self, parts: list[str]) -> None:
        if len(parts) != 1:
            self._reject(self._echo(parts), "FMT")
            return
        self.c_sq += 1
        # Replay the season ledger into a separate book.  Its queue and
        # priority flags shadow the live flags only for this replay.
        queued = [False] * len(self.order)
        aboard = [False] * len(self.order)
        priority = [False] * len(self.order)
        misses = [0] * len(self.order)
        wait = [0] * len(self.order)
        streak = [0] * len(self.order)
        lean = [0] * len(self.order)
        for kind, reg in self.ledger:
            if kind == 0:
                lean[reg] = 0
            elif kind == 1:
                if not queued[reg] and not aboard[reg]:
                    queued[reg] = True
            else:
                for i in range(len(self.order)):
                    aboard[i] = False
                self._replay_sail(queued, streak, lean)
        for i, v in enumerate(self.order):
            v.lean = lean[i]
        positive = sum(1 for value in lean if value > 0)
        self.registration_ties = True
        self._emit(f"KOK {positive}")

    def _replay_sail(self, queued, streak, lean) -> None:
        waiting = [i for i in range(len(self.order)) if queued[i]]
        waiting.sort(key=lambda i: (-lean[i], i))
        used = 0
        boarded = []
        for i in waiting:
            span = self.order[i].span
            if used + span <= DECK_CAP:
                used += span
                boarded.append(i)
        for i in boarded:
            streak[i] += 1
            lean[i] = 0
            queued[i] = False
        for i in waiting:
            if queued[i]:
                lean[i] += self.order[i].span

    def finish(self) -> None:
        queued = sum(1 for v in self.order if v.queued)
        self._emit(
            f"X {len(self.order)} {queued} {self.c_sail}"
            f" {self.c_sq} {self.c_rej}"
        )


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
