"""MeterCore batch billing engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads meter
readings on stdin, writes per-account B lines and an X trailer on stdout.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys
from fractions import Fraction

TIER1_LIMIT = 500
TIER2_LIMIT = 2000
# rate in tenths of a cent per kwh
RATE_TENTHS = (140, 190, 260)
BAND_PCT = {"D": 100, "N": 70, "W": 85}
SUMMER_MONTHS = (6, 7, 8, 9)
SUMMER_PCT = 110
WINTER_MONTHS = (12, 1, 2)
# Night-band tier-1 energy in winter months is billed at this percentage.
WINTER_NIGHT_PCT = 60
# Meter uplift: legacy analog meters (L) are billed 3% higher.
METER_UPLIFT_PCT = {"S": 100, "L": 103}
HALF = Fraction(1, 2)

ERROR_CODES = ("FMT", "MONTH", "KWH", "BAND", "METER")


def _round_nearest(value: Fraction) -> int:
    """Round a non-negative exact amount to whole cents, ties to even."""
    floor = value.numerator // value.denominator
    remainder = value - floor
    if remainder > HALF:
        return floor + 1
    if remainder < HALF:
        return floor
    return floor if floor % 2 == 0 else floor + 1


class Account:
    def __init__(self, shown: str):
        self.shown = shown
        self.counter = 0    # cumulative kwh within the batch
        self.total_kwh = 0
        self.bill = 0


def _slices(prev: int, kwh: int) -> tuple[int, int, int]:
    s1 = max(0, min(TIER1_LIMIT - prev, kwh))
    s2 = max(0, min(TIER2_LIMIT - max(prev, TIER1_LIMIT), kwh - s1))
    return s1, s2, kwh - s1 - s2


def _reading_fee(prev: int, kwh: int, month: int, band: str, meter: str) -> int:
    """Bill one reading exactly, then round once to whole cents.

    Per tier slice: rate x band x season x meter uplift, all as exact
    rationals. The engine rounds the reading's total, not each slice.
    """
    total = Fraction(0)
    winter_night = month in WINTER_MONTHS and band == "N"
    summer = month in SUMMER_MONTHS
    for tier, slice_kwh in enumerate(_slices(prev, kwh)):
        if slice_kwh == 0:
            continue
        band_pct = BAND_PCT[band]
        if tier == 0 and winter_night:
            band_pct = WINTER_NIGHT_PCT
        # The summer surcharge applies to tier-2 and tier-3 energy.
        season = SUMMER_PCT if summer and tier >= 1 else 100
        units = slice_kwh * RATE_TENTHS[tier] * band_pct * season * METER_UPLIFT_PCT[meter]
        # RATE_TENTHS is tenths of a cent; the four percent factors are /100 each.
        total += Fraction(units, 10_000_000)
    return _round_nearest(total)


BANDS = ("D", "N", "W")
METERS = ("S", "L")
# The engine reads each record up to its first NUL and splits fields on
# space, tab, and CR only; other Unicode whitespace is ordinary token text.
_FIELD_SEPARATOR = re.compile(r"[ \t\r\n]+")


def _tokenize(raw: str) -> list[str]:
    line = raw.split("\x00", 1)[0]
    return [token for token in _FIELD_SEPARATOR.split(line) if token]


def _is_ascii_digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


def _month_in_range(number: int) -> int | None:
    """Map a numeric month to 1..12; month 13 wraps to January."""
    if 1 <= number <= 12:
        return number
    if number == 13:
        return 1
    return None


def _parse_reading(tokens: list[str]) -> tuple[str | None, int, int, str, str]:
    """Validate one tokenized record.

    Returns ``(error_code, month, kwh, band, meter)``; ``error_code`` is None
    when the reading is accepted. Checks run in the engine's order: FMT, MONTH,
    KWH, BAND, METER. Extra tokens after the sixth are ignored.
    """
    if len(tokens) < 6 or tokens[0] != "M":
        return "FMT", 0, 0, "", ""
    account = tokens[1]
    if not (1 <= len(account) <= 8 and account.isascii() and account.isalnum()):
        return "FMT", 0, 0, "", ""

    month_token = tokens[2]
    if len(month_token) != 2 or not _is_ascii_digits(month_token):
        return "MONTH", 0, 0, "", ""
    month = _month_in_range(int(month_token))
    if month is None:
        return "MONTH", 0, 0, "", ""

    kwh_token = tokens[3]
    if not (1 <= len(kwh_token) <= 6 and _is_ascii_digits(kwh_token)):
        return "KWH", 0, 0, "", ""
    kwh = int(kwh_token)

    band = tokens[4]
    if band not in BANDS:
        return "BAND", 0, 0, "", ""
    if tokens[5] not in METERS:
        return "METER", 0, 0, "", ""
    return None, month, kwh, band, tokens[5]


def process(lines: list[str]) -> list[str]:
    out: list[str] = []
    accounts: dict[str, Account] = {}
    rejected = 0

    for raw in lines:
        tokens = _tokenize(raw)
        if not tokens:
            continue
        echo = tokens[1] if len(tokens) >= 2 else "?"
        error, month, kwh, band, meter = _parse_reading(tokens)

        if error is not None:
            out.append(f"R {echo} {error}")
            rejected += 1
            continue
        if kwh == 0:
            # A zero-kwh reading is valid but a no-op: it neither bills nor
            # registers the account.
            continue

        # Accounts are ASCII alphanumeric (validated above), so lower() is an
        # ASCII-only fold. Case variants share one account; the first accepted
        # spelling is the one printed.
        key = tokens[1].lower()
        account = accounts.get(key)
        if account is None:
            account = accounts[key] = Account(tokens[1])
        fee = _reading_fee(account.counter, kwh, month, band, meter)
        account.counter += kwh
        account.total_kwh += kwh
        account.bill += fee

    grand = 0
    for account in accounts.values():
        out.append(f"B {account.shown} {account.total_kwh} {account.bill}")
        grand += account.bill
    out.append(f"X {len(accounts)} {rejected} {grand}")
    return out


def main() -> None:
    for line in process(sys.stdin.readlines()):
        print(line)


if __name__ == "__main__":
    main()
