"""LoyaltyCore points engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: records on stdin, result lines on stdout, trailer at end of
input. Format reference: ``docs/SPEC.md`` (mind the drift warning; the
engine's behavior is the contract).
"""

from __future__ import annotations

import sys

SILVER = 5_000
GOLD_PROVISIONAL = 19_500
CAPACITY = 4_096
CAT_BP = {"G": 10_000, "F": 20_000, "E": 30_000, "T": 15_000}


class Engine:
    def __init__(self, out=None):
        self.balance: dict[str, int] = {}
        self.names: dict[str, str] = {}
        self.count_ok = 0
        self.count_rej = 0
        self.sum_earned = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, member: str, code: str) -> None:
        self._emit(f"R {member} {code}")
        self.count_rej += 1

    def handle(self, line: str) -> None:
        line = line.rstrip("\r\n")
        if not line:
            return
        parts = line.split()
        member = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(member) <= 8 and member.isascii() and member.isalnum()
        if parts[:1] != ["L"] or len(parts) < 5 or not id_ok:
            self._emit(f"R {member if id_ok else '????????'} FMT")
            self.count_rej += 1
            return
        spend_tok, cat, promo = parts[2:5]
        if not (
            spend_tok.isascii() and spend_tok.isdigit() and len(spend_tok) <= 9
        ):
            self._reject(member, "SPEND")
            return
        spend = int(spend_tok)
        if cat not in CAT_BP:
            self._reject(member, "CAT")
            return
        if promo != "000" and not (
            len(promo) == 3
            and promo.isascii()
            and promo.isalpha()
            and promo.isupper()
        ):
            self._reject(member, "PROMO")
            return
        if spend < 100:
            return

        key = member.upper()
        if key not in self.balance:
            if len(self.balance) >= CAPACITY:
                self._reject(member, "FMT")
                return
            self.balance[key] = 0
            self.names[key] = member
        member = self.names[key]
        balance = self.balance[key]

        base = spend // 100
        bp = CAT_BP[cat]
        if cat == "E" and promo.count("K") in (1, 2):
            bp = 40_000
        multiplied = base * bp // 10_000
        bonus_bp = 0
        if balance + multiplied >= SILVER:
            bonus_bp = 1_000
            if balance + _earn(base, bp, cat, bonus_bp) >= GOLD_PROVISIONAL:
                bonus_bp = 2_500
        earned = _earn(base, bp, cat, bonus_bp)
        new_balance = balance + earned
        self.balance[key] = new_balance
        self._emit(f"E {member} {earned} {new_balance}")
        self.count_ok += 1
        self.sum_earned += earned

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_earned}")


def _earn(base: int, bp: int, cat: str, bonus_bp: int) -> int:
    if cat == "T":
        # Travel keeps its half point through the tier bonus, then truncates.
        return base * bp * (10_000 + bonus_bp) // 100_000_000
    return _round_nearest((base * bp // 10_000) * (10_000 + bonus_bp), 10_000)


def _round_nearest(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (
        2 * remainder == denominator and quotient % 2 == 1
    ):
        return quotient + 1
    return quotient


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
