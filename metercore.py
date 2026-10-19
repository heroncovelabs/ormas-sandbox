"""MeterCore batch billing engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads meter
readings on stdin, writes per-account B lines and an X trailer on stdout.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import re
import sys

TIER1_LIMIT = 500
TIER2_LIMIT = 2000
# rate in tenths of a cent per kwh
RATE_TENTHS = (140, 190, 260)
BAND_PCT = {"D": 100, "N": 70, "W": 85}
SUMMER_MONTHS = (6, 7, 8, 9)
SUMMER_PCT = 110
MAX_ACCOUNTS = 8192

ERROR_CODES = ("FMT", "MONTH", "KWH", "BAND", "METER")

_TOKENS = re.compile(rb"[^ \t\r\n]+")


@dataclass(frozen=True)
class _Reading:
    shown: str
    month: int = 0
    kwh: int = 0
    band: str = ""
    meter: str = ""
    error: str | None = None


def _parse_reading(raw: bytes) -> _Reading | None:
    # The legacy tokenizer uses just these four ASCII separators and stops
    # at the first NUL. In particular, other Unicode whitespace is data.
    tokens = _TOKENS.findall(raw.split(b"\0", 1)[0])
    if not tokens:
        return None
    echo = tokens[1].decode("utf-8", "surrogateescape") if len(tokens) >= 2 else "?"
    if len(tokens) < 6 or tokens[0] != b"M":
        return _Reading(echo, error="FMT")
    if not (1 <= len(tokens[1]) <= 8 and tokens[1].isalnum()):
        return _Reading(echo, error="FMT")
    if len(tokens[2]) != 2 or not tokens[2].isdigit():
        return _Reading(echo, error="MONTH")
    month = int(tokens[2])
    if not 1 <= month <= 13:
        return _Reading(echo, error="MONTH")
    if not (1 <= len(tokens[3]) <= 6 and tokens[3].isdigit()):
        return _Reading(echo, error="KWH")
    if tokens[4] not in (b"D", b"N", b"W"):
        return _Reading(echo, error="BAND")
    if tokens[5] not in (b"S", b"L"):
        return _Reading(echo, error="METER")
    # 13 is accepted as January, independently of account history.
    return _Reading(echo, (month - 1) % 12 + 1, int(tokens[3]),
                    tokens[4].decode("ascii"), tokens[5].decode("ascii"))


def _parse_readings(lines: Iterable[str | bytes]) -> Iterator[_Reading]:
    for raw in lines:
        # The retired reader's 1024-byte buffer consumes at most 1023 bytes
        # at a time, with each chunk validated as a separate record.
        data = raw.encode("utf-8", "surrogateescape") if isinstance(raw, str) else raw
        for line in data.split(b"\n"):
            for offset in range(0, len(line), 1023):
                reading = _parse_reading(line[offset:offset + 1023])
                if reading is not None:
                    yield reading


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round to the nearest cent, with exact halves going to even."""
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
    for tier, slice_kwh in enumerate(_slices(prev, kwh)):
        if slice_kwh == 0:
            continue
        season = SUMMER_PCT if month in SUMMER_MONTHS and tier >= 1 else 100
        band_pct = 60 if tier == 0 and band == "N" and month in (12, 1, 2) else BAND_PCT[band]
        units += slice_kwh * RATE_TENTHS[tier] * band_pct * season
    # All tier slices contribute to one reading cost. Apply the analog-meter
    # uplift before the single rounding step, without floating-point loss.
    return _round_nearest(units * (103 if meter == "L" else 100), 10_000_000)


def _process(lines: Iterable[str | bytes]) -> Iterator[str]:
    accounts: dict[str, Account] = {}
    rejected = 0

    for reading in _parse_readings(lines):
        if reading.error is not None:
            yield f"R {reading.shown} {reading.error}"
            rejected += 1
            continue

        if reading.kwh == 0:
            continue
        key = reading.shown.lower()
        account = accounts.get(key)
        if account is None:
            if len(accounts) == MAX_ACCOUNTS:
                raise OverflowError("too many accounts")
            account = accounts[key] = Account(reading.shown)
        fee = _reading_fee(account.counter, reading.kwh, reading.month, reading.band, reading.meter)
        account.counter += reading.kwh
        account.total_kwh += reading.kwh
        account.bill += fee

    grand = 0
    for account in accounts.values():
        yield f"B {account.shown} {account.total_kwh} {account.bill}"
        grand += account.bill
    yield f"X {len(accounts)} {rejected} {grand}"


def process(lines: Iterable[str | bytes]) -> list[str]:
    return list(_process(lines))


def main() -> None:
    try:
        for line in _process(sys.stdin.buffer):
            sys.stdout.buffer.write((line + "\n").encode("utf-8", "surrogateescape"))
    except OverflowError as error:
        print(error, file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
