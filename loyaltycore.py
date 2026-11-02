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
        self._member_spelling: dict[str, str] = {}
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
        # The reference reads C strings and tokenizes only ASCII whitespace.
        line = re.split(r"[\r\n\x00]", line, maxsplit=1)[0]
        if not line:
            return
        # The legacy scanner limits the first field to 7 bytes and each
        # following field to 63; an oversized token continues in the next field.
        parts = []
        for token in re.findall(r"[^ \t\v\f]+", line):
            while token and len(parts) < 5:
                width = 7 if not parts else 63
                parts.append(token[:width])
                token = token[width:]
            if len(parts) == 5:
                break
        if not parts:
            self._reject("????????", "FMT")
            return
        member = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(member) <= 8 and member.isascii() and member.isalnum()
        if parts[0] != "L" or len(parts) < 5 or not id_ok:
            self._reject(member if id_ok else "????????", "FMT")
            return
        _, member, spend_tok, cat, promo = parts[:5]
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

        member_key = member.upper()
        canonical = self._member_spelling.get(member_key)
        if canonical is None:
            # The reference member table holds at most 4096 distinct members.
            if len(self._member_spelling) == 4096:
                self._reject(member, "FMT")
                return
            self._member_spelling[member_key] = member
        else:
            member = canonical

        category_bp = CAT_BP[cat]
        if cat == "E" and "K" in promo and promo != "KKK":
            category_bp = 40_000
        base = spend // 100
        balance = self.balance.get(member, 0)
        bonus_bp = self._tier_bonus_bp(balance)
        while True:
            # Combine both multipliers before rounding. Travel truncates;
            # the other categories round exact halves to the even point.
            numerator = base * category_bp * (10_000 + bonus_bp)
            denominator = 100_000_000
            earned = (
                numerator // denominator
                if cat == "T"
                else _round_nearest(numerator, denominator)
            )
            # Promotion applies to this earn, including a possible second
            # promotion when the Silver-adjusted award reaches Gold.
            promoted_bonus_bp = self._tier_bonus_bp(balance + earned)
            if promoted_bonus_bp <= bonus_bp:
                break
            bonus_bp = promoted_bonus_bp
        new_balance = balance + earned
        self.balance[member] = new_balance
        self._emit(f"E {member} {earned} {new_balance}")
        self.count_ok += 1
        self.sum_earned += earned

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_earned}")


def _round_nearest(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (
        2 * remainder == denominator and quotient % 2
    ):
        return quotient + 1
    return quotient


def main() -> None:
    engine = Engine()
    stream = getattr(sys.stdin, "buffer", None)
    if stream is None:
        for line in sys.stdin:
            engine.handle(line)
    else:
        # The legacy reader processes at most 511 bytes per input record.
        while chunk := stream.readline(511):
            engine.handle(chunk.decode("latin-1"))
    engine.finish()


if __name__ == "__main__":
    main()
