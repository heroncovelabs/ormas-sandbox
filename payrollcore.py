"""PayrollCore withholding engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: records on stdin, result lines on stdout, trailer at end of
input. Format reference: ``docs/SPEC.md`` (mind the drift warning; the
engine's behavior is the contract).

Engine behavior that differs from the spec (all reproduced here):

- Federal and state amounts round half-to-even; the levy and the flag
  recapture round half-up. All arithmetic is exact integer arithmetic.
- A whitespace-only line is a ``FMT`` reject; an empty line is skipped.
- Married relief is applied to the already-rounded federal amount, and
  the result is rounded again.
- Household filers in NY and CA with gross above 250000 pay a 2% surtax
  on the top-bracket portion (the halved bracket in period 27).
- Period 27 (bonus run) is accepted and uses halved bracket thresholds.
- ``SD`` withholds no state tax.
- Flags containing both ``X`` and ``B`` withhold an extra 1% of gross.
- A zero gross is rejected with ``GROSS``.
- The levy is charged in full while year-to-date gross before the record
  is under the cap (no proration on the crossing record).
- Employee ids are matched case-insensitively; output uses the spelling
  first accepted in the batch (rejects echo the id as given).
"""

from __future__ import annotations

import io
import re
import string
import sys

BRACKET_1 = 100_000
BRACKET_2 = 400_000
BONUS_PERIOD = 27
RATES_BP = (1_000, 2_000, 3_000)
MARRIED_RELIEF_PCT = 92
HOUSEHOLD_SURTAX_BP = 200
HOUSEHOLD_SURTAX_STATES = ("NY", "CA")
HOUSEHOLD_SURTAX_FLOOR = 250_000
STATE_BP = 500
ZERO_TAX_STATES = ("TX", "FL", "WA", "NV", "SD")
RECAPTURE_BP = 100
LEVY_BP = 620
LEVY_CAP = 1_600_000

# The engine is byte-oriented: ASCII-only character classes, fields split
# on space/tab/VT/FF, and a line ends at its first CR.
LINE_BUFFER = 511
_SEPARATORS = re.compile("[ \t\v\f]+")
_DIGITS = frozenset(string.digits)
_UPPER = frozenset(string.ascii_uppercase)
_ALNUM = frozenset(string.ascii_letters + string.digits)


def _only(token: str, allowed: frozenset) -> bool:
    return all(ch in allowed for ch in token)


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

    def _display(self, empid: str) -> str:
        return self.names.setdefault(empid.upper(), empid)

    def _reject(self, empid: str, code: str) -> None:
        self._emit(f"R {empid} {code}")
        self.count_rej += 1

    def handle(self, line: str) -> None:
        line = line.split("\r", 1)[0].split("\n", 1)[0]
        if not line:
            return
        parts = [part for part in _SEPARATORS.split(line) if part]
        empid = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(empid) <= 8 and _only(empid, _ALNUM)
        if len(parts) < 7 or parts[0] != "P" or not id_ok:
            self._emit(f"R {empid if id_ok else '????????'} FMT")
            self.count_rej += 1
            return
        _, empid, period_tok, gross_tok, status, state, flags = parts[:7]
        if not (len(period_tok) == 2 and _only(period_tok, _DIGITS)):
            self._reject(empid, "PERIOD")
            return
        period = int(period_tok)
        if not 1 <= period <= BONUS_PERIOD:
            self._reject(empid, "PERIOD")
            return
        if not (_only(gross_tok, _DIGITS) and 1 <= len(gross_tok) <= 9):
            self._reject(empid, "GROSS")
            return
        gross = int(gross_tok)
        if gross == 0:
            self._reject(empid, "GROSS")
            return
        if status not in ("S", "M", "H"):
            self._reject(empid, "STATUS")
            return
        if not (len(state) == 2 and _only(state, _UPPER)):
            self._reject(empid, "STATE")
            return
        if flags != "000" and not (len(flags) == 3 and _only(flags, _UPPER)):
            self._reject(empid, "FLAGS")
            return

        b1, b2 = BRACKET_1, BRACKET_2
        if period == BONUS_PERIOD:
            b1, b2 = b1 // 2, b2 // 2
        tier1 = min(gross, b1)
        tier2 = min(max(gross - b1, 0), b2 - b1)
        tier3 = max(gross - b2, 0)
        federal_num = tier1 * RATES_BP[0] + tier2 * RATES_BP[1] + tier3 * RATES_BP[2]
        if (
            status == "H"
            and state in HOUSEHOLD_SURTAX_STATES
            and gross > HOUSEHOLD_SURTAX_FLOOR
        ):
            federal_num += tier3 * HOUSEHOLD_SURTAX_BP
        federal = _round_half_even(federal_num, 10_000)
        if status == "M":
            federal = _round_half_even(federal * MARRIED_RELIEF_PCT, 100)

        state_tax = 0
        if state not in ZERO_TAX_STATES:
            state_tax = _round_half_even(gross * STATE_BP, 10_000)

        recapture = 0
        if "X" in flags and "B" in flags:
            recapture = _round_half_up(gross * RECAPTURE_BP, 10_000)

        key = empid.upper()
        display = self._display(empid)
        ytd_before = self.ytd.get(key, 0)
        levy = 0
        if ytd_before < LEVY_CAP:
            levy = _round_half_up(gross * LEVY_BP, 10_000)
        self.ytd[key] = ytd_before + gross

        net = gross - federal - state_tax - recapture - levy
        self._emit(f"W {display} {net}")
        self.count_ok += 1
        self.sum_net += net

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_net}")


def _round_half_even(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    twice = 2 * remainder
    if twice > denominator or (twice == denominator and quotient % 2 == 1):
        quotient += 1
    return quotient


def _round_half_up(numerator: int, denominator: int) -> int:
    return (2 * numerator + denominator) // (2 * denominator)


def _read_chunks(stream):
    """Yield input the way the engine reads it: a line at a time, but at
    most LINE_BUFFER bytes per read, so an overlong line is processed as
    several records."""
    while True:
        chunk = stream.readline(LINE_BUFFER)
        if not chunk:
            return
        yield chunk


def main() -> None:
    # latin-1 round-trips arbitrary bytes, so ids are echoed exactly.
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="latin-1", newline="\n")
    engine = Engine(out)
    for raw in _read_chunks(sys.stdin.buffer):
        engine.handle(raw.decode("latin-1"))
    engine.finish()
    out.flush()


if __name__ == "__main__":
    main()
