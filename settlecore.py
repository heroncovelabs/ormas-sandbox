"""SettleCore batch settlement engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
80-column settlement records on stdin, writes 47-column response lines and
a batch trailer on stdout. Format reference: ``docs/SPEC.md`` (note the
drift warning at the top of that file; the legacy engine's behavior is the
contract).
"""

from __future__ import annotations

import datetime
import sys

RECLEN = 80
OUTLEN = 47

RATE_BP = {
    1: 25, 2: 50, 3: 75, 4: 100, 5: 150, 6: 200, 7: 245, 8: 300, 9: 350,
}
FEE_CAP = 250_000
WEEKEND_SURCHARGE_BP = 25
EUR_LEVY_BP = 10
EUR_LEVY_THRESHOLD = 5_000_000

_WEIGHTS = (1, 3, 7)
_B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

ERROR_CODES = (
    "ERRLEN", "ERRCHK", "ERRTYPE", "ERRACCT", "ERRAMT",
    "ERRDATE", "ERRCUR", "ERRTIER", "ERRMCC",
)


def check_char(data: str, upto: int) -> str:
    total = sum(ord(c) * _WEIGHTS[i % 3] for i, c in enumerate(data[:upto]))
    return _B36[total % 36]


def _round_half_up(numerator: int, denominator: int = 10_000) -> int:
    quotient, remainder = divmod(numerator, denominator)
    return quotient + (2 * remainder >= denominator)


def _round_half_even(numerator: int, denominator: int = 10_000) -> int:
    quotient, remainder = divmod(numerator, denominator)
    twice = 2 * remainder
    return quotient + (twice > denominator or (twice == denominator and quotient % 2))


def _base_fee(amount: int, rate_bp: int, record_type: str, currency: str) -> int:
    numerator = amount * rate_bp
    if currency == "JPY":
        return _round_half_up(numerator)
    if record_type == "RF":
        return numerator // 10_000
    return _round_half_even(numerator)


def _days_in_month(year: int, month: int) -> int:
    days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if month == 2 and year % 4 == 0:
        return 29
    return days[month - 1]


def _weekday(year: int, month: int, day: int) -> int:
    """The legacy calendar has no century exception to its leap rule."""
    if month == 2 and day == 29 and year % 100 == 0 and year % 400 != 0:
        return datetime.date(year, 3, 1).weekday()
    return datetime.date(year, month, day).weekday()


class Record:
    def __init__(self, raw: str):
        self.raw = raw
        self.type = raw[0:2] if len(raw) >= 2 else "??"
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
        if not stripped or not stripped.isalnum():
            self.error = "ERRACCT"
            return
        sign, digits = raw[12], raw[13:24]
        if (
            sign not in "+-"
            or digits != digits.rstrip()
            or not digits.lstrip(" ").isdigit()
        ):
            self.error = "ERRAMT"
            return
        self.negative = sign == "-"
        if self.negative and self.type != "RF":
            self.error = "ERRAMT"
            return
        self.amount = int(digits)
        date = raw[24:32]
        if not date.isdigit():
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
        if tier[0] != "T" or not tier[1:].isdigit() or not 1 <= int(tier[1:]) <= 9:
            self.error = "ERRTIER"
            return
        self.tier = int(tier[1:])
        mcc = raw[39:43]
        if not mcc.isdigit():
            self.error = "ERRMCC"
            return
        self.mcc = int(mcc)

    def compute(self) -> None:
        fee = _base_fee(self.amount, RATE_BP[self.tier], self.type, self.currency)
        weekend = _weekday(self.year, self.month, self.day) >= 5
        if weekend and 5960 <= self.mcc <= 5969:
            fee += _round_half_up(self.amount * WEEKEND_SURCHARGE_BP)
        if self.currency == "EUR" and self.amount > EUR_LEVY_THRESHOLD:
            fee += _round_half_up(self.amount * EUR_LEVY_BP)
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
            f"{self.type:<2.2}{self.account:<10.10}"
            f"+{fee:011d}{net_sign}{abs(net):011d}"
            f"{self.currency:<3.3}{status:<7.7}"
        )
        return line + check_char(line, OUTLEN - 1)


def process(lines: list[str]) -> list[str]:
    records = []
    for raw in lines:
        raw = raw.rstrip("\r\n")
        if not raw:
            continue
        record = Record(raw)
        record.parse()
        if record.error is None:
            record.compute()
        records.append(record)

    accepted_records = [r for r in records if r.error is None]
    rejected_records = [r for r in records if r.error is not None]
    out = [record.emit() for record in accepted_records + rejected_records]
    accepted = len(accepted_records)
    rejected = len(rejected_records)
    fee_sum = sum(r.fee for r in accepted_records)
    trailer = f"TR{accepted:06d}{rejected:06d}+{fee_sum:011d}" + " " * 20
    out.append(trailer + check_char(trailer, OUTLEN - 1))
    return out


def main() -> None:
    for line in process(sys.stdin.readlines()):
        print(line)


if __name__ == "__main__":
    main()
