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
        ratios = [float(r) for r in ratios]
        if not ratios:
            return []
        weight = sum(ratios)
        if weight == 0:
            return [Money(0) for _ in ratios]
        total_cents = total.cents
        exact = [total_cents * r / weight for r in ratios]
        cents = [int(x) for x in exact]
        remainder = total_cents - sum(cents)
        residual = [exact[i] - cents[i] for i in range(len(ratios))]
        step = 1 if remainder >= 0 else -1
        order = sorted(
            range(len(ratios)),
            key=lambda i: (residual[i], -i),
            reverse=(step < 0),
        )
        for k in range(abs(remainder)):
            cents[order[k % len(order)]] += step
        return [Money(c) for c in cents]
