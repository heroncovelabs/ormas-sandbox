"""KilnCore firing-lot controller, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
firing commands on stdin (``L`` registers a firing lot with a target
heatwork number, ``H`` applies a firing segment, ``C`` certifies the lot
from its segment ledger), writes one reply per command and an ``X``
trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).

Where the engine departs from the spec (reproduced here):

- Lot lookups are case-insensitive; replies name the lot as first seen,
  rejects echo the line's token.
- Lines are cut at the first CR, LF or NUL and split on runs of spaces
  only; extra tokens after the documented ones are ignored.
- A segment of 0 is accepted (it still counts as a segment).
- ``H`` for an unknown lot walks the lot in with a default target of
  1000 (it counts toward ``OK`` lot counts but not toward the trailer's
  registrations). ``C`` for an unknown lot is still ``UNKNOWN``.
- Live ``W`` totals: a segment smaller than the previous one earns a
  soak bonus of ``seg // 8``; the fourth and later consecutive repeats of
  the same segment earn only ``seg // 2``.
- Certification recomputes from the ledger: soak bonus ``seg // 8`` only
  when the segment is at most half the previous one, no plateau
  reduction, and lots with a target of at least 10000 whose first segment
  was below 100 lose 150.
"""

from __future__ import annotations

import sys

ID_MAX = 8
TARGET_MIN = 100
WALK_IN_TARGET = 1000
COLD_TARGET = 10000
COLD_SEG = 100
COLD_PENALTY = 150
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


class Engine:
    """Firing-lot controller with live heatwork, certification, and counters."""

    def __init__(self) -> None:
        self.lots: dict[str, Lot] = {}
        self.registered = 0
        self.segments = 0
        self.certs = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        # The engine splits on runs of spaces only; leading whitespace
        # leaves an empty command letter.
        parts = line.split(" ")
        tokens = [parts[0]] + [t for t in parts[1:] if t]
        if tokens[0] == "L":
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
        seg = int(seg_tok)
        prev = k.ledger[-1] if k.ledger else None
        if prev is not None and seg == prev:
            k.run += 1
            k.accum += seg // 2 if k.run >= 3 else seg
        else:
            k.run = 0
            k.accum += seg
            if prev is not None and seg < prev:
                k.accum += seg // 8
        k.ledger.append(seg)
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
        total = 0
        prev = None
        for seg in k.ledger:
            total += seg
            if prev is not None and 2 * seg <= prev:
                total += seg // 8
            prev = seg
        if k.target >= COLD_TARGET and k.ledger and k.ledger[0] < COLD_SEG:
            total -= COLD_PENALTY
        k.certified = True
        self.certs += 1
        if total >= k.target:
            return f"C {k.name} PASS"
        return f"C {k.name} SHORT {k.target - total}"


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        # The engine cuts each line at its first CR, LF or NUL.
        line = raw.split("\n", 1)[0].split("\r", 1)[0].split("\0", 1)[0]
        if not line:
            continue
        replies.append(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    data = sys.stdin.buffer.read().decode("utf-8", errors="backslashreplace")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    replies = process(lines)
    sys.stdout.buffer.write("".join(r + "\n" for r in replies).encode("utf-8"))


if __name__ == "__main__":
    main()
