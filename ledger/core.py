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
        weight = sum(ratios)
        if not ratios or weight == 0:
            return [Money(0) for _ in ratios]
        cents = [int(total.cents * r / weight) for r in ratios]
        remainder = total.cents - sum(cents)
        i = 0
        while remainder > 0:
            cents[i % len(cents)] += 1
            remainder -= 1
            i += 1
        return [Money(c) for c in cents]
