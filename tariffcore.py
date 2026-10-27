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
EXEMPT_CHAPTERS = (98, 99)
CAP = 900_000
WEIGHT_RATE_CENTS = 40
DENSE_AIR_KG = (50, 100)  # air shipments over 50 kg up to 100 kg
DENSE_AIR_RATE_CENTS = 55
LEVY_ORIGINS = ("CU", "IR", "KP", "SY")
LEVY_CHAPTERS = (28, 38)
LEVY_RATE_BP = 130
AUDIT_MIN_VALUE = 2_000_000


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

    def handle(self, line: str | bytes) -> None:
        # The engine treats input as bytes: a record ends at the first CR or
        # NUL, and only ASCII whitespace separates fields.
        if isinstance(line, str):
            line = line.encode("utf-8", "surrogateescape")
        line = re.split(rb"[\r\n\0]", line, maxsplit=1)[0]
        if not line:
            return  # only truly empty records are skipped; blank ones are FMT
        parts = [p.decode("latin-1") for p in line.split()]
        declid = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(declid) <= 10 and declid.isascii() and declid.isalnum()
        # The engine ignores any fields after the eighth.
        if len(parts) < 8 or parts[0] != "D" or not id_ok:
            self._emit(f"R {declid if id_ok else '??????????'} FMT")
            self.count_rej += 1
            return
        _, declid, origin, hs, mode, currency, value_tok, weight_tok = parts[:8]
        if not (len(origin) == 2 and origin.isascii() and origin.isalpha()
                and origin.isupper()):
            self._reject(declid, "ORIGIN")
            return
        if not (len(hs) == 6 and _is_digits(hs)):
            self._reject(declid, "HS")
            return
        if mode not in ("A", "S", "R"):
            self._reject(declid, "MODE")
            return
        if currency not in ("USD", "EUR", "JPY"):
            self._reject(declid, "CUR")
            return
        if not (_is_digits(value_tok) and 1 <= len(value_tok) <= 9):
            self._reject(declid, "VALUE")
            return
        if not (_is_digits(weight_tok) and 1 <= len(weight_tok) <= 8):
            self._reject(declid, "WEIGHT")
            return
        value, weight_dg = int(value_tok), int(weight_tok)
        chapter = int(hs[:2])
        if chapter < 1:
            self._reject(declid, "HS")
            return

        duty = 0
        levy = 0
        if chapter not in EXEMPT_CHAPTERS:
            rate_bp = None
            for lo, hi, bp in RATE_BANDS:
                if lo <= chapter <= hi:
                    rate_bp = bp
                    break
            if rate_bp is None:
                self._reject(declid, "HS")
                return
            # Engine audit mode: large declarations whose id ends in 25-99
            # (month-end batches) truncate instead of rounding.
            if value >= AUDIT_MIN_VALUE and _audit_suffix(declid):
                duty = (value * rate_bp) // 10_000
            else:
                duty = _round_half_even(value * rate_bp, 10_000)
            if origin in LEVY_ORIGINS and LEVY_CHAPTERS[0] <= chapter <= LEVY_CHAPTERS[1]:
                levy = _round_half_up(value * LEVY_RATE_BP, 10_000)

        # The cap applies to duty and levy only, duty first.
        duty = min(duty, CAP)
        levy = min(levy, CAP - duty)

        kilograms = -(-weight_dg // 10_000)  # engine charges per started kg
        if currency == "JPY" and mode == "S":
            weight_fee = 0
        elif mode == "A" and DENSE_AIR_KG[0] < kilograms <= DENSE_AIR_KG[1]:
            weight_fee = kilograms * DENSE_AIR_RATE_CENTS
        else:
            weight_fee = kilograms * WEIGHT_RATE_CENTS

        total = duty + weight_fee + levy
        self._emit(f"T {declid} {duty} {weight_fee} {levy} {total}")
        self.count_ok += 1
        self.sum_total += total

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_total}")


def _round_half_up(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder >= denominator:
        return quotient + 1
    return quotient


def _round_half_even(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient % 2):
        return quotient + 1
    return quotient


def _audit_suffix(declid: str) -> bool:
    tail = declid[-2:]
    return len(tail) == 2 and _is_digits(tail) and int(tail) >= 25


def _is_digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


def main() -> None:
    calculator = Calculator()
    for line in sys.stdin.buffer:
        calculator.handle(line)
    calculator.finish()


if __name__ == "__main__":
    main()
