"""TollCore toll/congestion rating engine, Python implementation.

Drop-in behavioral replacement for the retired legacy binary (see
``legacy/README.md``). One batch per process: passages on stdin, rating
lines on stdout, trailer at end of input. The engine's observed behavior
is the contract; ``docs/SPEC.md`` agrees with it on the nominal path.

Engine behavior that the rules below reproduce:

- Lines end at LF. Fields are separated by runs of space, tab, or CR;
  other bytes stay inside a token. A NUL byte ends the line.
- Tokens are matched as ASCII only. Tokens past the seventh are ignored.
- Day 0 is day 7 (Sunday). Time 2400 is midnight.
- Gates 30 to 40 start the morning peak at 0645; gates 1 to 5 end the
  evening peak at 1929.
- The bus peak multiplier is x1.9; the class multiplier then applies.
- A motorcycle with three or more axles is rated as a car.
- A truck at gates 12 to 17 on a weekend is rated at x1.17 with no
  class multiplier.
- Each multiplication rounds to the nearest cent, ties to even.
"""

from __future__ import annotations

import re
import sys

BASE_CENTS = 250
PER_AXLE_CENTS = 40
CLASS_BP = {"C": 10_000, "T": 18_000, "B": 14_000, "M": 6_000}
PEAK_BP = 20_000
BUS_PEAK_BP = 19_000
FREIGHT_BP = 11_700
SIDECAR_MIN_AXLES = 3
FREIGHT_GATES = range(12, 18)
MORNING_GATES = range(30, 41)
EVENING_GATES = range(1, 6)
MORNING_START, MORNING_END = 700, 929
RIVER_MORNING_START = 645
EVENING_START, EVENING_END = 1600, 1859
RIVER_EVENING_END = 1929

_TOKEN = re.compile(r"[^ \t\r]+")
_TAG = re.compile(r"[A-Za-z0-9]{1,10}")


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round to the nearest integer, ties to even."""
    quotient, remainder = divmod(numerator, denominator)
    twice = 2 * remainder
    if twice > denominator or (twice == denominator and quotient % 2):
        return quotient + 1
    return quotient


def _ascii_digits(token: str, width: int) -> bool:
    return len(token) == width and all("0" <= ch <= "9" for ch in token)


def _tag_ok(tag: str) -> bool:
    return _TAG.fullmatch(tag) is not None


def _parse_time(token: str) -> int | None:
    """Return hhmm as an integer, or None when the engine rejects the time."""
    if not _ascii_digits(token, 4):
        return None
    if token == "2400":
        return 0
    hh, mm = int(token[:2]), int(token[2:])
    if hh > 23 or mm > 59:
        return None
    return hh * 100 + mm


def _in_peak(gate: int, hhmm: int) -> bool:
    morning_start = RIVER_MORNING_START if gate in MORNING_GATES else MORNING_START
    evening_end = RIVER_EVENING_END if gate in EVENING_GATES else EVENING_END
    return (morning_start <= hhmm <= MORNING_END
            or EVENING_START <= hhmm <= evening_end)


def _toll(gate: int, axles: int, hhmm: int, dow: int, cls: str) -> int:
    """Toll in cents for a validated passage; dow is 1 to 7."""
    base = BASE_CENTS + PER_AXLE_CENTS * (axles - 1)
    weekday = 1 <= dow <= 5
    if not weekday and cls == "T" and gate in FREIGHT_GATES:
        return _round_nearest(base * FREIGHT_BP, 10_000)
    if cls == "M" and axles >= SIDECAR_MIN_AXLES:
        cls = "C"
    if weekday and _in_peak(gate, hhmm):
        peak_bp = BUS_PEAK_BP if cls == "B" else PEAK_BP
        base = _round_nearest(base * peak_bp, 10_000)
    return _round_nearest(base * CLASS_BP[cls], 10_000)


class Engine:
    def __init__(self, out=None):
        self.count_ok = 0
        self.count_rej = 0
        self.sum_tolls = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, tag: str, code: str) -> None:
        self._emit(f"R {tag} {code}")
        self.count_rej += 1

    def handle(self, line: str) -> None:
        parts = _TOKEN.findall(line.partition("\x00")[0])
        if not parts:
            return
        tag_valid = len(parts) > 1 and _tag_ok(parts[1])
        tag = parts[1] if tag_valid else "??????????"
        if parts[0] != "T" or len(parts) < 7 or not tag_valid:
            self._reject(tag, "FMT")
            return
        gate_tok, axles_tok, time_tok, dow_tok, class_tok = parts[2:7]

        if not _ascii_digits(gate_tok, 2) or not 1 <= int(gate_tok) <= 40:
            self._reject(tag, "GATE")
            return
        gate = int(gate_tok)

        if not _ascii_digits(axles_tok, 1) or not 1 <= int(axles_tok) <= 6:
            self._reject(tag, "AXLES")
            return
        axles = int(axles_tok)

        hhmm = _parse_time(time_tok)
        if hhmm is None:
            self._reject(tag, "TIME")
            return

        if not _ascii_digits(dow_tok, 1) or not 0 <= int(dow_tok) <= 7:
            self._reject(tag, "DOW")
            return
        dow = int(dow_tok) or 7

        if class_tok not in CLASS_BP:
            self._reject(tag, "CLASS")
            return

        toll = _toll(gate, axles, hhmm, dow, class_tok)
        self._emit(f"F {tag} {toll}")
        self.count_ok += 1
        self.sum_tolls += toll

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_tolls}")


def main() -> None:
    engine = Engine()
    for raw in sys.stdin.buffer:
        engine.handle(raw.decode("latin-1").partition("\n")[0])
    engine.finish()


if __name__ == "__main__":
    main()
