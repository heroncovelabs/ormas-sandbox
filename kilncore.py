"""KilnCore firing-lot controller, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
firing commands on stdin (``L`` registers a firing lot with a target
heatwork number, ``H`` applies a firing segment, ``C`` certifies the lot
from its segment ledger), writes one reply per command and an ``X``
trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).

Engine behavior that differs from the spec:

- Lot ids are looked up case-insensitively; replies use the id as first
  stored.
- Tokens beyond the documented arity are ignored.
- A segment of 0 (``0`` to ``0000``) is accepted; it breaks plateau runs.
- ``H`` for an unknown lot creates a walk-in lot with target 1000
  (counted in the ``OK`` lot count, not in the trailer's lot count).
- Live ``W`` gain: a step-down segment (lower than the previous one)
  earns ``seg // 8`` extra; the 4th and later identical consecutive
  segments earn only ``seg // 2``.
- Certification total: the plain segment sum plus ``seg // 8`` for each
  steep step-down (``2 * seg <= previous``); lots with target >= 10000
  whose first segment was below 100 lose 150.
"""

from __future__ import annotations

import sys

ID_MAX = 8
TARGET_MIN = 100
WALK_IN_TARGET = 1000
BIG_TARGET = 10000
SLOW_START = 100
SLOW_START_PENALTY = 150
PLATEAU_RUN = 4
NO_LOT = "????????"


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


class Lot:
    def __init__(self, name: str, target: int) -> None:
        self.name = name
        self.target = target
        self.accum = 0
        self.ledger: list[int] = []
        self.run = 0
        self.certified = False

    def apply(self, seg: int) -> None:
        prev = self.ledger[-1] if self.ledger else None
        if prev is not None and seg == prev and seg != 0:
            self.run += 1
        else:
            self.run = 1 if seg != 0 else 0
        if self.run >= PLATEAU_RUN:
            gain = seg // 2
        elif prev is not None and seg < prev:
            gain = seg + seg // 8
        else:
            gain = seg
        self.accum += gain
        self.ledger.append(seg)

    def cert_total(self) -> int:
        total = 0
        prev = None
        for seg in self.ledger:
            total += seg
            if prev is not None and 2 * seg <= prev:
                total += seg // 8
            prev = seg
        if self.target >= BIG_TARGET and self.ledger and self.ledger[0] < SLOW_START:
            total -= SLOW_START_PENALTY
        return total


class Engine:
    """Firing-lot controller with live heatwork, certification, and counters."""

    def __init__(self) -> None:
        self.lots: dict[str, Lot] = {}
        self.registered = 0
        self.segments = 0
        self.certs = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        # Only spaces separate tokens; a line must start with its command.
        pieces = line.split(" ")
        tokens = [piece for piece in pieces if piece]
        if not pieces[0]:
            reply = f"N {NO_LOT} FMT"
        elif tokens[0] == "L":
            reply = self._register(tokens)
        elif tokens[0] == "H":
            reply = self._heat(tokens)
        elif tokens[0] == "C":
            reply = self._certify(tokens)
        else:
            reply = f"N {NO_LOT} FMT"
        if reply.startswith("N "):
            self.rejected += 1
        return reply

    def trailer(self) -> str:
        return f"X {self.registered} {self.segments} {self.certs} {self.rejected}"

    def _find(self, lot: str) -> Lot | None:
        return self.lots.get(lot.lower())

    def _register(self, tokens: list[str]) -> str:
        lot = tokens[1] if len(tokens) >= 2 else NO_LOT
        if len(tokens) < 3:
            return f"N {lot} FMT"
        if not _valid_id(tokens[1]):
            return f"N {lot} FMT"
        target_tok = tokens[2]
        if (
            not _digits(target_tok)
            or not 3 <= len(target_tok) <= 5
            or int(target_tok) < TARGET_MIN
        ):
            return f"N {lot} TARGET"
        if self._find(tokens[1]) is not None:
            return f"N {lot} DUP"
        self.lots[tokens[1].lower()] = Lot(tokens[1], int(target_tok))
        self.registered += 1
        return f"OK {len(self.lots)}"

    def _heat(self, tokens: list[str]) -> str:
        lot = tokens[1] if len(tokens) >= 2 else NO_LOT
        if len(tokens) < 3:
            return f"N {lot} FMT"
        if not _valid_id(tokens[1]):
            return f"N {lot} FMT"
        seg_tok = tokens[2]
        if not _digits(seg_tok) or len(seg_tok) > 4:
            return f"N {lot} SEG"
        k = self._find(tokens[1])
        if k is None:
            k = Lot(tokens[1], WALK_IN_TARGET)
            self.lots[tokens[1].lower()] = k
        if k.certified:
            return f"N {lot} DONE"
        k.apply(int(seg_tok))
        self.segments += 1
        return f"W {k.name} {k.accum}"

    def _certify(self, tokens: list[str]) -> str:
        lot = tokens[1] if len(tokens) >= 2 else NO_LOT
        if len(tokens) < 2:
            return f"N {lot} FMT"
        if not _valid_id(tokens[1]):
            return f"N {lot} FMT"
        k = self._find(tokens[1])
        if k is None:
            return f"N {lot} UNKNOWN"
        if k.certified:
            return f"N {lot} DONE"
        total = k.cert_total()
        k.certified = True
        self.certs += 1
        if total >= k.target:
            return f"C {k.name} PASS"
        return f"C {k.name} SHORT {k.target - total}"


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        # The engine ends a line at the first carriage return.
        line = raw.rstrip("\n").split("\r", 1)[0]
        if not line:
            continue
        reply = engine.handle(line)
        if reply:
            replies.append(reply)
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    process(sys.stdin.readlines(), out=sys.stdout)


if __name__ == "__main__":
    main()
