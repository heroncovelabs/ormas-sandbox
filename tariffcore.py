"""TariffCore duty calculator, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
calculator per process: declarations on stdin, result lines on stdout,
trailer at end of input. Format reference: ``docs/SPEC.md`` (mind the
drift warning at the top; the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys

RATE_BANDS = (
    (1, 15, 250), (16, 27, 400), (28, 38, 650), (39, 49, 500),
    (50, 63, 800), (64, 83, 300), (84, 90, 150), (91, 97, 550),
)
CAP = 900_000
WEIGHT_RATE_CENTS = 40


class Calculator:
    def __init__(self, out=None):
        self.count_ok = 0
        self.count_rej = 0
        self.sum_total = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, declid: str, code: str) -> None:
        self._emit(f"R {declid} {code}")
        self.count_rej += 1

    def handle(self, line: str) -> None:
        # The engine terminates records at CR, LF, or NUL and scans eight
        # width-limited ASCII fields, ignoring anything left over.
        line = re.split(r"[\r\n\x00]", line, maxsplit=1)[0]
        if not line:
            return
        parts = []
        offset = 0
        for width in (7, 63, 63, 63, 63, 63, 63, 63):
            match = re.match(r"\s*(\S{1,%d})" % width, line[offset:], re.ASCII)
            if match is None:
                break
            parts.append(match[1])
            offset += match.end()
        declid = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(declid) <= 10 and declid.isascii() and declid.isalnum()
        if not parts or parts[0] != "D" or len(parts) != 8 or not id_ok:
            self._emit(f"R {declid if id_ok else '??????????'} FMT")
            self.count_rej += 1
            return
        _, declid, origin, hs, mode, currency, value_tok, weight_tok = parts
        if not (len(origin) == 2 and all("A" <= c <= "Z" for c in origin)):
            self._reject(declid, "ORIGIN")
            return
        if not (len(hs) == 6 and hs.isascii() and hs.isdigit()):
            self._reject(declid, "HS")
            return
        if mode not in ("A", "S", "R"):
            self._reject(declid, "MODE")
            return
        if currency not in ("USD", "EUR", "JPY"):
            self._reject(declid, "CUR")
            return
        if not (value_tok.isascii() and value_tok.isdigit() and 1 <= len(value_tok) <= 9):
            self._reject(declid, "VALUE")
            return
        if not (weight_tok.isascii() and weight_tok.isdigit() and 1 <= len(weight_tok) <= 8):
            self._reject(declid, "WEIGHT")
            return
        value, weight_dg = int(value_tok), int(weight_tok)
        chapter = int(hs[:2])
        if chapter < 1:
            self._reject(declid, "HS")
            return

        duty = 0
        if chapter not in (98, 99):
            rate_bp = None
            for lo, hi, bp in RATE_BANDS:
                if lo <= chapter <= hi:
                    rate_bp = bp
                    break
            if rate_bp is None:
                self._reject(declid, "HS")
                return
            # Large declarations with a numeric suffix of 25 or above use
            # the engine's audit rounding: truncate duty to whole cents.
            suffix = declid[-2:]
            audit = value >= 2_000_000 and len(suffix) == 2 and suffix.isdigit() and int(suffix) >= 25
            numerator = value * rate_bp
            duty = numerator // 10_000 if audit else _round_nearest(numerator, 10_000)

        # The levy is assessed independently on value at 130 basis points,
        # using half-up rounding even when duty uses audit rounding.
        levy = 0
        if origin in ("KP", "IR", "CU", "SY") and 28 <= chapter <= 38:
            levy = (value * 130 + 5_000) // 10_000

        kilograms = (weight_dg + 9_999) // 10_000
        weight_rate = 55 if mode == "A" and 50 < kilograms <= 100 else WEIGHT_RATE_CENTS
        weight_fee = kilograms * weight_rate
        if mode == "S" and currency == "JPY":
            weight_fee = 0

        # Preserve duty first, then levy, within the cap. Weight is added
        # after the capped assessment and remains fully payable.
        duty = min(duty, CAP)
        levy = min(levy, CAP - duty)
        total = duty + levy + weight_fee
        self._emit(f"T {declid} {duty} {weight_fee} {levy} {total}")
        self.count_ok += 1
        self.sum_total += total

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_total}")


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round an exact rational amount to the nearest cent, ties to even."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient % 2):
        return quotient + 1
    return quotient


def main() -> None:
    calculator = Calculator()
    # Match fgets with its 512-byte buffer, preserving embedded CR and
    # counting each 511-byte chunk as a separate record.
    for line in iter(lambda: sys.stdin.buffer.readline(511), b""):
        calculator.handle(line.decode("latin-1"))
    calculator.finish()


if __name__ == "__main__":
    main()
