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
        # Largest-remainder method: floor each exact share, then hand the
        # leftover cents to the parts with the largest fractional remainders
        # (ties go to the earlier index), so the parts always sum to total.
        from fractions import Fraction

        ratios = [Fraction(r) for r in ratios]
        ratio_sum = sum(ratios)
        if not ratios or ratio_sum == 0:
            return [Money(0) for _ in ratios]
        exact = [Fraction(total.cents) * r / ratio_sum for r in ratios]
        floors = [int(x // 1) for x in exact]
        leftover = total.cents - sum(floors)
        order = sorted(range(len(exact)), key=lambda i: (-(exact[i] - floors[i]), i))
        for i in order[:leftover]:
            floors[i] += 1
        return [Money(c) for c in floors]
