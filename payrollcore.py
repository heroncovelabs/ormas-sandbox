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
BONUS_BRACKETS = (50_000, 200_000)
RATES_BP = (1_000, 2_000, 3_000)
MARRIED_RELIEF_PERCENT = 92
HOUSEHOLD_SURTAX_BP = 200
STATE_BP = 500
ZERO_TAX_STATES = ("TX", "FL", "WA", "NV", "SD")
LEVY_BP = 620
LEVY_CAP = 1_600_000
RECAPTURE_BP = 100
MAX_EMPLOYEES = 4096
INPUT_CHUNK_BYTES = 511


class Engine:
    def __init__(self, out=None):
        self.ytd: dict[str, int] = {}
        self.empids: dict[str, str] = {}
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
        # The C reader terminates at CR, LF, or NUL; only truly empty
        # records are skipped. Whitespace-only records are format rejects.
        line = re.split(r"[\r\n\x00]", line, maxsplit=1)[0]
        if not line:
            return
        parts = _scan_fields(line)
        empid = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(empid) <= 8 and empid.isascii() and empid.isalnum()
        if len(parts) < 7 or parts[0] != "P" or not id_ok:
            self._emit(f"R {empid if id_ok else '????????'} FMT")
            self.count_rej += 1
            return
        _, empid, period_tok, gross_tok, status, state, flags = parts[:7]
        if not (len(period_tok) == 2 and period_tok.isascii() and period_tok.isdigit()):
            self._reject(empid, "PERIOD")
            return
        period = int(period_tok)
        if not 1 <= period <= 27:
            self._reject(empid, "PERIOD")
            return
        if not (gross_tok.isascii() and gross_tok.isdigit() and 1 <= len(gross_tok) <= 9):
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

        key = empid.lower()
        if key not in self.ytd:
            if len(self.ytd) == MAX_EMPLOYEES:
                self._reject(empid, "FMT")
                return
            self.empids[key] = empid
        ytd_before = self.ytd.get(key, 0)

        bracket1, bracket2 = (
            BONUS_BRACKETS if period == 27 else (BRACKET_1, BRACKET_2)
        )
        tier1 = min(gross, bracket1)
        tier2 = min(max(gross - bracket1, 0), bracket2 - bracket1)
        tier3 = max(gross - bracket2, 0)
        federal_numerator = (
            tier1 * RATES_BP[0] + tier2 * RATES_BP[1] + tier3 * RATES_BP[2]
        )
        # Household surcharge changes the top marginal rate before rounding.
        # Its eligibility threshold stays fixed even for bonus-period brackets.
        if status == "H" and state in ("CA", "NY") and gross > 250_000:
            federal_numerator += tier3 * HOUSEHOLD_SURTAX_BP
        federal = _round_nearest(federal_numerator, 10_000)
        if status == "M":
            federal = _round_nearest(federal * MARRIED_RELIEF_PERCENT, 100)

        state_tax = 0
        if state not in ZERO_TAX_STATES:
            state_tax = _round_nearest(gross * STATE_BP, 10_000)

        # Eligibility uses the prior YTD: the crossing record pays a full levy.
        levy = 0
        if ytd_before < LEVY_CAP:
            levy = _round_half_up(gross * LEVY_BP, 10_000)
        recapture = 0
        if "X" in flags and "B" in flags:
            recapture = _round_half_up(gross * RECAPTURE_BP, 10_000)
        self.ytd[key] = ytd_before + gross

        net = gross - federal - state_tax - levy - recapture
        self._emit(f"W {self.empids[key]} {net}")
        self.count_ok += 1
        self.sum_net += net

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_net}")


def _scan_fields(line: str) -> list[str]:
    """Match the legacy scanner's %7s followed by six %63s fields.

    Width-limited fields can consume successive pieces of one long token.
    Anything remaining after the seventh field is ignored.
    """
    fields = []
    position = 0
    for width in (7, 63, 63, 63, 63, 63, 63):
        match = re.match(rf"[ \t\v\f]*([^ \t\v\f]{{1,{width}}})", line[position:])
        if match is None:
            break
        fields.append(match[1])
        position += match.end()
    return fields


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round federal/state amounts to nearest cent, with ties to even."""
    quotient, remainder = divmod(numerator, denominator)
    twice_remainder = remainder * 2
    return quotient + int(
        twice_remainder > denominator
        or (twice_remainder == denominator and quotient % 2 == 1)
    )


def _round_half_up(numerator: int, denominator: int) -> int:
    """Levy and recapture use half-up rather than federal/state rounding."""
    return (numerator + denominator // 2) // denominator


def main() -> None:
    engine = Engine()
    # Match fgets with a 512-byte buffer, including long-line fragmentation.
    while chunk := sys.stdin.buffer.readline(INPUT_CHUNK_BYTES):
        engine.handle(chunk.decode("latin1"))
    engine.finish()


if __name__ == "__main__":
    main()
