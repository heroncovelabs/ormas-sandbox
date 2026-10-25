"""MeterCore batch billing engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads meter
readings on stdin, writes per-account B lines and an X trailer on stdout.
Format reference: ``docs/SPEC.md``. Where the spec and the legacy engine
disagree, the engine's behavior is the contract; the rules below follow the
engine as observed.
"""

from __future__ import annotations

import re
import sys

TIER1_LIMIT = 500
TIER2_LIMIT = 2000
# rate in tenths of a cent per kwh
RATE_TENTHS = (140, 190, 260)
BAND_PCT = {"D": 100, "N": 70, "W": 85}
# The engine bills night energy at a lower rate in winter months.
WINTER_MONTHS = (12, 1, 2)
WINTER_NIGHT_PCT = 60
SUMMER_MONTHS = (6, 7, 8, 9)
# Summer surcharge applies to all energy above the first tier limit.
SUMMER_PCT = 110
# Legacy meter type carries a 3% uplift; standard meters bill at face rate.
LEGACY_METER_PCT = 103
# Bill arithmetic: rate tenths * band% * season% * meter% -> cents.
BILL_DIVISOR = 10 * 100 * 100 * 100

ERROR_CODES = ("FMT", "MONTH", "KWH", "BAND", "METER")

# The engine splits fields on space, tab and carriage return only.
_SEPARATORS = re.compile(r"[ \t\r\n]+")


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round to the nearest whole unit, ties to even."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator:
        return quotient + 1
    if 2 * remainder == denominator and quotient % 2 == 1:
        return quotient + 1
    return quotient


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
    band_pct = BAND_PCT[band]
    meter_pct = LEGACY_METER_PCT if meter == "L" else 100
    summer = month in SUMMER_MONTHS
    winter_night = band == "N" and month in WINTER_MONTHS
    numerator = 0
    for tier, slice_kwh in enumerate(_slices(prev, kwh)):
        if slice_kwh == 0:
            continue
        # The winter night discount applies to tier-1 energy only.
        tier_band_pct = WINTER_NIGHT_PCT if winter_night and tier == 0 else band_pct
        season = SUMMER_PCT if summer and tier >= 1 else 100
        numerator += slice_kwh * RATE_TENTHS[tier] * tier_band_pct * season * meter_pct
    return _round_nearest(numerator, BILL_DIVISOR)


def _is_ascii_alnum(text: str) -> bool:
    return text.isascii() and text.isalnum()


def _is_ascii_digits(text: str) -> bool:
    return text.isascii() and text.isdigit()


def _parse(tokens: list[str]) -> tuple[str | None, int, int, str, str]:
    """Validate one reading. Returns (error, month, kwh, band, meter)."""
    if len(tokens) < 6 or tokens[0] != "M":
        return "FMT", 0, 0, "", ""
    if not (1 <= len(tokens[1]) <= 8 and _is_ascii_alnum(tokens[1])):
        return "FMT", 0, 0, "", ""
    if len(tokens[2]) != 2 or not _is_ascii_digits(tokens[2]):
        return "MONTH", 0, 0, "", ""
    month = int(tokens[2])
    if month == 0 or month > 13:
        return "MONTH", 0, 0, "", ""
    if month == 13:
        month = 1
    if not (1 <= len(tokens[3]) <= 6 and _is_ascii_digits(tokens[3])):
        return "KWH", 0, 0, "", ""
    kwh = int(tokens[3])
    if tokens[4] not in BAND_PCT:
        return "BAND", 0, 0, "", ""
    if tokens[5] not in ("S", "L"):
        return "METER", 0, 0, "", ""
    return None, month, kwh, tokens[4], tokens[5]


def process(lines: list[str]) -> list[str]:
    out: list[str] = []
    accounts: dict[str, Account] = {}
    rejected = 0

    for raw in lines:
        tokens = [t for t in _SEPARATORS.split(raw) if t]
        if not tokens:
            continue
        echo = tokens[1] if len(tokens) >= 2 else "?"
        error, month, kwh, band, meter = _parse(tokens)

        if error is not None:
            out.append(f"R {echo} {error}")
            rejected += 1
            continue
        if kwh == 0:
            # A zero-kwh reading is a valid no-op: it bills nothing and does
            # not register the account.
            continue

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
