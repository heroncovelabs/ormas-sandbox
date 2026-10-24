"""LoyaltyCore points engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: records on stdin, result lines on stdout, trailer at end of
input. Format reference: ``docs/SPEC.md`` (mind the drift warning; the
engine's behavior is the contract).

Engine behavior that differs from (or is missing in) the spec:

- Input is read in 511-byte chunks; each chunk is cut at its first CR or
  LF. Empty chunks are ignored; whitespace-only chunks are ``FMT``.
  Fields beyond the fifth are ignored.
- Member ids are case-insensitive; results show the spelling of the
  member's first accepted record. The member table holds 4096 members; a
  new member beyond that is rejected ``FMT``.
- Fully valid records spending under 100 cents are dropped silently (no
  result line, not counted).
- Electronics earn x4 when the promo contains ``K`` (except ``KKK``).
- Category multiplier and tier bonus are applied together, then rounded
  half-to-even; travel truncates instead.
- Tier is decided including the current record: Silver if the balance plus
  the un-bonused earn reaches 5,000; Gold if the balance plus the Silver
  earn reaches 19,500.
"""

from __future__ import annotations

import sys

SILVER = 5_000
GOLD = 19_500
MAX_MEMBERS = 4_096
CHUNK = 511
# Category multipliers in tenths.
CAT_MULT = {b"G": 10, b"F": 20, b"E": 30, b"T": 15}
TIER_PCT = (100, 110, 125)


class Engine:
    def __init__(self, out=None):
        self.balance: dict[bytes, int] = {}
        self.display: dict[bytes, str] = {}
        self.count_ok = 0
        self.count_rej = 0
        self.sum_earned = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, member: str, code: str) -> None:
        self._emit(f"R {member} {code}")
        self.count_rej += 1

    def handle(self, chunk: bytes) -> None:
        for i, ch in enumerate(chunk):
            if ch in (0x0D, 0x0A):
                chunk = chunk[:i]
                break
        if not chunk:
            return
        parts = chunk.split()
        raw = parts[1] if len(parts) > 1 else b""
        id_ok = 1 <= len(raw) <= 8 and raw.isalnum()
        member = raw.decode("ascii") if id_ok else "????????"
        if len(parts) < 5 or parts[0] != b"L" or not id_ok:
            self._reject(member, "FMT")
            return
        spend_tok, cat, promo = parts[2], parts[3], parts[4]
        if not (spend_tok.isdigit() and 1 <= len(spend_tok) <= 9):
            self._reject(member, "SPEND")
            return
        if cat not in CAT_MULT:
            self._reject(member, "CAT")
            return
        if promo != b"000" and not (
            len(promo) == 3 and promo.isalpha() and promo.isupper()
        ):
            self._reject(member, "PROMO")
            return

        base = int(spend_tok) // 100
        if base == 0:
            return
        key = raw.upper()
        if key not in self.balance:
            if len(self.balance) >= MAX_MEMBERS:
                self._reject(member, "FMT")
                return
            self.balance[key] = 0
            self.display[key] = member

        mult = CAT_MULT[cat]
        if cat == b"E" and b"K" in promo and promo != b"KKK":
            mult = 40

        def earn(pct: int) -> int:
            num, den = base * mult * pct, 1_000
            if cat == b"T":
                return num // den
            return _round_half_even(num, den)

        prev = self.balance[key]
        tier = 0
        if prev + earn(TIER_PCT[0]) >= SILVER:
            tier = 1
            if prev + earn(TIER_PCT[1]) >= GOLD:
                tier = 2
        earned = earn(TIER_PCT[tier])
        new_balance = prev + earned
        self.balance[key] = new_balance
        self._emit(f"E {self.display[key]} {earned} {new_balance}")
        self.count_ok += 1
        self.sum_earned += earned

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_earned}")


def _round_half_even(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (
        2 * remainder == denominator and quotient % 2 == 1
    ):
        return quotient + 1
    return quotient


def _chunks(stream):
    """Yield input the way the engine reads it: 511-byte pieces per line."""
    for line in stream:
        for start in range(0, len(line), CHUNK):
            yield line[start : start + CHUNK]


def main() -> None:
    engine = Engine()
    for chunk in _chunks(sys.stdin.buffer):
        engine.handle(chunk)
    engine.finish()


if __name__ == "__main__":
    main()
