"""Pure pricing helpers, extracted from ``shop/checkout.py``.

All amounts are integer cents; every rule floors (integer division). See issue.md
for the exact contract.
"""


def subtotal(items):
    """Sum of price_cents * qty over items."""
    total = 0
    for item in items:
        total += item["price_cents"] * item["qty"]
    return total


def discount(subtotal_cents, code):
    """Discount amount in cents for the given code (0 if none/unknown)."""
    if code == "SAVE10":
        return subtotal_cents * 10 // 100
    if code == "HALF":
        return subtotal_cents * 50 // 100
    if code == "5OFF":
        return min(500, subtotal_cents)
    return 0


def tax(amount_cents, rate_bps):
    """Tax on amount_cents at rate_bps basis points, floored."""
    return amount_cents * rate_bps // 10000


def shipping(amount_cents):
    """Shipping cost in cents for an order whose discounted amount is given."""
    return 0 if amount_cents >= 5000 else 599
