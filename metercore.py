"""MeterCore batch billing engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads meter
readings on stdin, writes per-account B lines and an X trailer on stdout.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys
from typing import NamedTuple

MAX_MONTH = 13  # the engine accepts months 01..13 (13 bills as a non-summer month)
TIER1_LIMIT = 500
TIER2_LIMIT = 2000
# rate in tenths of a cent per kwh
RATE_TENTHS = (140, 190, 260)
BAND_PCT = {"D": 100, "N": 70, "W": 85}
# engine: night energy in tier 1 during winter months is billed at 60%.
WINTER_NIGHT_PCT = 60
WINTER_MONTHS = (12, 1, 2)
SUMMER_MONTHS = (6, 7, 8, 9)
# engine: the summer surcharge applies to tier 2 and tier 3 energy.
SUMMER_PCT = 110
# engine: legacy analog meters (L) are billed 3% above standard.
LEGACY_METER_PCT = 103
# numerator scale: rate tenths-of-cent * band% * season% * meter% -> cents
_BILL_DENOMINATOR = 10 * 100 * 100 * 100

ERROR_CODES = ("FMT", "MONTH", "KWH", "BAND", "METER")


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round to the nearest whole unit, ties to even (the engine's rounding)."""
    quotient, remainder = divmod(numerator, denominator)
    twice = 2 * remainder
    if twice > denominator or (twice == denominator and quotient % 2 == 1):
        return quotient + 1
    return quotient


class _Reading(NamedTuple):
    account: str
    month: int
    kwh: int
    band: str
    meter: str


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


def _band_pct(tier: int, month: int, band: str) -> int:
    if tier == 0 and band == "N" and month in WINTER_MONTHS:
        return WINTER_NIGHT_PCT
    return BAND_PCT[band]


def _reading_fee(prev: int, kwh: int, month: int, band: str, meter: str = "S") -> int:
    """Bill one reading from the account's pre-reading cumulative kwh.

    The whole reading is summed exactly and rounded once, to the cent.
    """
    numerator = 0
    meter_pct = LEGACY_METER_PCT if meter == "L" else 100
    for tier, slice_kwh in enumerate(_slices(prev, kwh)):
        if slice_kwh == 0:
            continue
        season = SUMMER_PCT if month in SUMMER_MONTHS and tier >= 1 else 100
        numerator += (
            slice_kwh * RATE_TENTHS[tier] * _band_pct(tier, month, band) * season * meter_pct
        )
    return _round_nearest(numerator, _BILL_DENOMINATOR)


def _tokenize(raw: str) -> list[str]:
    """Split a line the way the engine does.

    The engine treats a NUL byte as end of line, and separates fields only on
    ASCII space, tab, CR and LF (not on other Unicode or control whitespace).
    """
    line = raw.split("\x00", 1)[0]
    return [token for token in re.split(r"[ \t\r\n]+", line) if token]


def _is_ascii_digits(text: str) -> bool:
    return text.isascii() and text.isdigit()


def _normalize_month(month: int) -> int:
    """Map an accepted month onto the billing calendar.

    The engine bills month 13 exactly as month 01 (the wrap into the next
    year), so downstream billing sees 01 for it.
    """
    return 1 if month == MAX_MONTH else month


def _parse_reading(tokens: list[str]) -> _Reading | str:
    """Validate a tokenized record without touching any batch state.

    The engine requires at least six tokens and ignores any tokens after the
    sixth. Returns the parsed reading, or the rejection code for the first
    failing check in engine order: FMT, MONTH, KWH, BAND, METER.
    """
    if len(tokens) < 6 or tokens[0] != "M":
        return "FMT"
    account = tokens[1]
    if not (1 <= len(account) <= 8 and account.isascii() and account.isalnum()):
        return "FMT"
    if len(tokens[2]) != 2 or not _is_ascii_digits(tokens[2]):
        return "MONTH"
    month = int(tokens[2])
    if not 1 <= month <= MAX_MONTH:
        return "MONTH"
    # The kwh field is limited to six characters as written, so leading
    # zeros count toward the limit.
    if not (1 <= len(tokens[3]) <= 6 and _is_ascii_digits(tokens[3])):
        return "KWH"
    kwh = int(tokens[3])
    if tokens[4] not in ("D", "N", "W"):
        return "BAND"
    if tokens[5] not in ("S", "L"):
        return "METER"
    return _Reading(account, _normalize_month(month), kwh, tokens[4], tokens[5])


def _account_key(account: str) -> str:
    """Lookup key for an account: the engine matches accounts ASCII case-insensitively.

    Accounts are validated as ASCII alphanumerics before this is called, so
    ``upper`` only ever changes ASCII letters.
    """
    return account.upper()


def _apply_reading(accounts: dict[str, Account], reading: _Reading) -> None:
    """Accumulate an accepted reading into the batch state.

    A reading with zero kwh has already passed full validation (a bad token
    still rejects it). It is then skipped entirely: it creates no account, does
    not fix the account's displayed spelling, and does not move the account in
    encounter order.
    """
    if reading.kwh == 0:
        return
    key = _account_key(reading.account)
    account = accounts.get(key)
    if account is None:
        account = accounts[key] = Account(reading.account)
    fee = _reading_fee(
        account.counter, reading.kwh, reading.month, reading.band, reading.meter
    )
    account.counter += reading.kwh
    account.total_kwh += reading.kwh
    account.bill += fee


def process(lines: list[str]) -> list[str]:
    out: list[str] = []
    accounts: dict[str, Account] = {}
    rejected = 0

    for raw in lines:
        tokens = _tokenize(raw)
        if not tokens:
            continue
        parsed = _parse_reading(tokens)
        if isinstance(parsed, str):
            echo = tokens[1] if len(tokens) >= 2 else "?"
            out.append(f"R {echo} {parsed}")
            rejected += 1
            continue
        _apply_reading(accounts, parsed)

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
