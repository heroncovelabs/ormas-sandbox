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
UNCAPPED_TIERS = (9,)

# Weekend surcharge for MCCs 5960-5969, rounded separately (half up).
SURCHARGE_BP = 25
SURCHARGE_MCC = range(5960, 5970)

# EUR large-value levy on amounts strictly above the threshold, rounded
# separately (half up).
EUR_LEVY_BP = 10
EUR_LEVY_THRESHOLD = 5_000_000

_WEIGHTS = (1, 3, 7)
_B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

ERROR_CODES = (
    "ERRLEN", "ERRCHK", "ERRTYPE", "ERRACCT", "ERRAMT",
    "ERRDATE", "ERRCUR", "ERRTIER", "ERRMCC",
)


_DIGITS = frozenset("0123456789")
_ALNUM = _DIGITS | frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")


def _ascii(text: str, allowed: frozenset) -> bool:
    """C-locale ctype test: every character is in ``allowed``."""
    return all(c in allowed for c in text)


def check_char(data: str, upto: int) -> str:
    total = sum(ord(c) * _WEIGHTS[i % 3] for i, c in enumerate(data[:upto]))
    return _B36[total % 36]


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round to the nearest unit (halves up), per the spec's fee rule."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder >= denominator:
        return quotient + 1
    return quotient


def _round_half_even(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient % 2):
        return quotient + 1
    return quotient


def _round_floor(numerator: int, denominator: int) -> int:
    return numerator // denominator


def _days_in_month(year: int, month: int) -> int:
    days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    # The engine uses the plain four-year rule (1900 and 2100 are leap).
    if month == 2 and year % 4 == 0:
        return 29
    return days[month - 1]


def _is_weekend(year: int, month: int, day: int) -> bool:
    # Zeller's congruence on the Gregorian calendar (also defined for the
    # Feb 29 dates the four-year leap rule admits); 0 = Saturday, 1 = Sunday.
    if month < 3:
        month += 12
        year -= 1
    k, j = year % 100, year // 100
    h = (day + 13 * (month + 1) // 5 + k + k // 4 + j // 4 + 5 * j) % 7
    return h in (0, 1)


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
        if not stripped or not _ascii(stripped, _ALNUM):
            self.error = "ERRACCT"
            return
        sign, digits = raw[12], raw[13:24]
        # Leading space padding is accepted in place of zeros.
        digits = digits.lstrip(" ")
        if sign not in "+-" or not digits or not _ascii(digits, _DIGITS):
            self.error = "ERRAMT"
            return
        self.negative = sign == "-"
        # Negative amounts are accepted on refunds only (as the magnitude).
        if self.negative and self.type != "RF":
            self.error = "ERRAMT"
            return
        self.amount = int(digits)
        date = raw[24:32]
        if not _ascii(date, _DIGITS):
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
        if tier[0] != "T" or not _ascii(tier[1:], _DIGITS) or not 1 <= int(tier[1:]) <= 9:
            self.error = "ERRTIER"
            return
        self.tier = int(tier[1:])
        mcc = raw[39:43]
        if not _ascii(mcc, _DIGITS):
            self.error = "ERRMCC"
            return
        self.mcc = int(mcc)

    def compute(self) -> None:
        if self.currency == "JPY":
            base_round = _round_nearest
        elif self.type == "RF":
            base_round = _round_floor
        else:
            base_round = _round_half_even
        fee = base_round(self.amount * RATE_BP[self.tier], 10_000)
        if self.mcc in SURCHARGE_MCC and _is_weekend(self.year, self.month, self.day):
            fee += _round_nearest(self.amount * SURCHARGE_BP, 10_000)
        if self.currency == "EUR" and self.amount > EUR_LEVY_THRESHOLD:
            fee += _round_nearest(self.amount * EUR_LEVY_BP, 10_000)
        if self.tier not in UNCAPPED_TIERS:
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
        if len(line) < OUTLEN - 1:
            # A one-byte record leaves the engine's buffer short: the check
            # byte and newline land past its terminator and are never
            # written, so this line runs into the next one.
            return line
        return line + check_char(line, OUTLEN - 1)


def process(lines: list[str]) -> list[str]:
    records = []
    for raw in lines:
        # The engine cuts each line at its first CR or LF.
        raw = raw.split("\n", 1)[0].split("\r", 1)[0]
        if not raw:
            continue
        record = Record(raw)
        record.parse()
        if record.error is None:
            record.compute()
        records.append(record)

    # The engine emits accepted records first, then rejected ones, each
    # group in input order.
    ordered = [r for r in records if r.error is None] + [r for r in records if r.error]
    out = [record.emit() for record in ordered]
    accepted = sum(1 for r in records if r.error is None)
    rejected = len(records) - accepted
    fee_sum = sum(r.fee for r in records if r.error is None)
    trailer = f"TR{accepted:06d}{rejected:06d}+{fee_sum:011d}" + " " * 20
    out.append(trailer + check_char(trailer, OUTLEN - 1))
    return out


def main() -> None:
    # Records are raw bytes; latin-1 maps each byte to one character.
    lines = sys.stdin.buffer.read().decode("latin-1").split("\n")
    for line in process(lines):
        sys.stdout.buffer.write(
            (line + ("\n" if len(line) == OUTLEN else "")).encode("latin-1")
        )


if __name__ == "__main__":
    main()
