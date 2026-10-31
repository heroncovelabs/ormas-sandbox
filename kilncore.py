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

import string
import sys

ID_MAX = 8
TARGET_MIN = 100
# Target assigned to a lot created implicitly by a segment for an unknown id
# (legacy engine: "H w2 400" then "C w2" reports SHORT 600).
IMPLICIT_TARGET = 1000
SEG_MAX_DIGITS = 4
LOT_LIMIT = 1024
LEDGER_LIMIT = 1024
NO_LOT = "????????"

# ASCII-only case folding for lot identity (ids are validated as ASCII).
_ASCII_FOLD = {ord(c): ord(c) + 32 for c in string.ascii_uppercase}


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


def _lot_key(token: str) -> str:
    """Canonical lot identity: lots are matched case-insensitively."""
    return token.translate(_ASCII_FOLD)


def _clip(line: str) -> str:
    """The engine reads each line up to the first CR or NUL byte."""
    return line.split("\r", 1)[0].split("\x00", 1)[0]


def _tokenize(line: str) -> list[str]:
    """Split a line into command word and argument fields.

    The command word is everything before the first space, so a line with
    leading spaces or tabs has an unrecognized command. Argument fields are
    separated by runs of spaces only; tabs and other whitespace are ordinary
    characters. Surplus fields are kept here and ignored by the handlers.
    """
    head, _, rest = line.partition(" ")
    return [head] + [field for field in rest.split(" ") if field]


class Lot:
    def __init__(self, target: int) -> None:
        self.target = target
        self.accum = 0
        self.certified = False
        # Spelling used in replies: the id as first registered or first seen.
        self.ident = ""
        # Certification retains only the first LEDGER_LIMIT accepted segments.
        # Live heatwork and its transition state continue updating afterwards.
        self.ledger: list[int] = []
        self.previous = 0
        self.run_length = 0

    def heat(self, value: int) -> None:
        self.run_length = self.run_length + 1 if value == self.previous else 1
        credit = value
        if value < self.previous:
            credit += value // 8
        if self.run_length >= 4:
            credit //= 2
        self.accum += credit
        self.previous = value
        if len(self.ledger) < LEDGER_LIMIT:
            self.ledger.append(value)

    def certification_total(self) -> int:
        # Replay raw segments: only drops of at least half earn the soak
        # bonus, and repeated segments receive their full value.
        total = 0
        previous = 0
        for value in self.ledger:
            total += value
            if previous >= 2 * value:
                total += value // 8
            previous = value
        if self.target >= 10000 and self.ledger and self.ledger[0] < 100:
            total -= 150
        return total


class Engine:
    """Firing-lot controller with live heatwork, certification, and counters."""

    def __init__(self) -> None:
        self.lots: dict[str, Lot] = {}
        self._index: dict[str, Lot] = {}
        self.registered = 0
        self.segments = 0
        self.certs = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        line = _clip(line)
        if not line:
            return ""
        tokens = _tokenize(line)
        if not tokens:
            return ""
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
        return self._index.get(_lot_key(lot))

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
        if len(self.lots) >= LOT_LIMIT:
            return f"N {lot} FMT"
        new = Lot(int(target_tok))
        new.ident = tokens[1]
        self.lots[tokens[1]] = new
        self._index[_lot_key(tokens[1])] = new
        self.registered += 1
        return f"OK {len(self.lots)}"

    def _heat(self, tokens: list[str]) -> str:
        lot = tokens[1] if len(tokens) >= 2 else NO_LOT
        if len(tokens) < 3:
            return f"N {lot} FMT"
        if not _valid_id(tokens[1]):
            return f"N {lot} FMT"
        seg_tok = tokens[2]
        if not _digits(seg_tok) or not 1 <= len(seg_tok) <= SEG_MAX_DIGITS:
            return f"N {lot} SEG"
        k = self._find(tokens[1])
        if k is None:
            # Walk-ins occupy a lot slot without counting as registrations.
            if len(self.lots) >= LOT_LIMIT:
                return f"N {lot} FMT"
            k = Lot(IMPLICIT_TARGET)
            k.ident = tokens[1]
            self.lots[tokens[1]] = k
            self._index[_lot_key(tokens[1])] = k
        if k.certified:
            return f"N {lot} DONE"
        k.heat(int(seg_tok))
        self.segments += 1
        return f"W {k.ident} {k.accum}"

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
            return f"C {k.ident} PASS"
        return f"C {k.ident} SHORT {k.target - total}"


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
    # Split on LF only so a bare CR stays inside its record for _clip.
    data = sys.stdin.buffer.read().decode(
        sys.stdin.encoding or "utf-8", errors="surrogateescape"
    )
    process(data.split("\n"), out=sys.stdout)


if __name__ == "__main__":
    main()
