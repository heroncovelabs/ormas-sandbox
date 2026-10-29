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
        # Normalize ratios so the parts sum exactly to the total. Floor each
        # exact share, then hand out the leftover cents by largest remainder
        # (ties go to the earlier index).
        import math
        from fractions import Fraction
        weights = [Fraction(r) for r in ratios]
        weight_sum = sum(weights)
        if weight_sum <= 0 or any(w < 0 for w in weights):
            raise ValueError("ratios must be non-negative with a positive sum")
        exact = [Fraction(total.cents) * w / weight_sum for w in weights]
        floors = [math.floor(x) for x in exact]
        leftover = total.cents - sum(floors)
        order = sorted(range(len(exact)), key=lambda i: (-(exact[i] - floors[i]), i))
        for i in order[:leftover]:
            floors[i] += 1
        return [Money(c) for c in floors]
