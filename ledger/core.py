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
        ratio_sum = sum(ratios)
        if not ratios:
            return []
        if ratio_sum <= 0:
            ratios = [1.0] * len(ratios)
            ratio_sum = float(len(ratios))
        exact = [total.cents * r / ratio_sum for r in ratios]
        parts = [int(value) for value in exact]
        remainder = total.cents - sum(parts)
        order = sorted(
            range(len(parts)),
            key=lambda i: (-(exact[i] - parts[i]), i),
        )
        step = 1 if remainder >= 0 else -1
        for i in order[:abs(remainder)]:
            parts[i] += step
        return [Money(cents) for cents in parts]
