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
BUS_PEAK_BP = 13_300  # buses rate at x1.33 (not x1.4) inside peak windows
WEEKEND_FREIGHT_GATES = range(12, 18)  # trucks at x1.17 on weekends here
WEEKEND_FREIGHT_BP = 11_700
EARLY_MORNING_GATES = range(30, 41)  # river crossings: morning peak from 0645
EARLY_MORNING_START = 645
LATE_EVENING_GATES = range(1, 6)  # first gates: evening peak until 1929
LATE_EVENING_END = 1929
SIDECAR_MIN_AXLES = 3  # motorcycles with 3+ axles are rated as cars


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round to the nearest cent, halves to even (the engine's mode)."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient % 2):
        return quotient + 1
    return quotient


def _tag_ok(tag: str) -> bool:
    return 1 <= len(tag) <= 10 and tag.isascii() and tag.isalnum()


def _digits(tok: str, width: int) -> bool:
    return len(tok) == width and tok.isascii() and tok.isdigit()


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
        # The engine reads C strings (NUL ends the line) and only splits on
        # spaces, tabs and line terminators.
        line = line.split("\0", 1)[0]
        parts = [p for p in re.split(r"[ \t\r\n]+", line) if p]
        if not parts:
            return
        tag_valid = len(parts) > 1 and _tag_ok(parts[1])
        tag = parts[1] if tag_valid else "??????????"
        # The engine ignores trailing tokens past the class.
        if parts[0] != "T" or len(parts) < 7 or not tag_valid:
            self._reject(tag, "FMT")
            return
        gate_tok, axles_tok, time_tok, dow_tok, class_tok = parts[2:7]

        if not _digits(gate_tok, 2):
            self._reject(tag, "GATE")
            return
        gate = int(gate_tok)
        if not 1 <= gate <= 40:
            self._reject(tag, "GATE")
            return

        if not _digits(axles_tok, 1):
            self._reject(tag, "AXLES")
            return
        axles = int(axles_tok)
        if not 1 <= axles <= 6:
            self._reject(tag, "AXLES")
            return

        if not _digits(time_tok, 4):
            self._reject(tag, "TIME")
            return
        hh, mm = int(time_tok[:2]), int(time_tok[2:])
        if time_tok == "2400":
            hh, mm = 0, 0
        if hh > 23 or mm > 59:
            self._reject(tag, "TIME")
            return
        hhmm = hh * 100 + mm

        if not _digits(dow_tok, 1):
            self._reject(tag, "DOW")
            return
        dow = int(dow_tok)
        if dow == 0:
            dow = 7
        if not 1 <= dow <= 7:
            self._reject(tag, "DOW")
            return

        if class_tok not in CLASS_BP:
            self._reject(tag, "CLASS")
            return
        if class_tok == "M" and axles >= SIDECAR_MIN_AXLES:
            class_tok = "C"

        morning_start = (
            EARLY_MORNING_START if gate in EARLY_MORNING_GATES else MORNING_START
        )
        evening_end = LATE_EVENING_END if gate in LATE_EVENING_GATES else EVENING_END
        base = BASE_CENTS + PER_AXLE_CENTS * (axles - 1)
        peak = 1 <= dow <= 5 and (
            morning_start <= hhmm <= MORNING_END
            or EVENING_START <= hhmm <= evening_end
        )
        class_bp = CLASS_BP[class_tok]
        if class_tok == "B" and peak:
            class_bp = BUS_PEAK_BP
        if class_tok == "T" and dow >= 6 and gate in WEEKEND_FREIGHT_GATES:
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
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
