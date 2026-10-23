"""MeterCore batch billing engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads meter
readings on stdin, writes per-account B lines and an X trailer on stdout.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).
"""

from __future__ import annotations

import sys
from typing import NamedTuple

# Legacy engine reads stdin through a 1024-byte buffer (fgets-style): a read
# returns at most 1023 bytes, ending early at a newline. Longer lines are
# therefore delivered as several records.
_READ_CHUNK = 1023

TIER1_LIMIT = 500
TIER2_LIMIT = 2000
# rate in tenths of a cent per kwh
RATE_TENTHS = (140, 190, 260)
BAND_PCT = {"D": 100, "N": 70, "W": 85}
# winter night discount: tier-1 energy of an N reading in these months is billed at 60%.
WINTER_MONTHS = (12, 1, 2)
WINTER_NIGHT_TIER1_PCT = 60
SUMMER_MONTHS = (6, 7, 8, 9)
# summer surcharge applies to tier-2 and tier-3 energy.
SUMMER_PCT = 110
# meter type uplift, percent of the computed fee.
METER_PCT = {"S": 100, "L": 103}

ERROR_CODES = ("FMT", "MONTH", "KWH", "BAND", "METER")


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round to the nearest whole unit; exact halves go to the even neighbour."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient % 2 == 1):
        return quotient + 1
    return quotient


class Account:
    def __init__(self, shown: str):
        self.shown = shown  # display spelling from the first accepted reading
        self.counter = 0    # cumulative kwh used to position tiers
        self.total_kwh = 0  # total reported usage
        self.bill = 0


def _slices(prev: int, kwh: int) -> tuple[int, int, int]:
    s1 = max(0, min(TIER1_LIMIT - prev, kwh))
    s2 = max(0, min(TIER2_LIMIT - max(prev, TIER1_LIMIT), kwh - s1))
    return s1, s2, kwh - s1 - s2


def _reading_fee(prev: int, kwh: int, month: int, band: str, meter: str = "S") -> int:
    """Cents for one reading. Tiers, rates and percentages are combined before rounding."""
    total = 0
    for tier, slice_kwh in enumerate(_slices(prev, kwh)):
        if slice_kwh == 0:
            continue
        band_pct = BAND_PCT[band]
        if tier == 0 and band == "N" and month in WINTER_MONTHS:
            band_pct = WINTER_NIGHT_TIER1_PCT
        season = SUMMER_PCT if month in SUMMER_MONTHS and tier >= 1 else 100
        total += slice_kwh * RATE_TENTHS[tier] * band_pct * season
    # tenths of a cent -> cents (/10), percentages (/100 each for band, season, meter)
    return _round_nearest(total * METER_PCT[meter], 10_000_000)


class _Parsed(NamedTuple):
    """Outcome of parsing one record: a reading, or a rejection with its echo."""

    echo: str
    error: str | None
    account: str = ""
    month: int = 0
    kwh: int = 0
    band: str = ""
    meter: str = ""


def _record_text(raw: str) -> str:
    """Text the legacy engine sees for one record: up to newline, then up to NUL."""
    raw = raw.split("\n", 1)[0]
    return raw.split("\x00", 1)[0]


def _tokenize(text: str) -> list[str]:
    """Split on runs of space, tab, and CR only (no other Unicode or control whitespace)."""
    return [tok for tok in text.replace("\t", " ").replace("\r", " ").split(" ") if tok]


def _is_ascii_digits(tok: str) -> bool:
    return tok.isascii() and tok.isdigit()


def _is_ascii_alnum(tok: str) -> bool:
    return tok.isascii() and tok.isalnum()


def _parse_record(raw: str) -> _Parsed | None:
    """Parse one record. Returns None for a blank record, which is skipped silently."""
    tokens = _tokenize(_record_text(raw))
    if not tokens:
        return None
    echo = tokens[1] if len(tokens) >= 2 else "?"

    # Field count is a minimum: the engine ignores any tokens after the sixth.
    if len(tokens) < 6 or tokens[0] != "M":
        return _Parsed(echo, "FMT")
    account = tokens[1]
    if not (1 <= len(account) <= 8 and _is_ascii_alnum(account)):
        return _Parsed(echo, "FMT")

    month_tok = tokens[2]
    if len(month_tok) != 2 or not _is_ascii_digits(month_tok):
        return _Parsed(echo, "MONTH")
    month = int(month_tok)
    if month == 13:
        # Month 13 is accepted and is the same calendar month as 01.
        month = 1
    if not 1 <= month <= 12:
        return _Parsed(echo, "MONTH")

    kwh_tok = tokens[3]
    if not (1 <= len(kwh_tok) <= 6 and _is_ascii_digits(kwh_tok)):
        return _Parsed(echo, "KWH")

    band = tokens[4]
    if band not in ("D", "N", "W"):
        return _Parsed(echo, "BAND")

    if tokens[5] not in ("S", "L"):
        return _Parsed(echo, "METER")

    return _Parsed(echo, None, account, month, int(kwh_tok), band, tokens[5])


def process(lines: list[str]) -> list[str]:
    out: list[str] = []
    # keyed by case-folded account id; dict order is first-seen order of accepted, nonzero readings
    accounts: dict[str, Account] = {}
    rejected = 0

    for raw in lines:
        parsed = _parse_record(raw)
        if parsed is None:
            continue
        if parsed.error is not None:
            out.append(f"R {parsed.echo} {parsed.error}")
            rejected += 1
            continue
        if parsed.kwh == 0:
            # zero-kwh readings are accepted but are a no-op: no account, no display, no history.
            continue

        key = parsed.account.lower()
        account = accounts.get(key)
        if account is None:
            account = accounts[key] = Account(parsed.account)
        fee = _reading_fee(account.counter, parsed.kwh, parsed.month, parsed.band, parsed.meter)
        account.counter += parsed.kwh
        account.total_kwh += parsed.kwh
        account.bill += fee

    grand = 0
    for account in accounts.values():
        out.append(f"B {account.shown} {account.total_kwh} {account.bill}")
        grand += account.bill
    out.append(f"X {len(accounts)} {rejected} {grand}")
    return out


def _records(data: bytes) -> list[str]:
    """Split raw stdin bytes into the records the legacy reader would deliver.

    Each record is decoded one character per byte (latin-1), so byte values
    survive unchanged through parsing and back out to stdout.
    """
    records: list[str] = []
    pos = 0
    while pos < len(data):
        end = min(pos + _READ_CHUNK, len(data))
        newline = data.find(b"\n", pos, end)
        if newline != -1:
            end = newline + 1
        records.append(data[pos:end].decode("latin-1"))
        pos = end
    return records


def _read_stdin() -> bytes:
    stream = getattr(sys.stdin, "buffer", None)
    if stream is not None:
        return stream.read()
    return sys.stdin.read().encode("utf-8")


def _write_stdout(payload: bytes) -> None:
    stream = getattr(sys.stdout, "buffer", None)
    if stream is not None:
        stream.write(payload)
        stream.flush()
    else:
        sys.stdout.write(payload.decode("utf-8", errors="replace"))


def main() -> None:
    lines = process(_records(_read_stdin()))
    _write_stdout("".join(line + "\n" for line in lines).encode("latin-1"))


if __name__ == "__main__":
    main()
