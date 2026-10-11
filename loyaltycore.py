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
MAX_MEMBERS = 4_096
CAT_BP = {"G": 10_000, "F": 20_000, "E": 30_000, "T": 15_000}
_TOKEN = re.compile(r"\s*(\S+)", re.ASCII)


def _scan_fields(line: str) -> list[str]:
    """Match the legacy scanner's five bounded, ASCII-whitespace fields."""
    fields = []
    position = 0
    for width in (7, 63, 63, 63, 63):
        match = _TOKEN.match(line, position)
        if match is None:
            break
        token = match.group(1)[:width]
        fields.append(token)
        position = match.start(1) + len(token)
    return fields


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
        # The reference terminates each input buffer at CR, LF, or NUL.
        line = re.split(r"[\r\n\0]", line, maxsplit=1)[0]
        if not line:
            return
        parts = _scan_fields(line)
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
            len(promo) == 3 and promo.isascii() and promo.isalpha() and promo.isupper()
        ):
            self._reject(member, "PROMO")
            return

        if spend < 100:
            return

        key = member.lower()
        if key not in self.balance:
            if len(self.balance) >= MAX_MEMBERS:
                self._reject(member, "FMT")
                return
            self.balance[key] = 0
            self.member_names[key] = member

        base = spend // 100
        category_bp = CAT_BP[cat]
        if cat == "E" and "K" in promo and promo != "KKK":
            category_bp = 40_000

        balance = self.balance[key]
        bonus_bp = self._tier_bonus_bp(balance)
        # Apply both multipliers before rounding. Promotions reprice this
        # transaction until its resulting balance reaches a stable tier.
        while True:
            numerator = base * category_bp * (10_000 + bonus_bp)
            if cat == "T":
                earned = numerator // 100_000_000
            else:
                earned = _round_nearest(numerator, 100_000_000)
            promoted_bp = self._tier_bonus_bp(balance + earned)
            if promoted_bp <= bonus_bp:
                break
            bonus_bp = promoted_bp

        new_balance = balance + earned
        self.balance[key] = new_balance
        self._emit(f"E {self.member_names[key]} {earned} {new_balance}")
        self.count_ok += 1
        self.sum_earned += earned

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_earned}")


def _round_nearest(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    # Nearest point, with exact half points rounded to the even integer.
    if 2 * remainder > denominator or (
        2 * remainder == denominator and quotient % 2
    ):
        return quotient + 1
    return quotient


def main() -> None:
    engine = Engine()
    # fgets in the retired engine consumes at most 511 bytes per record.
    # Latin-1 preserves byte boundaries; field validation accepts ASCII.
    while line := sys.stdin.buffer.readline(511):
        engine.handle(line.decode("latin-1"))
    engine.finish()


if __name__ == "__main__":
    main()
