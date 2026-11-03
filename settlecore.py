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
# Tiers the engine never caps.
CAP_EXEMPT_TIERS = (9,)

# Weekend surcharge for this MCC range (inclusive), in basis points.
SURCHARGE_MCC = (5960, 5969)
SURCHARGE_BP = 25

# EUR cross-border levy on amounts strictly above the threshold.
EUR_LEVY_THRESHOLD = 5_000_000
EUR_LEVY_BP = 10

_WEIGHTS = (1, 3, 7)
_B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

ERROR_CODES = (
    "ERRLEN", "ERRCHK", "ERRTYPE", "ERRACCT", "ERRAMT",
    "ERRDATE", "ERRCUR", "ERRTIER", "ERRMCC",
)


# The engine reads with fgets() into a 512-byte buffer, so longer lines are
# split into several records.
_LINEBUF = 512

_DIGITS = frozenset("0123456789")
_ALNUM = _DIGITS | frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")


def _isdigits(s: str) -> bool:
    """C-locale isdigit() over a non-empty string."""
    return bool(s) and all(c in _DIGITS for c in s)


def _isalnums(s: str) -> bool:
    """C-locale isalnum() over a non-empty string."""
    return bool(s) and all(c in _ALNUM for c in s)


def check_char(data: str, upto: int) -> str:
    # Text is latin-1 decoded, so ord() is the unsigned byte value.
    total = sum(ord(c) * _WEIGHTS[i % 3] for i, c in enumerate(data[:upto]))
    return _B36[total % 36]


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round to the nearest unit, halves up."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder >= denominator:
        return quotient + 1
    return quotient


def _round_half_even(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient % 2):
        return quotient + 1
    return quotient


def _round_fee(numerator: int, denominator: int, rtype: str, currency: str) -> int:
    """Engine rounding regimes: JPY halves up; otherwise refunds truncate
    and settlements round half to even."""
    if currency == "JPY":
        return _round_nearest(numerator, denominator)
    if rtype == "RF":
        return numerator // denominator
    return _round_half_even(numerator, denominator)


def _days_in_month(year: int, month: int) -> int:
    days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    # The engine applies the plain every-4-years leap rule.
    if month == 2 and year % 4 == 0:
        return 29
    return days[month - 1]


def _is_weekend(year: int, month: int, day: int) -> bool:
    # Sakamoto's Gregorian day-of-week (0 = Sunday), applied arithmetically,
    # so a Julian-only Feb 29 falls on the weekday of Mar 1.
    offsets = (0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4)
    if month < 3:
        year -= 1
    dow = (year + year // 4 - year // 100 + year // 400 + offsets[month - 1] + day) % 7
    return dow in (0, 6)


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
        if not _isalnums(stripped):
            self.error = "ERRACCT"
            return
        # The engine tolerates leading spaces in place of zero padding.
        sign, digits = raw[12], raw[13:24].lstrip(" ")
        if sign not in "+-" or not _isdigits(digits):
            self.error = "ERRAMT"
            return
        self.negative = sign == "-"
        # Negative amounts are accepted on refunds only.
        if self.negative and self.type != "RF":
            self.error = "ERRAMT"
            return
        self.amount = int(digits)
        date = raw[24:32]
        if not _isdigits(date):
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
        if tier[0] != "T" or not _isdigits(tier[1:]) or not 1 <= int(tier[1:]) <= 9:
            self.error = "ERRTIER"
            return
        self.tier = int(tier[1:])
        mcc = raw[39:43]
        if not _isdigits(mcc):
            self.error = "ERRMCC"
            return
        self.mcc = int(mcc)

    def compute(self) -> None:
        # Surcharge and levy are separately rounded components added to the
        # base fee; only the base follows the type/currency rounding regime.
        fee = _round_fee(
            self.amount * RATE_BP[self.tier], 10_000, self.type, self.currency
        )
        if SURCHARGE_MCC[0] <= self.mcc <= SURCHARGE_MCC[1] and _is_weekend(
            self.year, self.month, self.day
        ):
            fee += _round_nearest(self.amount * SURCHARGE_BP, 10_000)
        if self.currency == "EUR" and self.amount > EUR_LEVY_THRESHOLD:
            fee += _round_nearest(self.amount * EUR_LEVY_BP, 10_000)
        if self.tier not in CAP_EXEMPT_TIERS:
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
            f"{self.type}{self.account:<10.10}"
            f"+{fee:011d}{net_sign}{abs(net):011d}"
            f"{self.currency:<3.3}{status:<7.7}"
        )
        if len(self.type) < 2:
            # A one-byte record leaves a NUL in the engine's output buffer,
            # so the line is cut there: no check character, no newline.
            return line
        return line + check_char(line, OUTLEN - 1)


def _c_line(raw: str) -> str:
    """The record as the engine sees it: cut at the first CR, LF or NUL."""
    for stop in ("\r", "\n", "\0"):
        cut = raw.find(stop)
        if cut != -1:
            raw = raw[:cut]
    return raw


def read_lines(data: bytes) -> list[str]:
    """Split input the way fgets() with the engine's buffer does."""
    lines = []
    pos = 0
    while pos < len(data):
        end = data.find(b"\n", pos, pos + _LINEBUF - 1)
        end = pos + _LINEBUF - 1 if end == -1 else end + 1
        lines.append(data[pos:end].decode("latin-1"))
        pos = end
    return lines


def process(lines: list[str]) -> list[str]:
    records = []
    for raw in lines:
        raw = _c_line(raw)
        if not raw:
            continue
        record = Record(raw)
        record.parse()
        if record.error is None:
            record.compute()
        records.append(record)

    # The engine emits accepted records first, then rejected ones, each
    # group in input order.
    ordered = [r for r in records if r.error is None]
    ordered += [r for r in records if r.error is not None]
    out = [record.emit() for record in ordered]
    accepted = sum(1 for r in records if r.error is None)
    rejected = len(records) - accepted
    fee_sum = sum(r.fee for r in records if r.error is None)
    # Padded to a fixed width, so a wide fee sum consumes the spaces.
    trailer = f"TR{accepted:06d}{rejected:06d}+{fee_sum:011d}".ljust(OUTLEN - 1)
    out.append(trailer + check_char(trailer, OUTLEN - 1))
    return out


def main() -> None:
    out = sys.stdout.buffer
    for line in process(read_lines(sys.stdin.buffer.read())):
        # Lines cut short by the engine carry no newline either.
        out.write(line.encode("latin-1") + (b"\n" if len(line) >= OUTLEN else b""))
    out.flush()


if __name__ == "__main__":
    main()
