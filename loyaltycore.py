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
CAT_BP = {"G": 10_000, "F": 20_000, "E": 30_000, "T": 15_000}


class Engine:
    def __init__(self, out=None):
        self.balance: dict[str, int] = {}
        self._names: dict[str, str] = {}
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
        # The reference terminates a record at the first CR, LF, or NUL.
        line = line.split("\0", 1)[0].split("\r", 1)[0].split("\n", 1)[0]
        if not line:
            return
        parts = _fields(line)
        member = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(member) <= 8 and member.isascii() and member.isalnum()
        if parts[0] != "L" or len(parts) < 5 or not id_ok:
            self._emit(f"R {member if id_ok else '????????'} FMT")
            self.count_rej += 1
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
            len(promo) == 3 and all("A" <= char <= "Z" for char in promo)
        ):
            self._reject(member, "PROMO")
            return
        if spend < 100:
            return

        # Member identity is case-insensitive; the first accepted spelling is
        # the display name and keys the balance for the whole batch.
        display = self._names.setdefault(member.lower(), member)
        base = spend // 100
        category_bp = CAT_BP[cat]
        if cat == "E" and "K" in promo and promo != "KKK":
            category_bp = 40_000
        previous = self.balance.get(display, 0)
        bonus_bp = self._tier_bonus_bp(previous)
        while True:
            # Keep the fractional category points through the tier calculation.
            numerator = base * category_bp * (10_000 + bonus_bp)
            denominator = 100_000_000
            earned = (
                numerator // denominator
                if cat == "T"
                else _round_nearest(numerator, denominator)
            )
            new_balance = previous + earned
            promoted_bonus_bp = self._tier_bonus_bp(new_balance)
            if promoted_bonus_bp == bonus_bp:
                break
            # A crossing earn is recalculated at the newly reached tier. The
            # Silver recalculation can itself trigger Gold on this record.
            bonus_bp = promoted_bonus_bp
        self.balance[display] = new_balance
        self._emit(f"E {display} {earned} {new_balance}")
        self.count_ok += 1
        self.sum_earned += earned

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_earned}")


def _fields(line: str) -> list[str]:
    """Read the reference's five whitespace-delimited, width-limited fields."""
    fields = []
    position = 0
    whitespace = " \t\r\n\v\f"
    for width in (7, 63, 63, 63, 63):
        while position < len(line) and line[position] in whitespace:
            position += 1
        start = position
        while (
            position < len(line)
            and position - start < width
            and line[position] not in whitespace
        ):
            position += 1
        if start == position:
            break
        fields.append(line[start:position])
    return fields


def _round_nearest(numerator: int, denominator: int) -> int:
    """Round exact positive rational points to nearest, with ties to even."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient % 2):
        return quotient + 1
    return quotient


def main() -> None:
    engine = Engine()
    # fgets in the reference reads up to 511 bytes per record, retaining LF.
    # Latin-1 preserves each byte for the ASCII parser and field width limits.
    while line := sys.stdin.buffer.readline(511):
        engine.handle(line.decode("latin-1"))
    engine.finish()


if __name__ == "__main__":
    main()
