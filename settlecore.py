"""SettleCore batch settlement engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
80-column settlement records on stdin, writes 47-column response lines and
a batch trailer on stdout. Format reference: ``docs/SPEC.md`` (note the
drift warning at the top of that file; the legacy engine's behavior is the
contract).
"""

from __future__ import annotations

import sys

RECLEN = 80
OUTLEN = 47

RATE_BP = {
    1: 25, 2: 50, 3: 75, 4: 100, 5: 150, 6: 200, 7: 245, 8: 300, 9: 350,
}
FEE_CAP = 250_000

_WEIGHTS = (1, 3, 7)
_B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

ERROR_CODES = (
    "ERRLEN", "ERRCHK", "ERRTYPE", "ERRACCT", "ERRAMT",
    "ERRDATE", "ERRCUR", "ERRTIER", "ERRMCC",
)


def check_char(data: str, upto: int) -> str:
    total = sum(ord(c) * _WEIGHTS[i % 3] for i, c in enumerate(data[:upto]))
    return _B36[total % 36]


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round to the nearest unit, with ties rounded up."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder >= denominator:
        return quotient + 1
    return quotient


def _days_in_month(year: int, month: int) -> int:
    days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    # Validation follows the engine's four-year leap cycle.
    if month == 2 and year % 4 == 0:
        return 29
    return days[month - 1]


def _digits(value: str) -> bool:
    return bool(value) and all("0" <= c <= "9" for c in value)


def _weekday(year: int, month: int, day: int) -> int:
    """Gregorian weekday, Sunday = 0, including accepted century leap days."""
    offsets = (0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4)
    year -= month < 3
    return (year + year // 4 - year // 100 + year // 400
            + offsets[month - 1] + day) % 7


class Record:
    def __init__(self, raw: str):
        self.raw = raw
        self.type = raw[0:2]
        self.account = raw[2:12] if len(raw) >= 12 else " " * 10
        self.currency = raw[32:35] if len(raw) >= 35 else "   "
        self.error: str | None = None
        self.amount = 0
        self.negative = False
        self.year = self.month = self.day = 0
        self.tier = 0
        self.mcc = 0
        self.fee = 0
        self.net = 0

    def parse(self) -> None:
        raw = self.raw
        if len(raw) != RECLEN:
            self.error = "ERRLEN"
            self.account = " " * 10
            self.currency = "   "
            return
        if check_char(raw, 78) != raw[79]:
            self.error = "ERRCHK"
            return
        if self.type not in ("ST", "RF"):
            self.error = "ERRTYPE"
            return
        stripped = self.account.replace(" ", "")
        if not stripped or not all(
            "0" <= c <= "9" or "A" <= c <= "Z" or "a" <= c <= "z"
            for c in stripped
        ):
            self.error = "ERRACCT"
            return
        sign, digits = raw[12], raw[13:24].lstrip(" ")
        if sign not in "+-" or not _digits(digits):
            self.error = "ERRAMT"
            return
        self.negative = sign == "-"
        if self.negative and self.type == "ST":
            self.error = "ERRAMT"
            return
        self.amount = int(digits)
        date = raw[24:32]
        if not _digits(date):
            self.error = "ERRDATE"
            return
        self.year, self.month, self.day = int(date[:4]), int(date[4:6]), int(date[6:8])
        if (
            self.year < 1900
            or not 1 <= self.month <= 12
            or not 1 <= self.day <= _days_in_month(self.year, self.month)
        ):
            self.error = "ERRDATE"
            return
        if self.currency not in ("USD", "EUR", "GBP", "JPY"):
            self.error = "ERRCUR"
            return
        tier = raw[35:39]
        if tier[0] != "T" or not _digits(tier[1:]) or not 1 <= int(tier[1:]) <= 9:
            self.error = "ERRTIER"
            return
        self.tier = int(tier[1:])
        mcc = raw[39:43]
        if not _digits(mcc):
            self.error = "ERRMCC"
            return
        self.mcc = int(mcc)

    def compute(self) -> None:
        numerator = self.amount * RATE_BP[self.tier]
        if self.currency == "JPY":
            fee = _round_nearest(numerator, 10_000)
        elif self.type == "RF":
            fee = numerator // 10_000
        else:
            fee, remainder = divmod(numerator, 10_000)
            # Settlements use nearest-even rounding for the base fee.
            if remainder > 5_000 or (remainder == 5_000 and fee % 2):
                fee += 1
        # These components each have their own half-up rounding step.
        if 5960 <= self.mcc <= 5969 and _weekday(self.year, self.month, self.day) in (0, 6):
            fee += _round_nearest(self.amount * 25, 10_000)
        if self.currency == "EUR" and self.amount > 5_000_000:
            fee += _round_nearest(self.amount * 10, 10_000)
        if self.tier != 9:
            fee = min(fee, FEE_CAP)
        self.fee = fee
        if self.type == "RF":
            self.net = -(self.amount - fee)
        else:
            self.net = self.amount - fee

    def emit(self) -> str:
        fee = 0 if self.error else self.fee
        net = 0 if self.error else self.net
        net_sign = "-" if net < 0 else "+"
        status = self.error or "OK"
        line = (
            f"{self.type:.2}{self.account:<10.10}"
            f"+{fee:011d}{net_sign}{abs(net):011d}"
            f"{self.currency:<3.3}{status:<7.7}"
        )
        # A one-byte type leaves an early string terminator in the engine's
        # response buffer, before the check character and newline positions.
        if len(line) < OUTLEN - 1:
            return line
        line = line[:OUTLEN - 1]
        return line + check_char(line, OUTLEN - 1)


def process(lines: list[str]) -> list[str]:
    records = []
    for raw in lines:
        for terminator in ("\0", "\r", "\n"):
            raw = raw.split(terminator, 1)[0]
        if not raw:
            continue
        record = Record(raw)
        record.parse()
        if record.error is None:
            record.compute()
        records.append(record)

    # The engine emits two stable groups: successful records, then errors.
    records = [r for r in records if r.error is None] + [r for r in records if r.error is not None]
    out = [record.emit() for record in records]
    accepted = sum(1 for r in records if r.error is None)
    rejected = len(records) - accepted
    fee_sum = sum(r.fee for r in records if r.error is None)
    trailer = (f"TR{accepted:06d}{rejected:06d}+{fee_sum:011d}" + " " * 20)[:OUTLEN - 1]
    out.append(trailer + check_char(trailer, OUTLEN - 1))
    return out


def main() -> None:
    # Match fgets' 511-byte chunks and preserve byte-based field positions and
    # checksums, independently of the terminal's text encoding.
    lines = []
    while raw := sys.stdin.buffer.readline(511):
        lines.append(raw.decode("latin1"))
    for line in process(lines):
        suffix = "\n" if len(line) == OUTLEN else ""
        sys.stdout.buffer.write((line + suffix).encode("latin1"))


if __name__ == "__main__":
    main()
