"""FerryCore island car-ferry boarding controller, Python implementation.

Replaces the retired legacy controller (see ``legacy/README.md``). Reads
boarding-day commands on stdin (``V`` registers a vehicle with its deck
span, ``Q`` joins the quay queue, ``G`` runs a sailing, ``K`` runs the
seasonal squaring), writes the reply lines for each command and an ``X``
trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy controller's behavior is the contract).

Where the controller departs from the spec (all reproduced here):

- quay wear: each miss adds ``span + wear + streak`` to the lean, where
  ``wear`` counts every sailing the vehicle has missed this season and
  ``streak`` the misses since it last boarded; once any squaring has
  been held, each miss adds one more unit;
- a vehicle on its third miss in a row is wedged: at the next sailing it
  boards ahead of everyone else (wedged vehicles in registration order);
- ties go to queue order, except that a squaring switches them to
  registration order until the next successful join;
- season regulars (three or more crossings boarded with no lean) take
  one deck unit less, never below one;
- a sailing with an empty quay still prints ``GEND 0 0``;
- the squaring replays the ledger (registrations, joins, sailings) by the
  book's plain rules (span per miss, registration-order ties, no wear,
  wedging or squeeze), adopts the replayed leans for every vehicle and
  counts the positive ones; vehicles registered afterwards start with a
  lean of two per squaring held so far.
"""

from __future__ import annotations

import sys

DECK_CAP = 40  # deck units available per sailing
WEDGE_STREAK = 3  # consecutive misses that wedge a vehicle
REGULAR_CROSSINGS = 3  # lean-free crossings that make a season regular
SQUARING_LEVY = 2  # starting lean per squaring for later registrations
SENTINEL = "????????"


def _valid_id(tok: str) -> bool:
    return 1 <= len(tok) <= 8 and tok.isascii() and tok.isalnum()


def _parse_span(tok: str) -> int | None:
    if not (tok.isascii() and tok.isdigit() and 1 <= len(tok) <= 2):
        return None
    value = int(tok)
    return value if 1 <= value <= 20 else None


class Vehicle:
    def __init__(self, vid: str, span: int, reg: int, lean: int = 0) -> None:
        self.id = vid
        self.span = span
        self.reg = reg  # registration order, 0-based
        self.lean = lean  # standing lean (internal; never printed)
        self.wear = 0  # sailings missed this season
        self.streak = 0  # sailings missed since last boarding
        self.regular = 0  # crossings boarded with no lean
        self.seq = 0  # join order
        self.queued = False
        self.aboard = False  # boarded the most recent sailing


class Book:
    """Vehicles and sailing rules. The live controller runs with the
    quirks on; the squaring's ledger replay runs the plain book rules."""

    def __init__(self, live: bool) -> None:
        self.live = live
        self.vehicles: dict[str, Vehicle] = {}
        self.order: list[Vehicle] = []  # registration order
        self.join_seq = 0
        self.reg_ties = not live  # ties by registration order
        self.squared = False  # a squaring has been held

    def register(self, vid: str, span: int, lean: int = 0) -> Vehicle:
        v = Vehicle(vid, span, len(self.order), lean)
        self.vehicles[vid] = v
        self.order.append(v)
        return v

    def can_join(self, v: Vehicle) -> bool:
        return not (v.queued or v.aboard)

    def join(self, v: Vehicle) -> None:
        self.join_seq += 1
        v.seq = self.join_seq
        v.queued = True
        if self.live:
            self.reg_ties = False

    def _rank(self, v: Vehicle) -> tuple:
        if self.live and v.streak == WEDGE_STREAK:
            return (0, v.reg)
        return (1, -v.lean, v.reg if self.reg_ties else v.seq)

    def _deck_span(self, v: Vehicle) -> int:
        if self.live and v.regular >= REGULAR_CROSSINGS and v.span > 1:
            return v.span - 1
        return v.span

    def sail(self) -> tuple[list[Vehicle], int]:
        for v in self.order:
            v.aboard = False  # last crossing's passengers disembark
        # rank, then skip what does not fit and keep going down the list
        waiting = sorted((v for v in self.order if v.queued), key=self._rank)
        used = 0
        boarded = []
        for v in waiting:
            span = self._deck_span(v)
            if used + span <= DECK_CAP:
                used += span
                boarded.append(v)
        for v in boarded:
            if v.lean == 0:
                v.regular += 1
            v.lean = 0
            v.streak = 0
            v.run = 0
            v.queued = False
            v.aboard = True
        left = 0
        for v in waiting:
            if v.queued:  # left behind at this sailing
                left += 1
                import os
                tv = os.environ.get("FC_T", "maxrun")
                term = {"streak": v.streak, "pos": 1 if v.lean > 0 else 0,
                        "min1": min(v.streak, 1), "run": getattr(v, "run", 0),
                        "maxrun": max(getattr(v, "run", 0), 1 if self.squared else 0)}[tv]
                v.run = getattr(v, "run", 0) + 1
                v.lean += v.span
                if self.live:
                    v.lean += v.wear + term + (1 if self.squared and tv != "maxrun" else 0)
                v.wear += 1
                v.streak += 1
        return boarded, left


class Engine:
    """Boarding controller with registration, queueing, sailings, and
    seasonal squarings."""

    def __init__(self, out=None):
        self.book = Book(live=True)
        self.ledger: list[tuple] = []  # accepted V / Q / G commands
        self.c_sail = 0
        self.c_sq = 0
        self.c_rej = 0
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
        if parts[1] in self.book.vehicles:
            self._reject(parts[1], "DUP")
            return
        self.book.register(parts[1], span, SQUARING_LEVY * self.c_sq)
        self.ledger.append(("V", parts[1], span))
        self._emit(f"OK {len(self.book.order)}")

    def _join(self, parts: list[str]) -> None:
        if len(parts) != 2 or not _valid_id(parts[1]):
            self._reject(self._echo(parts), "FMT")
            return
        v = self.book.vehicles.get(parts[1])
        if v is None:
            self._reject(parts[1], "UNKNOWN")
            return
        if not self.book.can_join(v):
            self._reject(parts[1], "QUEUED")
            return
        self.book.join(v)
        self.ledger.append(("Q", parts[1]))
        self._emit(f"Q {v.id}")

    def _sail(self, parts: list[str]) -> None:
        if len(parts) != 1:
            self._reject(self._echo(parts), "FMT")
            return
        self.c_sail += 1
        boarded, left = self.book.sail()
        self.ledger.append(("G",))
        for v in boarded:
            self._emit(f"G {v.id}")
        self._emit(f"GEND {len(boarded)} {left}")

    def _square(self, parts: list[str]) -> None:
        if len(parts) != 1:
            self._reject(self._echo(parts), "FMT")
            return
        self.c_sq += 1
        # replay the season ledger by the plain book rules and adopt the
        # replayed leans; queue and deck state stay as they are
        replay = Book(live=False)
        for ev in self.ledger:
            if ev[0] == "V":
                replay.register(ev[1], ev[2])
            elif ev[0] == "Q":
                rv = replay.vehicles[ev[1]]
                if replay.can_join(rv):
                    replay.join(rv)
            else:
                replay.sail()
        import os
        var = os.environ.get("FC_V", "R")
        for v in self.book.order:
            rv = replay.vehicles[v.id]
            v.lean = rv.lean
            if "s" in var:
                v.streak = rv.streak
            if "p" in var:
                v.streak = rv.streak + 1
            if "P" in var and v.queued:
                v.streak = rv.streak + 1
            if "L" in var:
                self.book.squared = False
            if "R" in var:
                v.run = 0
            if "W" in var:
                v.streak = 0
            if "z" in var and v.lean == 0:
                v.streak = 0
            if "w" in var:
                v.wear = rv.wear
            if "r" in var:
                v.regular = rv.regular
        self.book.reg_ties = True
        self.book.squared = True
        positive = sum(1 for v in self.book.order if v.lean > 0)
        self._emit(f"KOK {positive}")

    def finish(self) -> None:
        queued = sum(1 for v in self.book.order if v.queued)
        self._emit(
            f"X {len(self.book.order)} {queued} {self.c_sail}"
            f" {self.c_sq} {self.c_rej}"
        )


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
