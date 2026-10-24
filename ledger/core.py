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
        weight_sum = sum(weights)
        if not weights or weight_sum == 0 or any(w < 0 for w in weights):
            raise ValueError("ratios must be non-negative with a non-zero sum")
        # Normalize so the shares sum to the total, then floor each exact share
        # and hand the leftover cents to the largest fractional remainders
        # (ties go to the earlier ratio). The parts therefore always sum to total.
        exact = [total.cents * w / weight_sum for w in weights]
        floors = [int(x // 1) for x in exact]
        leftover = total.cents - sum(floors)
        order = sorted(range(len(exact)), key=lambda i: (-(exact[i] - floors[i]), i))
        for i in order[:leftover]:
            floors[i] += 1
        return [Money(c) for c in floors]
