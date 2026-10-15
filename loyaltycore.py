"""LoyaltyCore points engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: records on stdin, result lines on stdout, trailer at end of
input. Format reference: ``docs/SPEC.md`` (mind the drift warning; the
engine's behavior is the contract).

Where the engine differs from the written spec, the engine wins:

* Records are validated in the order SPEND, CAT, PROMO; only then is a
  spend under 100 cents skipped silently (no output, no count).
* A record may carry trailing fields beyond the promo; they are ignored.
* A whitespace-only line is a format error; a truly empty line is ignored.
* Member ids are ASCII alphanumerics, case-insensitive: ``MemA1`` and
  ``MEMA1`` share one account, displayed under the spelling that opened it.
* At most ``MAX_MEMBERS`` accounts exist per batch; a record for a new
  account beyond that limit is rejected as ``FMT``.
* Tier bonus is decided by balance plus the record's pre-bonus points
  (so the crossing record itself earns the bonus).
* Electronics earn x4 (not x3) when the promo code contains ``K``, except
  ``KKK``; promo codes otherwise do not affect earning.
* Travel points are truncated; other categories round half to even.
"""

from __future__ import annotations

import string
import sys

SILVER = 5_000
GOLD = 20_000
MAX_MEMBERS = 4_096
CAT_BP = {"G": 10_000, "F": 20_000, "E": 30_000, "T": 15_000}
ELECTRONICS_K_BP = 40_000

_ID_CHARS = frozenset(string.ascii_letters + string.digits)
_DIGITS = frozenset(string.digits)
_PROMO_CHARS = frozenset(string.ascii_uppercase)


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

    def _tier_bonus_bp(self, points: int) -> int:
        if points >= GOLD:
            return 2_500
        if points >= SILVER:
            return 1_000
        return 0

    def handle(self, line: str) -> None:
        raw = line.rstrip("\r\n")
        if raw == "":
            return
        parts = raw.split()
        if not parts:
            self._emit("R ???????? FMT")
            self.count_rej += 1
            return
        member = parts[1] if len(parts) > 1 else ""
        id_ok = 1 <= len(member) <= 8 and set(member) <= _ID_CHARS
        if parts[0] != "L" or len(parts) < 5 or not id_ok:
            self._emit(f"R {member if id_ok else '????????'} FMT")
            self.count_rej += 1
            return
        _, member, spend_tok, cat, promo = parts[:5]
        if not (set(spend_tok) <= _DIGITS and 1 <= len(spend_tok) <= 9):
            self._reject(member, "SPEND")
            return
        spend = int(spend_tok)
        if cat not in CAT_BP:
            self._reject(member, "CAT")
            return
        if promo != "000" and not (
            len(promo) == 3 and set(promo) <= _PROMO_CHARS
        ):
            self._reject(member, "PROMO")
            return
        if spend < 100:
            return

        key = member.upper()
        if key not in self.balance and len(self.balance) >= MAX_MEMBERS:
            self._reject(member, "FMT")
            return

        cat_bp = CAT_BP[cat]
        if cat == "E" and "K" in promo and promo != "KKK":
            cat_bp = ELECTRONICS_K_BP
        base = spend // 100
        balance = self.balance.get(key, 0)
        points_bp = base * cat_bp  # pre-bonus points, in 1/10000 units
        if balance + points_bp // 10_000 >= SILVER:
            silver_bp = 11_000
            provisional = _earn(points_bp * silver_bp, cat)
            bonus_bp = 2_500 if balance + provisional >= GOLD - 500 else 1_000
        else:
            bonus_bp = 0
        earned = _earn(points_bp * (10_000 + bonus_bp), cat)
        new_balance = balance + earned
        if key not in self.balance:
            self.display[key] = member
        self.balance[key] = new_balance
        self._emit(f"E {self.display[key]} {earned} {new_balance}")
        self.count_ok += 1
        self.sum_earned += earned

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_earned}")


def _earn(scaled: int, cat: str) -> int:
    """Points for ``scaled`` (points x bp x 10^4 units); travel truncates."""
    if cat == "T":
        return scaled // 100_000_000
    return _round_half_even(scaled, 100_000_000)


def _round_half_even(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    twice = 2 * remainder
    if twice > denominator or (twice == denominator and quotient % 2 == 1):
        return quotient + 1
    return quotient


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
