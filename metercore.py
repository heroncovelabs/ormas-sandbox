"""MeterCore batch billing engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads meter
readings on stdin, writes per-account B lines and an X trailer on stdout.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).

Behavior follows the legacy engine wherever it differs from the spec:

- Each reading is fully validated before its kwh are considered; a zero-kwh
  reading that passes validation is skipped and creates no account.
- Accounts are keyed case-insensitively; the first-seen spelling is shown.
- Month ``13`` is accepted and bills as January.
- Winter (12, 01, 02) tier-1 night energy is discounted to 60%.
- The summer surcharge applies to tier 2 and tier 3 energy.
- Meter ``L`` carries a 3% uplift.
- Each reading's cost is rounded to the nearest cent, ties to even.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
import re
import sys

TIER1_LIMIT = 500
TIER2_LIMIT = 2000
# rate in tenths of a cent per kwh
RATE_TENTHS = (140, 190, 260)
BAND_PCT = {"D": 100, "N": 70, "W": 85}
WINTER_NIGHT_PCT = 60
WINTER_MONTHS = (12, 1, 2)
SUMMER_MONTHS = (6, 7, 8, 9)
SUMMER_PCT = 110
LEGACY_METER_PCT = 103

# Month values 1..13 are accepted; 13 is billed as January.
MONTH_MAX = 13
ACCOUNT_MAX_LEN = 8
KWH_MAX_DIGITS = 6
ACCOUNT_LIMIT = 8192
_INPUT_RECORD_BYTES = 1023
_TOKEN = re.compile(r"[^ \t\r\n]+")

# Denominator for units scaled by rate (tenths of a cent), band, season and
# meter percentages, yielding whole cents.
_UNIT_DIVISOR = 10 * 100 * 100 * 100

ERROR_CODES = ("FMT", "MONTH", "KWH", "BAND", "METER")

_ASCII_DIGITS = frozenset("0123456789")
_ASCII_ALNUM = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round to the nearest integer, ties to even (matches the legacy engine)."""
    quotient, remainder = divmod(numerator, denominator)
    twice = 2 * remainder
    if twice > denominator or (twice == denominator and quotient % 2 == 1):
        return quotient + 1
    return quotient


class Account:
    def __init__(self, shown: str):
        self.shown = shown
        self.counter = 0    # cumulative kwh within the batch (tier position)
        self.total_kwh = 0
        self.bill = 0


def _slices(prev: int, kwh: int) -> tuple[int, int, int]:
    s1 = max(0, min(TIER1_LIMIT - prev, kwh))
    s2 = max(0, min(TIER2_LIMIT - max(prev, TIER1_LIMIT), kwh - s1))
    return s1, s2, kwh - s1 - s2


def _billing_month(month: int) -> int:
    """Map accepted month values onto calendar months (13 -> January)."""
    return month - 12 if month > 12 else month


def _band_pct(band: str, month: int, tier: int) -> int:
    """Band multiplier for one tier. Winter night discount covers tier 1 only."""
    if band == "N" and tier == 0 and _billing_month(month) in WINTER_MONTHS:
        return WINTER_NIGHT_PCT
    return BAND_PCT[band]


def _reading_fee(prev: int, kwh: int, month: int, band: str, meter: str) -> int:
    billing_month = _billing_month(month)
    summer = billing_month in SUMMER_MONTHS
    meter_pct = LEGACY_METER_PCT if meter == "L" else 100
    units = 0
    for tier, slice_kwh in enumerate(_slices(prev, kwh)):
        if slice_kwh == 0:
            continue
        band_pct = _band_pct(band, month, tier)
        # The summer surcharge applies to tier 2 and tier 3 energy.
        season = SUMMER_PCT if summer and tier >= 1 else 100
        units += slice_kwh * RATE_TENTHS[tier] * band_pct * season * meter_pct
    return _round_nearest(units, _UNIT_DIVISOR)


def _is_ascii_digits(text: str, min_len: int, max_len: int) -> bool:
    return min_len <= len(text) <= max_len and all(c in _ASCII_DIGITS for c in text)


def _is_account_id(text: str) -> bool:
    return 1 <= len(text) <= ACCOUNT_MAX_LEN and all(c in _ASCII_ALNUM for c in text)


def _parse_reading(tokens: list[str]) -> tuple[str | None, int, int, str, str]:
    """Validate one reading. Returns (error, month, kwh, band, meter)."""
    if len(tokens) < 6 or tokens[0] != "M":
        return "FMT", 0, 0, "", ""
    if not _is_account_id(tokens[1]):
        return "FMT", 0, 0, "", ""
    if not _is_ascii_digits(tokens[2], 2, 2):
        return "MONTH", 0, 0, "", ""
    month = int(tokens[2])
    if not 1 <= month <= MONTH_MAX:
        return "MONTH", 0, 0, "", ""
    if not _is_ascii_digits(tokens[3], 1, KWH_MAX_DIGITS):
        return "KWH", month, 0, "", ""
    kwh = int(tokens[3])
    if tokens[4] not in BAND_PCT:
        return "BAND", month, kwh, "", ""
    band = tokens[4]
    if tokens[5] not in ("S", "L"):
        return "METER", month, kwh, band, ""
    return None, month, kwh, band, tokens[5]


class _TooManyAccounts(Exception):
    pass


def _records(lines: Iterable[str | bytes]) -> Iterator[str]:
    """Reproduce fgets' byte limit and C-string termination before tokenizing."""
    for raw in lines:
        data = raw.encode("utf-8", "surrogateescape") if isinstance(raw, str) else raw
        start = 0
        while start < len(data):
            end = min(start + _INPUT_RECORD_BYTES, len(data))
            newline = data.find(b"\n", start, end)
            if newline >= 0:
                end = newline + 1
            record = data[start:end].split(b"\0", 1)[0]
            yield record.decode("utf-8", "surrogateescape")
            start = end


def _process(lines: Iterable[str | bytes]) -> Iterator[str]:
    accounts: dict[str, Account] = {}
    rejected = 0

    for raw in _records(lines):
        tokens = _TOKEN.findall(raw)
        if not tokens:
            continue
        echo = tokens[1] if len(tokens) >= 2 else "?"

        error, month, kwh, band, meter = _parse_reading(tokens)
        if error is not None:
            yield f"R {echo} {error}"
            rejected += 1
            continue

        if kwh == 0:
            # Valid zero-kwh readings are no-ops: no account, no state change.
            continue

        key = tokens[1].lower()
        account = accounts.get(key)
        if account is None:
            if len(accounts) == ACCOUNT_LIMIT:
                raise _TooManyAccounts("too many accounts")
            account = accounts[key] = Account(tokens[1])
        fee = _reading_fee(account.counter, kwh, month, band, meter)
        account.counter += kwh
        account.total_kwh += kwh
        account.bill += fee

    grand = 0
    for account in accounts.values():
        yield f"B {account.shown} {account.total_kwh} {account.bill}"
        grand += account.bill
    yield f"X {len(accounts)} {rejected} {grand}"


def process(lines: Iterable[str | bytes]) -> list[str]:
    return list(_process(lines))


def main() -> None:
    # Binary input preserves CRs, invalid UTF-8, and byte-sized record boundaries.
    records = iter(lambda: sys.stdin.buffer.readline(_INPUT_RECORD_BYTES), b"")
    try:
        for line in _process(records):
            sys.stdout.buffer.write((line + "\n").encode("utf-8", "surrogateescape"))
    except _TooManyAccounts as error:
        print(error, file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
