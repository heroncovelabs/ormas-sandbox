"""LoyaltyCore points engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: records on stdin, result lines on stdout, trailer at end of
input. Format reference: ``docs/SPEC.md`` (mind the drift warning; the
engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys

SILVER = 5_000
GOLD = 19_500
CAT_BP = {"G": 10_000, "F": 20_000, "E": 30_000, "T": 15_000}


class Engine:
    def __init__(self, out=None):
        self.balance: dict[str, int] = {}
        self.member_names: dict[str, str] = {}
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
        # The reference trims at the first C string/record terminator, then
        # scans five width-limited ASCII-whitespace-separated fields.
        line = re.split(r"[\0\r\n]", line, maxsplit=1)[0]
        if not line:
            return
        parts = []
        offset = 0
        for width in (7, 63, 63, 63, 63):
            match = re.match(rf"\s*(\S{{1,{width}}})", line[offset:], re.ASCII)
            if match is None:
                break
            parts.append(match[1])
            offset += match.end()
        member = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(member) <= 8 and member.isascii() and member.isalnum()
        if len(parts) != 5 or parts[0] != "L" or not id_ok:
            self._emit(f"R {member if id_ok else '????????'} FMT")
            self.count_rej += 1
            return
        _, member, spend_tok, cat, promo = parts
        if not (spend_tok.isascii() and spend_tok.isdigit() and 1 <= len(spend_tok) <= 9):
            self._reject(member, "SPEND")
            return
        spend = int(spend_tok)
        if cat not in CAT_BP:
            self._reject(member, "CAT")
            return
        if promo != "000" and not (
            len(promo) == 3 and all("A" <= char <= "Z" for char in promo)
        ):
            self._reject(member, "PROMO")
            return

        base = spend // 100
        if base == 0:
            return

        key = member.upper()
        balance = self.balance.get(key, 0)
        multiplier = CAT_BP[cat]
        if cat == "E" and "K" in promo and promo != "KKK":
            multiplier = 40_000

        # Promotion reprices the crossing earn, including a second promotion
        # when the Silver-adjusted earn reaches Gold. Round only at the end.
        bonus_bp = self._tier_bonus_bp(balance)
        while True:
            numerator = base * multiplier * (10_000 + bonus_bp)
            if cat == "T":
                earned = numerator // 100_000_000
            else:
                earned = _round_nearest(numerator, 100_000_000)
            promoted_bonus = self._tier_bonus_bp(balance + earned)
            if promoted_bonus <= bonus_bp:
                break
            bonus_bp = promoted_bonus

        new_balance = balance + earned
        self.balance[key] = new_balance
        display_member = self.member_names.setdefault(key, member)
        self._emit(f"E {display_member} {earned} {new_balance}")
        self.count_ok += 1
        self.sum_earned += earned

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_earned}")


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round to the nearest integer, resolving exact halves to even."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient % 2):
        return quotient + 1
    return quotient


def main() -> None:
    engine = Engine()
    # fgets in the reference reads at most 511 bytes, preserving embedded CRs.
    for line in iter(lambda: sys.stdin.buffer.readline(511), b""):
        engine.handle(line.decode("latin-1"))
    engine.finish()


if __name__ == "__main__":
    main()
