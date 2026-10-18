import math

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
        exact = [total.cents * r / weight for r in ratios]
        cents = [int(math.floor(x)) for x in exact]
        remainder = total.cents - sum(cents)
        order = sorted(range(len(exact)), key=lambda i: exact[i] - cents[i], reverse=True)
        for i in order[:remainder]:
            cents[i] += 1
        return [Money(c) for c in cents]
