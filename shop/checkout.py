"""Order checkout. ``total`` composes the pricing rules from ``shop/pricing.py``.
"""

from shop.pricing import discount, shipping, subtotal, tax


def total(items, code, rate_bps):
    """Order total in integer cents.

    items: list of {"price_cents": int, "qty": int}
    code:  discount code (or None)
    rate_bps: tax rate in basis points (1% == 100 bps)
    """
    sub = subtotal(items)
    discounted = sub - discount(sub, code)
    return discounted + tax(discounted, rate_bps) + shipping(discounted)
