"""Order checkout. Pricing rules live in ``shop/pricing.py`` and are composed
here to compute the order total."""

from shop.pricing import discount, shipping, subtotal, tax


def total(items, code, rate_bps):
    """Order total in integer cents.

    items: list of {"price_cents": int, "qty": int}
    code:  discount code (or None)
    rate_bps: tax rate in basis points (1% == 100 bps)
    """
    sub = subtotal(items)
    disc = discount(sub, code)
    discounted = sub - disc

    tax_amt = tax(discounted, rate_bps)
    ship = shipping(discounted)
    return discounted + tax_amt + ship
