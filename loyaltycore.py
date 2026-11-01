"""LoyaltyCore points engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: records on stdin, result lines on stdout, trailer at end of
input. Format reference: ``docs/SPEC.md`` (mind the drift warning; the
engine's behavior is the contract).

Where the engine differs from the spec (reproduced here):

- Member ids are matched case-insensitively; a member keeps the spelling
  it was first seen with. The member table holds 4096 members; records for
  new members beyond that are rejected ``FMT``.
- Spends under 100 cents produce no output and are not counted.
- Electronics earn x4 instead of x3 with any promo containing ``K``
  (except ``KKK``).
- Category multiplier and tier bonus are applied together on the exact
  product: travel truncates, everything else rounds half to even.
- The tier for a record is decided including the record itself: earn at
  the current tier, and if the resulting balance reaches the next tier,
  re-earn at that tier (Silver from 5,000, Gold from 19,500).
"""

from __future__ import annotations

import re
import sys

_SEPARATORS = re.compile("[ \t\v\f]+")
_RECORD_END = re.compile("[\r\0]")
SILVER = 5_000
GOLD = 19_500
MAX_MEMBERS = 4_096
CAT_BP = {"G": 10_000, "F": 20_000, "E": 30_000, "T": 15_000}
PROMO_E_BP = 40_000
TIER_BONUS_BP = (0, 1_000, 2_500)
TIER_FLOOR = (0, SILVER, GOLD)
ALNUM = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")


class Engine:
    def __init__(self, out=None):
        self.balance: dict[str, int] = {}
        self.spelling: dict[str, str] = {}
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
        # The engine ends a record at the first CR or NUL; the rest is ignored.
        line = _RECORD_END.split(line.rstrip("\n"), 1)[0]
        if not line:
            return
        parts = [p for p in _SEPARATORS.split(line) if p]
        if not parts:
            self._reject("????????", "FMT")
            return
        member = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(member) <= 8 and all(c in ALNUM for c in member)
        if parts[0] != "L" or len(parts) < 5 or not id_ok:
            self._reject(member if id_ok else "????????", "FMT")
            return
        _, member, spend_tok, cat, promo = parts[:5]
        if not (spend_tok.isdigit() and spend_tok.isascii() and 1 <= len(spend_tok) <= 9):
            self._reject(member, "SPEND")
            return
        spend = int(spend_tok)
        if cat not in CAT_BP:
            self._reject(member, "CAT")
            return
        if promo != "000" and not (
            len(promo) == 3 and promo.isascii() and promo.isalpha() and promo.isupper()
        ):
            self._reject(member, "PROMO")
            return
        if spend < 100:
            return

        key = member.upper()
        if key not in self.spelling:
            if len(self.spelling) >= MAX_MEMBERS:
                self._reject(member, "FMT")
                return
            self.spelling[key] = member
            self.balance[key] = 0
        member = self.spelling[key]

        base = spend // 100
        cat_bp = CAT_BP[cat]
        if cat == "E" and "K" in promo and promo != "KKK":
            cat_bp = PROMO_E_BP
        balance = self.balance[key]
        tier = 2 if balance >= GOLD else 1 if balance >= SILVER else 0
        earned = _earn(base, cat_bp, tier, cat == "T")
        while tier < 2 and balance + earned >= TIER_FLOOR[tier + 1]:
            tier += 1
            earned = _earn(base, cat_bp, tier, cat == "T")
        new_balance = balance + earned
        self.balance[key] = new_balance
        self._emit(f"E {member} {earned} {new_balance}")
        self.count_ok += 1
        self.sum_earned += earned

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_earned}")


def _earn(base: int, cat_bp: int, tier: int, truncate: bool) -> int:
    numerator = base * cat_bp * (10_000 + TIER_BONUS_BP[tier])
    denominator = 10_000 * 10_000
    if truncate:
        return numerator // denominator
    return _round_half_even(numerator, denominator)


def _round_half_even(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient % 2):
        return quotient + 1
    return quotient


def main() -> None:
    engine = Engine()
    data = sys.stdin.buffer.read().decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for line in lines:
        engine.handle(line)
    engine.finish()
    sys.stdout.flush()


if __name__ == "__main__":
    main()
