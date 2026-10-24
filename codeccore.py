"""CodecCore VX interchange codec, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads codec
commands on stdin (``E`` encodes a field list to a 48-column VX record,
``D`` decodes a record back to fields), writes one reply per command and
an ``X`` trailer at EOF. Format reference: ``docs/SPEC.md`` (note the
drift warning at the top of that file; the legacy engine's behavior is the
contract).
"""

from __future__ import annotations

import re
import sys

RECLEN = 48
ACCT_WIDTH = 10
AMOUNT_WIDTH = 11
MEMO_WIDTH = 15
MEMO_MAX = 15
MEMO_SQUEEZE_MAX = 20
AUDIT_THRESHOLD = 10000000
CHECK_WILDCARD = "Z"
NULL_DATE = "00000000"

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


def _valid_date(field: str) -> bool:
    if len(field) != 8 or not _ascii_digits(field):
        return False
    year, month, day = int(field[:4]), int(field[4:6]), int(field[6:8])
    return year >= 1900 and 1 <= month <= 12 and 1 <= day <= _days_in_month(year, month)


def _ascii_digits(text: str) -> bool:
    return text.isascii() and text.isdigit()


def _ascii_alnum(text: str) -> bool:
    return text.isascii() and text.isalnum()


def _valid_acct(token: str) -> bool:
    return 1 <= len(token) <= ACCT_WIDTH and _ascii_alnum(token)


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
            # The engine splits on single spaces only (a tab stays in the token).
            reply = self._encode([t for t in line.split(" ") if t])
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
        # Tokens past the memo are ignored.
        if len(tokens) < 5:
            return f"R FMT {echo}"
        acct, amount, date, memo = tokens[1:5]
        if not _valid_acct(acct):
            return f"R FMT {NO_ACCT}"
        if not 1 <= len(amount) <= AMOUNT_WIDTH or not _ascii_digits(amount):
            return f"R FMT {acct}"
        if not _valid_date(date):
            return f"R FMT {acct}"
        if memo == "_":
            memo = ""
        if not _printable(memo):
            return f"R FMT {acct}"
        if len(memo) > MEMO_SQUEEZE_MAX:
            return f"R FMT {acct}"
        stored = memo
        if len(memo) > MEMO_MAX:
            # Overlong memos are squeezed: first 12, a tilde, last 2.
            stored = memo[:12] + "~" + memo[-2:]
        # High-value January records carry the audit flag.
        flag = "H" if date[4:6] == "01" and int(amount) > AUDIT_THRESHOLD else "N"
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
        # Anything after the record and a separating space is ignored.
        if len(arg) > RECLEN and arg[RECLEN] == " ":
            arg = arg[:RECLEN]
        if len(arg) != RECLEN:
            return "R LEN"
        # The prefix is case-insensitive; the check covers it uppercased.
        record = arg[:2].upper() + arg[2:]
        if record[:2] != "VX":
            return "R FMT"
        check = record[RECLEN - 1]
        if check != CHECK_WILDCARD and check != check_char(record):
            return "R CHK"
        # Account padding may be '*' or ' ' on either side.
        acct = record[2:12].strip("* ")
        if not acct or not _ascii_alnum(acct):
            return "R FMT"
        amount = record[12:23]
        if not _ascii_digits(amount):
            return "R FMT"
        date = record[23:31]
        if date != NULL_DATE and not _valid_date(date):
            return "R FMT"
        # Memo padding may be '.' or ','; the flag byte is not validated.
        memo = record[31:46].rstrip(".,")
        if not _printable(memo):
            return "R FMT"
        return f"P {acct} {int(amount)} {date} {memo or '_'}"


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        # The engine ends a line at the first CR, LF or NUL byte.
        line = re.split("[\r\n\0]", raw, maxsplit=1)[0]
        if not line:
            continue
        replies.append(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    # The engine works on raw bytes: latin-1 maps each byte to one character.
    data = sys.stdin.buffer.read().decode("latin-1")
    replies = process(data.split("\n"))
    sys.stdout.buffer.write("".join(r + "\n" for r in replies).encode("latin-1"))


if __name__ == "__main__":
    main()
