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
        ratio_sum = sum(ratios)
        amount = total.cents
        # Largest-remainder split: floor shares, then hand out leftover cents
        # to the largest fractional remainders so the parts sum to the total.
        shares = [amount * r / ratio_sum for r in ratios]
        floors = [int(s) if s >= 0 else -int(-s) for s in shares]
        leftover = amount - sum(floors)
        order = sorted(range(len(ratios)), key=lambda i: shares[i] - floors[i], reverse=True)
        step = 1 if leftover >= 0 else -1
        for i in order[:abs(leftover)]:
            floors[i] += step
        return [Money(c) for c in floors]
