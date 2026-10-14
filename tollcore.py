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
BUS_PEAK_BP = 19_000
WEEKEND_FREIGHT_BP = 6_500
MORNING_START, MORNING_END = 700, 929
EVENING_START, EVENING_END = 1600, 1859
# The legacy reader processes at most 4095 bytes per record, including LF.
MAX_RECORD_BYTES = 4095


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round to the nearest cent, resolving exact halves to an even cent."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (
        2 * remainder == denominator and quotient % 2
    ):
        return quotient + 1
    return quotient


def _tag_ok(tag: str) -> bool:
    return 1 <= len(tag) <= 10 and tag.isascii() and tag.isalnum()


def _digits_ok(token: str, width: int) -> bool:
    return len(token) == width and token.isascii() and token.isdigit()


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
        # Match the legacy C-string tokenizer: NUL ends the record, and
        # only space, tab, CR, and LF separate tokens. Extra tokens are ignored.
        parts = re.findall(r"[^ \t\r\n]+", line.partition("\0")[0])
        if not parts:
            return
        tag_valid = len(parts) > 1 and _tag_ok(parts[1])
        tag = parts[1] if tag_valid else "??????????"
        if parts[0] != "T" or len(parts) < 7 or not tag_valid:
            self._reject(tag, "FMT")
            return
        gate_tok, axles_tok, time_tok, dow_tok, class_tok = parts[2:7]

        if not _digits_ok(gate_tok, 2):
            self._reject(tag, "GATE")
            return
        gate = int(gate_tok)
        if not 1 <= gate <= 40:
            self._reject(tag, "GATE")
            return

        if not _digits_ok(axles_tok, 1):
            self._reject(tag, "AXLES")
            return
        axles = int(axles_tok)
        if not 1 <= axles <= 6:
            self._reject(tag, "AXLES")
            return

        if not _digits_ok(time_tok, 4):
            self._reject(tag, "TIME")
            return
        hh, mm = int(time_tok[:2]), int(time_tok[2:])
        if time_tok == "2400":
            hh = 0
        if hh > 23 or mm > 59:
            self._reject(tag, "TIME")
            return
        hhmm = hh * 100 + mm

        if not _digits_ok(dow_tok, 1):
            self._reject(tag, "DOW")
            return
        dow = int(dow_tok)
        if not 0 <= dow <= 7:
            self._reject(tag, "DOW")
            return
        if dow == 0:
            dow = 7

        if class_tok not in CLASS_BP:
            self._reject(tag, "CLASS")
            return

        # Sidecar motorcycles are rated as cars starting at three axles.
        if class_tok == "M" and axles >= 3:
            class_tok = "C"

        base = BASE_CENTS + PER_AXLE_CENTS * (axles - 1)
        morning_start = 645 if gate >= 30 else MORNING_START
        evening_end = 1929 if gate <= 5 else EVENING_END
        peak = 1 <= dow <= 5 and (
            morning_start <= hhmm <= MORNING_END
            or EVENING_START <= hhmm <= evening_end
        )
        time_bp = 10_000
        if peak:
            time_bp = BUS_PEAK_BP if class_tok == "B" else PEAK_BP
        elif dow >= 6 and 12 <= gate <= 17 and class_tok == "T":
            time_bp = WEEKEND_FREIGHT_BP
        # Keep all factors exact until the final nearest-even rounding.
        toll = _round_nearest(base * time_bp * CLASS_BP[class_tok], 10_000**2)

        self._emit(f"F {tag} {toll}")
        self.count_ok += 1
        self.sum_tolls += toll

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_tolls}")


def main() -> None:
    engine = Engine()
    while True:
        line = sys.stdin.buffer.readline(MAX_RECORD_BYTES)
        if not line:
            break
        # Preserve CR separators and byte boundaries from the reference reader.
        engine.handle(line.decode("ascii", errors="surrogateescape"))
    engine.finish()


if __name__ == "__main__":
    main()
