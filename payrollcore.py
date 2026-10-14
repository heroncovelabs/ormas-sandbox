"""PayrollCore withholding engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: records on stdin, result lines on stdout, trailer at end of
input. Format reference: ``docs/SPEC.md`` (mind the drift warning; the
engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys

BRACKET_1 = 100_000
BRACKET_2 = 400_000
RATES_BP = (1_000, 2_000, 3_000)
MARRIED_PERCENT = 92
HOUSEHOLD_THRESHOLD = 250_000
HOUSEHOLD_TOP_BP = 3_200
STATE_BP = 500
ZERO_TAX_STATES = ("TX", "FL", "WA", "NV", "SD")
LEVY_BP = 620
LEVY_CAP = 1_600_000
RECAPTURE_BP = 100
MAX_EMPLOYEES = 4_096
INPUT_CHUNK_BYTES = 511


class Engine:
    def __init__(self, out=None):
        self.ytd: dict[str, int] = {}
        self.employee_ids: dict[str, str] = {}
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
        # The reference terminates each input chunk at the first CR, LF or NUL.
        line = re.split(r"[\r\n\x00]", line, maxsplit=1)[0]
        if not line:
            return
        parts = re.findall(r"[^ \t\v\f\r\n]+", line)
        empid = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(empid) <= 8 and empid.isascii() and empid.isalnum()
        if len(parts) < 7 or parts[0] != "P" or not id_ok:
            self._reject(empid if id_ok else "????????", "FMT")
            return
        _, empid, period_tok, gross_tok, status, state, flags = parts[:7]
        if not (len(period_tok) == 2 and period_tok.isascii() and period_tok.isdigit()):
            self._reject(empid, "PERIOD")
            return
        period = int(period_tok)
        if not 1 <= period <= 27:
            self._reject(empid, "PERIOD")
            return
        if not (1 <= len(gross_tok) <= 9 and gross_tok.isascii() and gross_tok.isdigit()):
            self._reject(empid, "GROSS")
            return
        gross = int(gross_tok)
        if gross == 0:
            self._reject(empid, "GROSS")
            return
        if status not in ("S", "M", "H"):
            self._reject(empid, "STATUS")
            return
        if not (len(state) == 2 and state.isascii() and state.isalpha() and state.isupper()):
            self._reject(empid, "STATE")
            return
        if flags != "000" and not (
            len(flags) == 3 and flags.isascii() and flags.isalpha() and flags.isupper()
        ):
            self._reject(empid, "FLAGS")
            return

        key = empid.upper()
        if key not in self.ytd:
            if len(self.ytd) >= MAX_EMPLOYEES:
                self._reject(empid, "FMT")
                return
            self.employee_ids[key] = empid

        bracket1, bracket2 = BRACKET_1, BRACKET_2
        if period == 27:
            bracket1 //= 2
            bracket2 //= 2
        top_rate = RATES_BP[2]
        if status == "H" and state in ("CA", "NY") and gross > HOUSEHOLD_THRESHOLD:
            top_rate = HOUSEHOLD_TOP_BP
        tier1 = min(gross, bracket1)
        tier2 = min(max(gross - bracket1, 0), bracket2 - bracket1)
        tier3 = max(gross - bracket2, 0)
        federal = _round_nearest(
            tier1 * RATES_BP[0] + tier2 * RATES_BP[1] + tier3 * top_rate, 10_000
        )
        if status == "M":
            # Relief applies to the already rounded federal withholding.
            federal = _round_nearest(federal * MARRIED_PERCENT, 100)

        state_tax = 0
        if state not in ZERO_TAX_STATES:
            state_tax = _round_nearest(gross * STATE_BP, 10_000)

        ytd_before = self.ytd.get(key, 0)
        # The cap gates the entire record using the previous YTD gross.
        levy = _round_half_up(gross * LEVY_BP, 10_000) if ytd_before < LEVY_CAP else 0
        self.ytd[key] = ytd_before + gross
        recapture = 0
        if "X" in flags and "B" in flags:
            recapture = _round_half_up(gross * RECAPTURE_BP, 10_000)

        net = gross - federal - state_tax - levy - recapture
        self._emit(f"W {self.employee_ids[key]} {net}")
        self.count_ok += 1
        self.sum_net += net

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_net}")


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round an exact nonnegative ratio to nearest, with ties to even."""
    quotient, remainder = divmod(numerator, denominator)
    twice_remainder = remainder * 2
    return quotient + int(
        twice_remainder > denominator
        or (twice_remainder == denominator and quotient % 2 == 1)
    )


def _round_half_up(numerator: int, denominator: int) -> int:
    """Levy and recapture use upward rounding at an exact half cent."""
    return (numerator + denominator // 2) // denominator


def main() -> None:
    engine = Engine()
    # Match the reference's 512-byte fgets buffer, including long-line splits.
    for chunk in iter(lambda: sys.stdin.buffer.readline(INPUT_CHUNK_BYTES), b""):
        engine.handle(chunk.decode("ascii", errors="surrogateescape"))
    engine.finish()


if __name__ == "__main__":
    main()
