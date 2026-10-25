"""PayrollCore withholding engine, Python implementation.

One batch per process: records on stdin, result lines on stdout, trailer at
end of input.  The retired engine's observable behavior is the contract.
"""

from __future__ import annotations

import sys

LEVY_BP = 620
LEVY_CAP = 1_600_000
STATE_BP = 500
ZERO_TAX_STATES = ("TX", "FL", "WA", "NV", "SD")


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round a nonnegative rational to the nearest integer, ties to even."""
    quotient, remainder = divmod(numerator, denominator)
    twice = remainder * 2
    if twice > denominator or (twice == denominator and quotient & 1):
        quotient += 1
    return quotient


def _round_up(numerator: int, denominator: int) -> int:
    """Round a nonnegative rational to the nearest integer, ties upward."""
    quotient, remainder = divmod(numerator, denominator)
    return quotient + (remainder * 2 >= denominator)


def _federal(gross: int, period: int, status: str, state: str) -> int:
    bracket_1, bracket_2 = (50_000, 200_000) if period == 27 else (100_000, 400_000)
    rates = [1_000, 2_000, 3_000]
    if status == "H" and state in ("CA", "NY") and gross > 250_000:
        rates[2] = 3_200

    tier_1 = min(gross, bracket_1)
    tier_2 = min(max(gross - bracket_1, 0), bracket_2 - bracket_1)
    tier_3 = max(gross - bracket_2, 0)
    numerator = sum(tier * rate for tier, rate in zip((tier_1, tier_2, tier_3), rates))
    federal = _round_nearest(numerator, 10_000)
    if status == "M":
        federal = _round_nearest(federal * 92, 100)
    return federal


class Engine:
    def __init__(self, out=None):
        self.ytd: dict[str, int] = {}
        self.ids: dict[str, str] = {}
        self.count_ok = 0
        self.count_rej = 0
        self.sum_net = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, empid: str, code: str) -> None:
        self._emit(f"R {empid} {code}")
        self.count_rej += 1

    def handle(self, line: str) -> None:
        line = line.rstrip("\r\n")
        if not line:
            return
        parts = line.split()
        empid = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(empid) <= 8 and empid.isascii() and empid.isalnum()
        if not id_ok:
            empid = "????????"
        if len(parts) < 7 or parts[0] != "P" or empid == "????????":
            self._reject(empid, "FMT")
            return
        _, empid, period_tok, gross_tok, status, state, flags = parts[:7]

        if not (len(period_tok) == 2 and period_tok.isascii() and period_tok.isdigit()):
            self._reject(empid, "PERIOD")
            return
        period = int(period_tok)
        if not 1 <= period <= 27:
            self._reject(empid, "PERIOD")
            return
        if not (
            1 <= len(gross_tok) <= 9
            and gross_tok.isascii()
            and gross_tok.isdigit()
            and int(gross_tok) > 0
        ):
            self._reject(empid, "GROSS")
            return
        gross = int(gross_tok)
        if status not in ("S", "M", "H"):
            self._reject(empid, "STATUS")
            return
        if not (
            len(state) == 2
            and state.isascii()
            and state.isalpha()
            and state.isupper()
        ):
            self._reject(empid, "STATE")
            return
        if flags != "000" and not (
            len(flags) == 3
            and flags.isascii()
            and flags.isalpha()
            and flags.isupper()
        ):
            self._reject(empid, "FLAGS")
            return

        key = empid.upper()
        canonical = self.ids.setdefault(key, empid)
        federal = _federal(gross, period, status, state)
        state_tax = 0
        if state not in ZERO_TAX_STATES:
            state_tax = _round_nearest(gross * STATE_BP, 10_000)

        ytd_before = self.ytd.get(key, 0)
        levy = 0 if ytd_before >= LEVY_CAP else _round_up(gross * LEVY_BP, 10_000)
        if "X" in flags and "B" in flags:
            levy += _round_up(gross * 100, 10_000)
        self.ytd[key] = ytd_before + gross

        net = gross - federal - state_tax - levy
        self._emit(f"W {canonical} {net}")
        self.count_ok += 1
        self.sum_net += net

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_net}")


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
