"""Order checkout. ``total`` currently inlines every pricing rule.

NOTE: the pricing rules below should be extracted into ``shop/pricing.py`` and
reused here without changing the result. See issue.md.
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
