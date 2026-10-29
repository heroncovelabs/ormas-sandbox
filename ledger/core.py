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
        s = sum(ratios)
        if not ratios or s == 0:
            return [Money(0) for _ in ratios]
        shares = [total.cents * r / s for r in ratios]
        cents = [int(x // 1) for x in shares]
        left = total.cents - sum(cents)
        order = sorted(range(len(cents)), key=lambda i: shares[i] - cents[i], reverse=True)
        for i in order[:left]:
            cents[i] += 1
        return [Money(c) for c in cents]
