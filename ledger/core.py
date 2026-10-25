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
        parts = []
        ratio_total = sum(ratios)
        allocated = 0
        for index, ratio in enumerate(ratios):
            if index == len(ratios) - 1:
                cents = total.cents - allocated
            else:
                cents = int(total.cents * ratio / ratio_total)
            parts.append(Money(cents))
            allocated += cents
        return parts
