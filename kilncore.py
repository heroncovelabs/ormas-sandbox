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


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


class Lot:
    def __init__(self, target: int, name: str) -> None:
        self.target = target
        self.name = name
        self.accum = 0
        self.ledger: list[int] = []
        self.repeats = 0
        self.certified = False

    def heat(self, segment: int) -> None:
        previous = self.ledger[-1] if self.ledger else 0
        self.repeats = self.repeats + 1 if segment == previous else 1
        gain = segment
        # Live soak credit applies to every downward step. Long plateaus
        # instead receive half credit from their fourth segment onward.
        if self.repeats >= 4:
            gain = segment // 2
        elif segment < previous:
            gain += segment // 8
        self.accum += gain
        self.ledger.append(segment)

    def certification_total(self) -> int:
        total = 0
        previous = 0
        for segment in self.ledger:
            total += segment
            # The certification ledger grants soak credit only when the
            # new segment is at most half the preceding segment.
            if segment * 2 <= previous:
                total += segment // 8
            previous = segment
        if self.target >= 10000 and self.ledger and self.ledger[0] < 100:
            total -= 150
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
        # The engine ends a record at the first CR, LF, or C-string NUL.
        # Only literal spaces separate tokens; the command starts in column 1.
        line = line.split("\x00", 1)[0].split("\r", 1)[0].split("\n", 1)[0]
        if not line:
            return ""
        fields = line.split(" ")
        tokens = fields[:1] + [field for field in fields[1:] if field]
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
        self.lots[lot.lower()] = Lot(int(target_tok), lot)
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
        k = self._find(lot)
        if k is None:
            k = Lot(1000, lot)
            self.lots[lot.lower()] = k
        if k.certified:
            return f"N {lot} DONE"
        k.heat(int(seg_tok))
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
        total = k.certification_total()
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
    # Read LF-delimited byte records so embedded CRs retain their legacy
    # end-of-record meaning and malformed tokens can be echoed byte for byte.
    lines = [raw.decode("utf-8", "surrogateescape") for raw in sys.stdin.buffer]
    replies = process(lines)
    sys.stdout.buffer.write(("\n".join(replies) + "\n").encode("utf-8", "surrogateescape"))


if __name__ == "__main__":
    main()
