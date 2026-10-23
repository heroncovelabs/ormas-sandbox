"""TariffCore duty calculator, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
calculator per process: declarations on stdin, result lines on stdout,
trailer at end of input. Format reference: ``docs/SPEC.md`` (mind the
drift warning at the top; the engine's behavior is the contract).

Engine behavior that differs from (or is missing in) the spec:

- duty rounds half to even, except "month-end" declarations (declid ending
  in two digits >= 25) with value >= 2000000, whose duty is truncated;
- chapter 98 is exempt from duty, like 99;
- weight is charged per started kilogram (ceiling), at 55 cents/kg for air
  shipments over 50 kg up to 100 kg; JPY sea shipments pay no weight fee;
- origins KP, IR, CU, SY on chapters 28-38 carry a levy of 20% of the
  duty, computed from the value and rounded half up;
- the cap applies to duty plus levy, not to the weight fee.
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
DENSE_AIR_RATE_CENTS = 55
LEVY_ORIGINS = ("KP", "IR", "CU", "SY")
LEVY_CHAPTERS = (28, 38)
AUDIT_VALUE = 2_000_000
AUDIT_DAY = 25
LINE_CHUNK = 511

_C_SPACE = " \t\n\v\f\r"
_WHITESPACE = re.compile("[ \t\n\v\f\r]+")
_DIGITS = frozenset("0123456789")
_UPPER = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
_ALNUM = _DIGITS | _UPPER | frozenset("abcdefghijklmnopqrstuvwxyz")


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
        parts = _WHITESPACE.split(line.strip(_C_SPACE))
        if parts == [""]:
            parts = []
        # The engine reads the record type into a 7-character field; the
        # rest of an over-long first token is read as the declid.
        if parts and len(parts[0]) > 7:
            parts[:1] = [parts[0][:7], parts[0][7:]]
        declid = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(declid) <= 10 and _only(declid, _ALNUM)
        # Tokens past the eighth are ignored.
        if not parts or parts[0] != "D" or len(parts) < 8 or not id_ok:
            self._emit(f"R {declid if id_ok else '??????????'} FMT")
            self.count_rej += 1
            return
        _, declid, origin, hs, mode, currency, value_tok, weight_tok = parts[:8]
        if not (len(origin) == 2 and _only(origin, _UPPER)):
            self._reject(declid, "ORIGIN")
            return
        if not (len(hs) == 6 and _only(hs, _DIGITS)):
            self._reject(declid, "HS")
            return
        if mode not in ("A", "S", "R"):
            self._reject(declid, "MODE")
            return
        if currency not in ("USD", "EUR", "JPY"):
            self._reject(declid, "CUR")
            return
        if not (_only(value_tok, _DIGITS) and 1 <= len(value_tok) <= 9):
            self._reject(declid, "VALUE")
            return
        if not (_only(weight_tok, _DIGITS) and 1 <= len(weight_tok) <= 8):
            self._reject(declid, "WEIGHT")
            return
        value, weight_dg = int(value_tok), int(weight_tok)
        chapter = int(hs[:2])
        if chapter < 1:
            self._reject(declid, "HS")
            return

        duty = 0
        rate_bp = 0
        if chapter not in EXEMPT_CHAPTERS:
            rate_bp = None
            for lo, hi, bp in RATE_BANDS:
                if lo <= chapter <= hi:
                    rate_bp = bp
                    break
            if rate_bp is None:
                self._reject(declid, "HS")
                return
            if _month_end(declid) and value >= AUDIT_VALUE:
                duty = value * rate_bp // 10_000
            else:
                duty = _round_half_even(value * rate_bp, 10_000)

        levy = 0
        if origin in LEVY_ORIGINS and LEVY_CHAPTERS[0] <= chapter <= LEVY_CHAPTERS[1]:
            levy = _round_half_up(value * rate_bp * 2, 100_000)
        duty = min(duty, CAP)
        levy = min(levy, CAP - duty)

        kilograms = -(-weight_dg // 10_000)
        if mode == "S" and currency == "JPY":
            weight_fee = 0
        elif mode == "A" and 50 < kilograms <= 100:
            weight_fee = kilograms * DENSE_AIR_RATE_CENTS
        else:
            weight_fee = kilograms * WEIGHT_RATE_CENTS

        total = duty + levy + weight_fee
        self._emit(f"T {declid} {duty} {weight_fee} {levy} {total}")
        self.count_ok += 1
        self.sum_total += total

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_total}")


def _only(token: str, allowed: frozenset) -> bool:
    return all(ch in allowed for ch in token)


def _month_end(declid: str) -> bool:
    tail = declid[-2:]
    return len(tail) == 2 and _only(tail, _DIGITS) and int(tail) >= AUDIT_DAY


def _round_half_even(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient % 2):
        return quotient + 1
    return quotient


def _round_half_up(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder >= denominator:
        return quotient + 1
    return quotient


def _records(data: bytes):
    """Split input the way the engine reads it: 511-byte line chunks, each
    cut at the first NUL, CR or LF; chunks left empty are skipped."""
    pos = 0
    while pos < len(data):
        end = data.find(b"\n", pos, pos + LINE_CHUNK)
        end = pos + LINE_CHUNK if end < 0 else end + 1
        chunk = data[pos:end]
        pos = end
        for stop in (b"\x00", b"\r", b"\n"):
            chunk = chunk.split(stop, 1)[0]
        if chunk:
            yield chunk.decode("latin-1")


def main() -> None:
    calculator = Calculator()
    for record in _records(sys.stdin.buffer.read()):
        calculator.handle(record)
    calculator.finish()


if __name__ == "__main__":
    main()
