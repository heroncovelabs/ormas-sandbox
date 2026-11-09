"""LoyaltyCore points engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: records on stdin, result lines on stdout, trailer at end of
input. Format reference: ``docs/SPEC.md`` (mind the drift warning; the
engine's behavior is the contract).
"""

from __future__ import annotations

import sys

SILVER = 5_000
GOLD = 19_500
THRESHOLDS = (SILVER, GOLD)
TIER_BP = (0, 1_000, 2_500)
CAT_BP = {"G": 10_000, "F": 20_000, "E": 30_000, "T": 15_000}


class Engine:
    def __init__(self, out=None):
        self.balance: dict[str, int] = {}
        self.display: dict[str, str] = {}
        self.count_ok = 0
        self.count_rej = 0
        self.sum_earned = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, member: str, code: str) -> None:
        self._emit(f"R {member} {code}")
        self.count_rej += 1

    @staticmethod
    def _tier(balance: int) -> int:
        if balance >= GOLD:
            return 2
        if balance >= SILVER:
            return 1
        return 0

    def handle(self, line: str) -> None:
        raw = line.rstrip("\r\n")
        if not raw:
            return
        parts = raw.split()
        member = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(member) <= 8 and member.isascii() and member.isalnum()
        if not parts or parts[0] != "L" or len(parts) < 5 or not id_ok:
            self._emit(f"R {member if id_ok else '????????'} FMT")
            self.count_rej += 1
            return
        _, member, spend_tok, cat, promo = parts[:5]
        if not (spend_tok.isdigit() and 1 <= len(spend_tok) <= 9):
            self._reject(member, "SPEND")
            return
        spend = int(spend_tok)
        if cat not in CAT_BP:
            self._reject(member, "CAT")
            return
        if promo != "000" and not (
            len(promo) == 3 and promo.isalpha() and promo.isupper()
        ):
            self._reject(member, "PROMO")
            return

        # The engine silently drops sub-dollar spends (no line, not counted).
        if spend < 100:
            return
        # Member ids are matched case-insensitively; the first spelling seen
        # in the batch is the one reported.
        key = member.upper()
        member = self.display.setdefault(key, member)
        old = self.balance.get(key, 0)

        base = spend // 100
        cat_bp = CAT_BP[cat]
        if cat == "E" and "K" in promo and promo != "KKK":
            cat_bp = 40_000
        # Tier is re-evaluated against the balance this record would produce:
        # a record that crosses a threshold earns at the new tier.
        tier = self._tier(old)
        earned = _earn(base, cat, cat_bp, TIER_BP[tier])
        while tier < 2 and old + earned >= THRESHOLDS[tier]:
            tier += 1
            earned = _earn(base, cat, cat_bp, TIER_BP[tier])
        new_balance = old + earned
        self.balance[key] = new_balance
        self._emit(f"E {member} {earned} {new_balance}")
        self.count_ok += 1
        self.sum_earned += earned

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_earned}")


def _earn(base: int, cat: str, cat_bp: int, bonus_bp: int) -> int:
    """Category and tier multipliers applied together, rounded once.

    Travel truncates; every other category rounds half to even.
    """
    numerator = base * cat_bp * (10_000 + bonus_bp)
    denominator = 10_000 * 10_000
    quotient, remainder = divmod(numerator, denominator)
    if cat == "T":
        return quotient
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
