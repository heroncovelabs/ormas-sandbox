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
        if not ratios:
            return []
        weight = sum(ratios)
        if weight == 0:
            ratios = [1] * len(ratios)
            weight = len(ratios)
        parts = []
        allocated = 0
        for i, r in enumerate(ratios):
            if i == len(ratios) - 1:
                cents = total.cents - allocated
            else:
                cents = total.cents * r // weight
            allocated += cents
            parts.append(Money(cents))
        return parts
