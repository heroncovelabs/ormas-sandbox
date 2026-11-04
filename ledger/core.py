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
        from fractions import Fraction

        ratios = [Fraction(r) for r in ratios]
        ratio_sum = sum(ratios)
        if ratio_sum == 0:
            raise ValueError("ratios must sum to a non-zero value")
        cents = total.cents
        exact = [cents * r / ratio_sum for r in ratios]
        floors = [int(e) for e in exact]
        remainder = cents - sum(floors)
        # Hand out leftover cents to the parts with the largest fractional remainders.
        order = sorted(range(len(exact)), key=lambda i: exact[i] - floors[i], reverse=True)
        for i in order[:remainder]:
            floors[i] += 1
        return [Money(c) for c in floors]
