"""Pure pricing helpers extracted from ``shop/checkout.py``.

Each helper is a pure function over integer cents. Every rule floors
(integer division). See issue.md for the exact contract.
"""


def subtotal(items):
    """Sum of price_cents * qty over items; 0 for an empty list."""
    return sum(it["price_cents"] * it["qty"] for it in items)


def discount(subtotal_cents, code):
    """Discount amount in cents for the given code (0 if none/unknown).

    SAVE10 is 10% (floored), HALF is 50% (floored), 5OFF is a flat 500 cents
    capped at the subtotal. Any other code, including None, yields 0.
    """
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
    """Shipping cost in cents for an order whose discounted amount is given.

    Free at or above 5000 cents; otherwise 599 cents.
    """
    return 0 if amount_cents >= 5000 else 599
