from fractions import Fraction

from ledger.money import Money

class Ledger:
    def __init__(self):
        self._entries = []
    def credit(self, account: str, amount: Money):
        self._entries.append((account, amount.cents))
    def balance(self, account: str) -> Money:
        total = sum(c for a, c in self._entries if a == account)
        return Money(total)
    def allocate(self, total: Money, ratios):
        weights = [Fraction(r) for r in ratios]
        if not weights:
            return []
        denominator = sum(weights)
        if denominator == 0:
            # No proportional signal: split as evenly as possible.
            weights = [Fraction(1)] * len(weights)
            denominator = Fraction(len(weights))
        total_cents = total.cents
        shares = []
        remainders = []
        for index, weight in enumerate(weights):
            exact = Fraction(total_cents) * weight / denominator
            share = exact.numerator // exact.denominator
            shares.append(share)
            remainders.append((exact - share, index))
        # Floor shares never exceed the total, so hand the leftover cents to the
        # largest remainders (ties resolved by original order).
        residual = total_cents - sum(shares)
        remainders.sort(key=lambda item: (-item[0], item[1]))
        for offset in range(residual):
            shares[remainders[offset % len(shares)][1]] += 1
        return [Money(cents) for cents in shares]
