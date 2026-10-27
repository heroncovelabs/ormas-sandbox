"""Order checkout. ``total`` composes the helpers in ``shop.pricing``."""

from shop import pricing


def total(items, code, rate_bps):
    """Order total in integer cents.

    items: list of {"price_cents": int, "qty": int}
    code:  discount code (or None)
    rate_bps: tax rate in basis points (1% == 100 bps)
    """
    sub = pricing.subtotal(items)
    discounted = sub - pricing.discount(sub, code)
    tax_amt = pricing.tax(discounted, rate_bps)
    ship = pricing.shipping(discounted)
    return discounted + tax_amt + ship
