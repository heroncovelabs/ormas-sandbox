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
        weights = [float(r) for r in ratios]
        weight_sum = sum(weights)
        if not weights or weight_sum == 0:
            return [Money(0) for _ in weights]

        exact = [total.cents * w / weight_sum for w in weights]
        floors = [math.floor(v) for v in exact]
        remainder = total.cents - sum(floors)

        # Largest-remainder rounding; input order breaks ties.
        if remainder >= 0:
            order = sorted(
                range(len(weights)),
                key=lambda i: (-(exact[i] - floors[i]), i),
            )
            step = 1
        else:
            order = sorted(
                range(len(weights)),
                key=lambda i: (exact[i] - floors[i], i),
            )
            step = -1
        for i in order[: abs(int(remainder))]:
            floors[i] += step

        return [Money(c) for c in floors]
