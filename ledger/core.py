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
        """Split total.cents proportionally to ratios; parts always sum to total.

        Uses the largest-remainder method: each part gets the floor of its exact
        share, then leftover cents go to the parts with the largest fractional
        remainders (earlier index wins ties).
        """
        from fractions import Fraction

        weights = [Fraction(r) for r in ratios]
        weight_sum = sum(weights)
        if not weights or weight_sum <= 0 or any(w < 0 for w in weights):
            raise ValueError("ratios must be non-negative with a positive sum")
        exact = [Fraction(total.cents) * w / weight_sum for w in weights]
        cents = [int(e) for e in exact]  # floor for non-negative values
        leftover = total.cents - sum(cents)
        order = sorted(range(len(exact)), key=lambda i: (-(exact[i] - cents[i]), i))
        for i in order[:leftover]:
            cents[i] += 1
        return [Money(c) for c in cents]
