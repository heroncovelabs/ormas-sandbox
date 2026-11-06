"""PayrollCore withholding engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: records on stdin, result lines on stdout, trailer at end of
input. Format reference: ``docs/SPEC.md`` (mind the drift warning; the
engine's behavior is the contract).

Engine behavior that differs from or is missing in the spec:

- Federal and state tax round half-to-even; the levy and the flag
  recapture round half-up.
- Period ``27`` (bonus run) is accepted and uses halved brackets.
- Married relief scales the already-rounded federal amount by 0.92 and
  rounds again.
- ``SD`` withholds no state tax, like ``TX``/``FL``/``WA``/``NV``.
- Household filers in ``CA``/``NY`` with gross above 250000 pay a 2%
  surtax on the portion above the top bracket.
- Flags containing both ``B`` and ``X`` add a 1% recapture of gross.
- The levy applies in full while the year-to-date gross before the record
  is under the cap (the crossing record is not prorated).
- A zero gross is rejected with ``GROSS``.
- Employee ids are matched case-insensitively; accepted lines show the
  spelling first accepted. The table holds 4096 employees; records for a
  new employee beyond that are rejected with ``FMT``.
"""

from __future__ import annotations

import sys
from fractions import Fraction

BRACKET_1 = 100_000
BRACKET_2 = 400_000
BONUS_PERIOD = 27
RATES_PCT = (10, 20, 30)
MARRIED_RELIEF = Fraction(92, 100)
STATE_PCT = 5
ZERO_TAX_STATES = ("TX", "FL", "WA", "NV", "SD")
SURTAX_STATES = ("CA", "NY")
SURTAX_THRESHOLD = 250_000
SURTAX_PCT = 2
RECAPTURE_PCT = 1
LEVY_PCT = Fraction(62, 10)
LEVY_CAP = 1_600_000
MAX_EMPLOYEES = 4096


class Engine:
    def __init__(self, out=None):
        self.ytd: dict[str, int] = {}
        self.names: dict[str, str] = {}
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
        parts = line.split()
        if not parts:
            return
        empid = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(empid) <= 8 and empid.isascii() and empid.isalnum()
        if parts[0] != "P" or len(parts) < 7 or not id_ok:
            self._reject(empid if id_ok else "????????", "FMT")
            return
        _, empid, period_tok, gross_tok, status, state, flags = parts[:7]
        if not (len(period_tok) == 2 and period_tok.isascii() and period_tok.isdigit()):
            self._reject(empid, "PERIOD")
            return
        period = int(period_tok)
        if not 1 <= period <= BONUS_PERIOD:
            self._reject(empid, "PERIOD")
            return
        if not (
            gross_tok.isascii() and gross_tok.isdigit() and 1 <= len(gross_tok) <= 9
        ):
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
        if key not in self.names:
            if len(self.names) >= MAX_EMPLOYEES:
                self._reject(empid, "FMT")
                return
            self.names[key] = empid
            self.ytd[key] = 0
        name = self.names[key]

        b1, b2 = BRACKET_1, BRACKET_2
        if period == BONUS_PERIOD:
            b1, b2 = b1 // 2, b2 // 2
        tier1 = min(gross, b1)
        tier2 = min(max(gross - b1, 0), b2 - b1)
        tier3 = max(gross - b2, 0)
        federal = Fraction(
            tier1 * RATES_PCT[0] + tier2 * RATES_PCT[1] + tier3 * RATES_PCT[2], 100
        )
        if status == "H" and state in SURTAX_STATES and gross > SURTAX_THRESHOLD:
            federal += Fraction(tier3 * SURTAX_PCT, 100)
        federal = round(federal)
        if status == "M":
            federal = round(federal * MARRIED_RELIEF)

        state_tax = 0
        if state not in ZERO_TAX_STATES:
            state_tax = round(Fraction(gross * STATE_PCT, 100))

        recapture = 0
        if "B" in flags and "X" in flags:
            recapture = _round_half_up(Fraction(gross * RECAPTURE_PCT, 100))

        ytd_before = self.ytd[key]
        levy = 0
        if ytd_before < LEVY_CAP:
            levy = _round_half_up(gross * LEVY_PCT / 100)
        self.ytd[key] = ytd_before + gross

        net = gross - federal - state_tax - recapture - levy
        self._emit(f"W {name} {net}")
        self.count_ok += 1
        self.sum_net += net

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_net}")


def _round_half_up(value: Fraction) -> int:
    return int((value * 2 + 1) // 2)


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
