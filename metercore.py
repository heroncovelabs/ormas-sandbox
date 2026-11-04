"""MeterCore batch billing engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads meter
readings on stdin, writes per-account B lines and an X trailer on stdout.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).
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
SUMMER_MONTHS = (6, 7, 8, 9)
SUMMER_PCT = 110
# Month 13 is normalized to January while parsing.
WINTER_MONTHS = (12, 1, 2)
WINTER_NIGHT_TIER1_PCT = 60

ERROR_CODES = ("FMT", "MONTH", "KWH", "BAND", "METER")
_RECORD_BYTES = 1023  # payload of the engine's 1024-byte fgets buffer
_MAX_ACCOUNTS = 8192

# The engine splits fields on these four ASCII whitespace characters;
# other control characters and Unicode whitespace stay inside a token.
_FIELD_SPLIT = re.compile(r"[ \t\r\n]+")
_DIGITS = frozenset("0123456789")
_ACCOUNT_CHARS = frozenset("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round exact integer units to the nearest cent, with ties to even."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient % 2):
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


def _reading_fee(prev: int, kwh: int, month: int, band: str, meter: str = "S") -> int:
    units = 0
    meter_pct = 103 if meter == "L" else 100
    for tier, slice_kwh in enumerate(_slices(prev, kwh)):
        if slice_kwh == 0:
            continue
        band_pct = BAND_PCT[band]
        if tier == 0 and band == "N" and month in WINTER_MONTHS:
            band_pct = WINTER_NIGHT_TIER1_PCT
        # Both upper tiers receive the summer surcharge. The analog-meter
        # uplift applies to every tier, without changing accumulated usage.
        season = SUMMER_PCT if month in SUMMER_MONTHS and tier >= 1 else 100
        units += slice_kwh * RATE_TENTHS[tier] * band_pct * season * meter_pct
    # Combine exact tier costs before rounding this reading once.
    return _round_nearest(units, 10_000_000)


def _records(lines: Iterable[str]) -> Iterator[str]:
    """Reproduce byte-sized fgets records, including long-line fragments."""
    for line in lines:
        data = line.encode("utf-8", "surrogateescape")
        start = 0
        while start < len(data):
            end = min(start + _RECORD_BYTES, len(data))
            newline = data.find(b"\n", start, end)
            if newline >= 0:
                end = newline + 1
            yield data[start:end].decode("utf-8", "surrogateescape")
            start = end


def _tokenize(raw: str) -> list[str]:
    # fgets consumes the entire record, but C string processing sees only
    # the prefix before its first NUL byte.
    raw = raw.split("\0", 1)[0]
    return [tok for tok in _FIELD_SPLIT.split(raw) if tok]


def _is_digits(text: str) -> bool:
    """Non-empty ASCII decimal digits only."""
    return bool(text) and all(ch in _DIGITS for ch in text)


def _is_account(text: str) -> bool:
    """1 to 8 ASCII letters or digits."""
    return 1 <= len(text) <= 8 and all(ch in _ACCOUNT_CHARS for ch in text)


def _parse(tokens: list[str]) -> tuple[str | None, tuple[str, int, int, str, str] | None]:
    """Validate one record. Returns (error_code, reading); reading is None on error.

    Only the first six fields are consumed; trailing fields are ignored.
    Checks run in the engine's order: FMT, MONTH, KWH, BAND, METER.
    """
    if len(tokens) < 6 or tokens[0] != "M" or not _is_account(tokens[1]):
        return "FMT", None

    month_tok, kwh_tok, band, meter = tokens[2], tokens[3], tokens[4], tokens[5]
    if len(month_tok) != 2 or not _is_digits(month_tok) or not 1 <= int(month_tok) <= 13:
        return "MONTH", None
    if len(kwh_tok) > 6 or not _is_digits(kwh_tok):
        return "KWH", None
    if band not in ("D", "N", "W"):
        return "BAND", None
    if meter not in ("S", "L"):
        return "METER", None
    month = int(month_tok)
    if month == 13:
        month = 1
    return None, (tokens[1], month, int(kwh_tok), band, meter)


class _AccountLimitError(Exception):
    """The legacy engine aborts a batch when its account table is full."""


def _process(lines: Iterable[str]) -> Iterator[str]:
    accounts: dict[str, Account] = {}
    rejected = 0

    for raw in _records(lines):
        tokens = _tokenize(raw)
        if not tokens:
            continue
        echo = tokens[1] if len(tokens) >= 2 else "?"

        error, reading = _parse(tokens)
        if error is not None:
            yield f"R {echo} {error}"
            rejected += 1
            continue

        acct_tok, month, kwh, band, meter = reading
        # A validated zero-kWh reading is a no-op: it creates no account,
        # does not fix the display spelling, and changes no history.
        if kwh == 0:
            continue
        # Account lookup is ASCII case-insensitive (account tokens are ASCII
        # alphanumerics only). The first-seen spelling is displayed.
        key = acct_tok.lower()
        account = accounts.get(key)
        if account is None:
            if len(accounts) == _MAX_ACCOUNTS:
                raise _AccountLimitError("too many accounts")
            account = accounts[key] = Account(acct_tok)
        fee = _reading_fee(account.counter, kwh, month, band, meter)
        account.counter += kwh
        account.total_kwh += kwh
        account.bill += fee

    grand = 0
    for account in accounts.values():
        yield f"B {account.shown} {account.total_kwh} {account.bill}"
        grand += account.bill
    yield f"X {len(accounts)} {rejected} {grand}"


def process(lines: Iterable[str]) -> list[str]:
    """Return a batch's output in engine order."""
    return list(_process(lines))


def main() -> None:
    # Read raw bytes so record boundaries and rejected tokens survive text
    # decoding, including invalid UTF-8 and standalone carriage returns.
    records = (
        raw.decode("utf-8", "surrogateescape")
        for raw in iter(lambda: sys.stdin.buffer.readline(_RECORD_BYTES), b"")
    )
    try:
        for line in _process(records):
            sys.stdout.buffer.write((line + "\n").encode("utf-8", "surrogateescape"))
    except _AccountLimitError as error:
        sys.stderr.write(f"{error}\n")
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
