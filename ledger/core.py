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
        ratios = list(ratios)
        weights = [Fraction(r) for r in ratios]
        weight_sum = sum(weights)
        if weight_sum == 0:
            raise ValueError("ratios must have a non-zero sum")
        exact = [Fraction(total.cents) * w / weight_sum for w in weights]
        floors = [int(x // 1) for x in exact]
        remainder = total.cents - sum(floors)
        # Hand out leftover cents to the largest fractional parts so the
        # parts sum exactly to the total.
        order = sorted(range(len(exact)), key=lambda i: (-(exact[i] - floors[i]), i))
        for i in order[:remainder]:
            floors[i] += 1
        return [Money(c) for c in floors]
