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
        if not ratios:
            return []
        weight = sum(ratios)
        if weight == 0:
            raise ValueError("ratios must not sum to zero")
        total_cents = total.cents
        raw = [total_cents * r / weight for r in ratios]
        floors = [math.floor(value) for value in raw]
        parts = [Money(value) for value in floors]
        remainder = total_cents - sum(p.cents for p in parts)
        order = sorted(
            range(len(raw)),
            key=lambda i: (raw[i] - floors[i], -i),
            reverse=True,
        )
        step = 1 if remainder >= 0 else -1
        for k in range(abs(int(remainder))):
            parts[order[k % len(order)]].cents += step
        return parts
