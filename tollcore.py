"""TollCore toll/congestion rating engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: passages on stdin, rating lines on stdout, trailer at end of
input. Format reference: ``docs/SPEC.md`` (mind the drift warning; the
engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys

BASE_CENTS = 250
PER_AXLE_CENTS = 40
CLASS_BP = {"C": 10_000, "T": 18_000, "B": 14_000, "M": 6_000}
PEAK_BP = 20_000
MORNING_START, MORNING_END = 700, 929
EVENING_START, EVENING_END = 1600, 1859

# Engine behavior not covered by the spec.
BUS_PEAK_BP = 13_300  # buses in a peak window use x1.33 instead of x1.4
WEEKEND_FREIGHT_GATES = range(12, 18)  # trucks on day 0/6/7 rate at x1.17
WEEKEND_FREIGHT_BP = 11_700
EARLY_MORNING_GATES = range(30, 41)  # river crossings: morning peak from 0645
EARLY_MORNING_START = 645
LATE_EVENING_GATES = range(1, 6)  # evening peak runs until 1929
LATE_EVENING_END = 1929
SIDECAR_MIN_AXLES = 3  # motorcycles with 3+ axles are rated as cars
LINE_CHUNK = 4095  # engine reads at most this many bytes per record

_ASCII_ALNUM = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
)


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round to the nearest cent, halves to even (as the engine does)."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (
        2 * remainder == denominator and quotient % 2 == 1
    ):
        return quotient + 1
    return quotient


def _tag_ok(tag: str) -> bool:
    return 1 <= len(tag) <= 10 and all(ch in _ASCII_ALNUM for ch in tag)


def _is_digits(tok: str) -> bool:
    return all("0" <= ch <= "9" for ch in tok)


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
        # The engine stops at a NUL byte and separates tokens only on
        # space, tab, CR and LF.
        line = line.split("\0", 1)[0]
        parts = re.split(r"[ \t\r\n]+", line.strip(" \t\r\n"))
        if parts == [""]:
            return
        tag_valid = len(parts) > 1 and _tag_ok(parts[1])
        tag = parts[1] if tag_valid else "??????????"
        # The engine ignores any tokens after the seventh.
        if parts[0] != "T" or len(parts) < 7 or not tag_valid:
            self._reject(tag, "FMT")
            return
        gate_tok, axles_tok, time_tok, dow_tok, class_tok = parts[2:7]

        if not (len(gate_tok) == 2 and _is_digits(gate_tok)):
            self._reject(tag, "GATE")
            return
        gate = int(gate_tok)
        if not 1 <= gate <= 40:
            self._reject(tag, "GATE")
            return

        if not (len(axles_tok) == 1 and _is_digits(axles_tok)):
            self._reject(tag, "AXLES")
            return
        axles = int(axles_tok)
        if not 1 <= axles <= 6:
            self._reject(tag, "AXLES")
            return

        if not (len(time_tok) == 4 and _is_digits(time_tok)):
            self._reject(tag, "TIME")
            return
        if time_tok == "2400":  # engine accepts 2400 as midnight
            time_tok = "0000"
        hh, mm = int(time_tok[:2]), int(time_tok[2:])
        if hh > 23 or mm > 59:
            self._reject(tag, "TIME")
            return
        hhmm = hh * 100 + mm

        if not (len(dow_tok) == 1 and _is_digits(dow_tok)):
            self._reject(tag, "DOW")
            return
        dow = int(dow_tok)
        if not 0 <= dow <= 7:  # engine accepts 0 as Sunday
            self._reject(tag, "DOW")
            return

        if class_tok not in CLASS_BP:
            self._reject(tag, "CLASS")
            return
        if class_tok == "M" and axles >= SIDECAR_MIN_AXLES:
            class_tok = "C"

        base = BASE_CENTS + PER_AXLE_CENTS * (axles - 1)
        morning_start = (
            EARLY_MORNING_START if gate in EARLY_MORNING_GATES else MORNING_START
        )
        evening_end = LATE_EVENING_END if gate in LATE_EVENING_GATES else EVENING_END
        peak = 1 <= dow <= 5 and (
            morning_start <= hhmm <= MORNING_END
            or EVENING_START <= hhmm <= evening_end
        )
        class_bp = CLASS_BP[class_tok]
        if peak and class_tok == "B":
            class_bp = BUS_PEAK_BP
        elif not 1 <= dow <= 5 and class_tok == "T" and gate in WEEKEND_FREIGHT_GATES:
            class_bp = WEEKEND_FREIGHT_BP
        toll = _round_nearest(base * (PEAK_BP if peak else 10_000), 10_000)
        toll = _round_nearest(toll * class_bp, 10_000)

        self._emit(f"F {tag} {toll}")
        self.count_ok += 1
        self.sum_tolls += toll

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_tolls}")


def main() -> None:
    engine = Engine()
    data = sys.stdin.buffer.read()
    pos = 0
    while pos < len(data):
        # Longer lines are split into consecutive LINE_CHUNK-byte records.
        nl = data.find(b"\n", pos, pos + LINE_CHUNK)
        end = nl + 1 if nl >= 0 else min(pos + LINE_CHUNK, len(data))
        engine.handle(data[pos:end].decode("latin-1"))
        pos = end
    engine.finish()


if __name__ == "__main__":
    main()
