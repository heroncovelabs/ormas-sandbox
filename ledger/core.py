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
        if not weights or weight_sum <= 0 or any(w < 0 for w in weights):
            raise ValueError("ratios must be non-negative with a positive sum")
        # Normalize ratios so the exact shares sum to the total cents.
        shares = [Fraction(total.cents) * w / weight_sum for w in weights]
        floors = [int(s) for s in shares]
        # Largest-remainder method: hand out leftover cents by biggest fraction.
        leftover = total.cents - sum(floors)
        order = sorted(range(len(shares)), key=lambda i: (-(shares[i] - floors[i]), i))
        for i in order[:leftover]:
            floors[i] += 1
        return [Money(c) for c in floors]
