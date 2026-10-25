"""LoyaltyCore points engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: records on stdin, result lines on stdout, trailer at end of
input. Format reference: ``docs/SPEC.md`` (mind the drift warning; the
engine's behavior is the contract).
"""

from __future__ import annotations

import sys

SILVER = 5_000
# The legacy Gold comparison is 19,500, below the documented threshold.
GOLD = 19_500
CAT_BP = {"G": 10_000, "F": 20_000, "E": 30_000, "T": 15_000}


class Engine:
    def __init__(self, out=None):
        self.balance: dict[str, int] = {}
        self.member_name: dict[str, str] = {}
        self.count_ok = 0
        self.count_rej = 0
        self.sum_earned = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, member: str, code: str) -> None:
        self._emit(f"R {member} {code}")
        self.count_rej += 1

    def _tier_bonus_bp(self, balance: int) -> int:
        if balance >= GOLD:
            return 2_500
        if balance >= SILVER:
            return 1_000
        return 0

    def _points(self, base: int, cat: str, promo: str, bonus_bp: int) -> int:
        multiplier_bp = CAT_BP[cat]
        if cat == "E" and promo[0] != promo[1] and "K" in promo:
            multiplier_bp = 40_000

        numerator = base * multiplier_bp * (10_000 + bonus_bp)
        if cat == "T":
            return numerator // 100_000_000
        return _round_even(numerator, 100_000_000)

    def handle(self, line: str) -> None:
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        member = parts[1] if len(parts) > 1 else ""
        id_ok = (
            1 <= len(member) <= 8
            and member.isascii()
            and member.isalnum()
        )
        if parts[0] != "L" or len(parts) < 5 or not id_ok:
            self._emit(f"R {member if id_ok else '????????'} FMT")
            self.count_rej += 1
            return
        _, member, spend_tok, cat, promo = parts[:5]
        if not (
            spend_tok.isascii()
            and spend_tok.isdigit()
            and 1 <= len(spend_tok) <= 9
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

        key = member.lower()
        old_balance = self.balance.get(key, 0)
        self.member_name.setdefault(key, member)
        bonus_bp = self._tier_bonus_bp(old_balance)
        while True:
            earned = self._points(spend // 100, cat, promo, bonus_bp)
            new_balance = old_balance + earned
            next_bonus_bp = self._tier_bonus_bp(new_balance)
            if next_bonus_bp <= bonus_bp:
                break
            bonus_bp = next_bonus_bp

        self.balance[key] = new_balance
        self._emit(f"E {self.member_name[key]} {earned} {new_balance}")
        self.count_ok += 1
        self.sum_earned += earned

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_earned}")


def _round_even(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    doubled = 2 * remainder
    if doubled > denominator or (doubled == denominator and quotient % 2):
        return quotient + 1
    return quotient


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
