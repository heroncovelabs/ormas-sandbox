"""KilnCore firing-lot controller, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
firing commands on stdin (``L`` registers a firing lot with a target
heatwork number, ``H`` applies a firing segment, ``C`` certifies the lot
from its segment ledger), writes one reply per command and an ``X``
trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).
"""

from __future__ import annotations

import sys

ID_MAX = 8
TARGET_MIN = 100
NO_LOT = "????????"
# Engine behavior not in the spec:
WALK_IN_TARGET = 1000  # H for an unregistered lot opens it with this target
PLATEAU_RUN = 4  # from this many identical segments in a row, live gain halves
COLD_TARGET = 10000  # big lots whose first segment is below COLD_SEG ...
COLD_SEG = 100
COLD_PENALTY = 150  # ... certify this much lower


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
        self.run = self.run + 1 if seg == prev else 1
        if self.run >= PLATEAU_RUN:
            self.accum += seg // 2
        elif prev is not None and seg < prev:
            self.accum += seg + seg // 8
        else:
            self.accum += seg
        self.ledger.append(seg)

    def cert_total(self) -> int:
        total = 0
        prev = None
        for seg in self.ledger:
            total += seg
            if prev is not None and 2 * seg <= prev:
                total += seg // 8
            prev = seg
        if self.target >= COLD_TARGET and self.ledger and self.ledger[0] < COLD_SEG:
            total -= COLD_PENALTY
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
        # The engine splits on spaces only; tabs stay inside tokens.
        # A leading space (or a whitespace-only line) leaves no command letter.
        tokens = [t for t in line.split(" ") if t]
        if line.startswith(" "):
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
            k = self.lots[tokens[1].lower()] = Lot(tokens[1], WALK_IN_TARGET)
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
        line = raw.rstrip("\r\n")
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
