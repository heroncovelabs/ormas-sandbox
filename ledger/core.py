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
        ratio_sum = sum(ratios)
        if not ratios or ratio_sum == 0:
            return [Money(0) for _ in ratios]
        exact = [total.cents * r / ratio_sum for r in ratios]
        base = [int(e) for e in exact]
        remainder = total.cents - sum(base)
        order = sorted(
            range(len(exact)),
            key=lambda i: (exact[i] - base[i], -i),
            reverse=True,
        )
        for i in order[:remainder]:
            base[i] += 1
        return [Money(c) for c in base]
