"""TariffCore duty calculator, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
calculator per process: declarations on stdin, result lines on stdout,
trailer at end of input. Format reference: ``docs/SPEC.md`` (mind the
drift warning at the top; the engine's behavior is the contract).
"""

from __future__ import annotations

import sys

RATE_BANDS = (
    (1, 15, 250), (16, 27, 400), (28, 38, 650), (39, 49, 500),
    (50, 63, 800), (64, 83, 300), (84, 90, 150), (91, 97, 550),
)
CAP = 900_000
WEIGHT_RATE_CENTS = 40
AIR_DENSE_RATE_CENTS = 55
LEVY_ORIGINS = ("KP", "IR", "CU", "SY")


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
        body = line.rstrip("\r\n")
        if not body:
            return
        parts = body.split()
        declid = parts[1] if len(parts) > 1 else ""
        id_ok = (1 <= len(declid) <= 10 and declid.isascii()
                 and declid.isalnum())
        if not parts or parts[0] != "D" or len(parts) < 8 or not id_ok:
            self._emit(f"R {declid if id_ok else '??????????'} FMT")
            self.count_rej += 1
            return
        declid, origin, hs, mode, currency, value_tok, weight_tok = parts[1:8]
        if not (len(origin) == 2 and origin.isascii() and origin.isalpha()
                and origin.isupper()):
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
        if not (value_tok.isascii() and value_tok.isdigit()
                and 1 <= len(value_tok) <= 9):
            self._reject(declid, "VALUE")
            return
        if not (weight_tok.isascii() and weight_tok.isdigit()
                and 1 <= len(weight_tok) <= 8):
            self._reject(declid, "WEIGHT")
            return
        value, weight_dg = int(value_tok), int(weight_tok)
        chapter = int(hs[:2])
        if chapter < 1:
            self._reject(declid, "HS")
            return

        duty = 0
        if chapter < 98:
            rate_bp = None
            for lo, hi, bp in RATE_BANDS:
                if lo <= chapter <= hi:
                    rate_bp = bp
                    break
            if rate_bp is None:
                self._reject(declid, "HS")
                return
            if (value >= 2_000_000 and declid[-2:].isdigit()
                    and int(declid[-2:]) >= 25):
                duty = value * rate_bp // 10_000
            else:
                duty = _round_even(value * rate_bp, 10_000)

        levy = 0
        if origin in LEVY_ORIGINS and 28 <= chapter <= 38:
            levy = (value * 130 * 2 + 10_000) // 20_000  # half up

        kilograms = -(-weight_dg // 10_000)  # ceiling kg
        if mode == "A" and 51 <= kilograms <= 100:
            weight_fee = kilograms * AIR_DENSE_RATE_CENTS
        elif mode == "S" and currency == "JPY":
            weight_fee = 0
        else:
            weight_fee = kilograms * WEIGHT_RATE_CENTS

        duty = min(duty, CAP)
        levy = min(levy, CAP - duty)
        total = duty + levy + weight_fee
        self._emit(f"T {declid} {duty} {weight_fee} {levy} {total}")
        self.count_ok += 1
        self.sum_total += total

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_total}")


def _round_even(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (
            2 * remainder == denominator and quotient % 2 == 1):
        return quotient + 1
    return quotient


def main() -> None:
    calculator = Calculator()
    for line in sys.stdin:
        calculator.handle(line)
    calculator.finish()


if __name__ == "__main__":
    main()
