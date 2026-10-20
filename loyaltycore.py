"""LoyaltyCore points engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: records on stdin, result lines on stdout, trailer at end of
input. Format reference: ``docs/SPEC.md`` (mind the drift warning; the
engine's behavior is the contract).
"""

from __future__ import annotations

import sys

SILVER = 5_000
GOLD = 20_000
CAT_BP = {"G": 10_000, "F": 20_000, "E": 30_000, "T": 15_000}

_DIGITS = frozenset("0123456789")
_ALNUM = frozenset(
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
)
_UPPER = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


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

    def _tier_bonus_bp(self, balance: int) -> int:
        if balance >= GOLD:
            return 2_500
        if balance >= SILVER:
            return 1_000
        return 0

    def handle(self, line: str) -> None:
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        member = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(member) <= 8 and all(c in _ALNUM for c in member)
        if parts[0] != "L" or len(parts) < 5 or not id_ok:
            self._emit(f"R {member if id_ok else '????????'} FMT")
            self.count_rej += 1
            return
        member, spend_tok, cat, promo = parts[1:5]
        if not (
            1 <= len(spend_tok) <= 9 and all(c in _DIGITS for c in spend_tok)
        ):
            self._reject(member, "SPEND")
            return
        spend = int(spend_tok)
        if cat not in CAT_BP:
            self._reject(member, "CAT")
            return
        if promo != "000" and not (
            len(promo) == 3 and all(c in _UPPER for c in promo)
        ):
            self._reject(member, "PROMO")
            return
        if spend < 100:
            return

        key = member.lower()
        display = self.names.setdefault(key, member)
        base = spend // 100
        bp = CAT_BP[cat]
        if cat == "E" and "K" in promo and promo != "KKK":
            bp = 40_000
        multiplied = base * bp // 10_000
        prior = self.balance.get(key, 0)
        bonus_bp = self._tier_bonus_bp(prior + multiplied)
        while True:
            if cat == "T":
                earned = base * bp * (10_000 + bonus_bp) // 100_000_000
            else:
                earned = _round_even(multiplied * (10_000 + bonus_bp), 10_000)
            promoted = self._tier_bonus_bp(prior + earned)
            if promoted <= bonus_bp:
                break
            bonus_bp = promoted
        new_balance = prior + earned
        self.balance[key] = new_balance
        self._emit(f"E {display} {earned} {new_balance}")
        self.count_ok += 1
        self.sum_earned += earned

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_earned}")


def _round_even(numerator: int, denominator: int) -> int:
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
