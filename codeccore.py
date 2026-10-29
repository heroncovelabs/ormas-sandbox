"""CodecCore VX interchange codec, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads codec
commands on stdin (``E`` encodes a field list to a 48-column VX record,
``D`` decodes a record back to fields), writes one reply per command and
an ``X`` trailer at EOF. Format reference: ``docs/SPEC.md`` (note the
drift warning at the top of that file; the legacy engine's behavior is the
contract).
"""

from __future__ import annotations

import sys
from collections.abc import Iterable

RECLEN = 48
ACCT_WIDTH = 10
AMOUNT_WIDTH = 11
MEMO_WIDTH = 15
MEMO_MAX = 20

_WEIGHTS = (2, 5, 3)
_B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

NO_ACCT = "?" * ACCT_WIDTH


def check_char(record: str) -> str:
    """Check character over the first 47 columns (positions 0 to 46)."""
    total = sum(ord(c) * _WEIGHTS[i % 3] for i, c in enumerate(record[: RECLEN - 1]))
    return _B36[total % 36]


def _days_in_month(year: int, month: int) -> int:
    days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if month == 2 and year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        return 29
    return days[month - 1]


def _digits(field: str) -> bool:
    return bool(field) and all("0" <= c <= "9" for c in field)


def _valid_date(field: str) -> bool:
    if len(field) != 8 or not _digits(field):
        return False
    year, month, day = int(field[:4]), int(field[4:6]), int(field[6:8])
    return year >= 1900 and 1 <= month <= 12 and 1 <= day <= _days_in_month(year, month)


def _valid_acct(token: str) -> bool:
    return 1 <= len(token) <= ACCT_WIDTH and all(
        "0" <= c <= "9" or "A" <= c <= "Z" or "a" <= c <= "z" for c in token
    )


def _printable(text: str) -> bool:
    return all(33 <= ord(c) <= 126 for c in text)


class Engine:
    """Bidirectional VX codec with batch counters."""

    def __init__(self) -> None:
        self.encoded = 0
        self.decoded = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        if line == "E" or line.startswith("E "):
            # The legacy tokenizer separates fields on literal spaces.
            reply = self._encode([token for token in line.split(" ") if token])
        elif line == "D" or line.startswith("D "):
            reply = self._decode(line[2:])
        else:
            reply = "R FMT"
        if reply.startswith("V "):
            self.encoded += 1
        elif reply.startswith("P "):
            self.decoded += 1
        else:
            self.rejected += 1
        return reply

    def trailer(self) -> str:
        return f"X {self.encoded} {self.decoded} {self.rejected}"

    def _encode(self, tokens: list[str]) -> str:
        echo = NO_ACCT
        if len(tokens) >= 2 and _valid_acct(tokens[1]):
            echo = tokens[1]
        if len(tokens) < 5:
            return f"R FMT {echo}"
        acct, amount, date, memo = tokens[1:5]
        if not _valid_acct(acct):
            return f"R FMT {NO_ACCT}"
        if not 1 <= len(amount) <= AMOUNT_WIDTH or not _digits(amount):
            return f"R FMT {acct}"
        if not _valid_date(date):
            return f"R FMT {acct}"
        if memo == "_":
            memo = ""
        if not _printable(memo):
            return f"R FMT {acct}"
        if len(memo) > MEMO_MAX:
            return f"R FMT {acct}"
        # Extended memos keep their first twelve and final two characters.
        stored = memo if len(memo) <= MEMO_WIDTH else memo[:12] + "~" + memo[-2:]
        flag = "H" if int(amount) > 10_000_000 and date[4:6] == "01" else "N"
        body = (
            "VX"
            + acct.rjust(ACCT_WIDTH, "*")
            + amount.zfill(AMOUNT_WIDTH)
            + date
            + stored.ljust(MEMO_WIDTH, ".")
            + flag
        )
        return "V " + body + check_char(body)

    def _decode(self, arg: str) -> str:
        # A space immediately after the fixed-width record starts ignored text.
        if arg[RECLEN : RECLEN + 1] == " ":
            arg = arg[:RECLEN]
        if len(arg) != RECLEN:
            return "R LEN"
        if arg[:2].upper() != "VX":
            return "R FMT"
        # Prefix case is normalized before checking; padding remains verbatim.
        record = "VX" + arg[2:]
        if record[RECLEN - 1] != "Z" and record[RECLEN - 1] != check_char(record):
            return "R CHK"
        acct = record[2:12].strip("* ")
        if not _valid_acct(acct):
            return "R FMT"
        amount = record[12:23]
        if not _digits(amount):
            return "R FMT"
        date = record[23:31]
        if date != "00000000" and not _valid_date(date):
            return "R FMT"
        memo = record[31:46].rstrip(".,")
        if not _printable(memo):
            return "R FMT"
        # The flag participates in the check sum and is otherwise opaque.
        return f"P {acct} {int(amount)} {date} {memo or '_'}"


def process(lines: Iterable[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        # Input is a C string terminated by the first NUL, CR, or LF.
        line = raw.partition("\0")[0].partition("\r")[0].partition("\n")[0]
        if not line:
            continue
        replies.append(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    # Match the engine's 4096-byte fgets buffer and byte-based columns.
    chunks = iter(lambda: sys.stdin.buffer.readline(4095), b"")
    process((raw.decode("latin-1") for raw in chunks), out=sys.stdout)


if __name__ == "__main__":
    main()
