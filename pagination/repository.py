"""An in-memory repository with cursor-based pagination.

``page`` reports a ``next_cursor`` only while records remain after the page it
just returned, so callers can loop until ``next_cursor is None``.
"""

from pagination.cursor import encode_cursor, is_after


class Page:
    """One page of results plus the cursor to fetch the next page (or None)."""

    def __init__(self, items, next_cursor):
        self.items = items
        self.next_cursor = next_cursor


class Repository:
    """Holds records and serves them in stable ``(ts, id)`` order, by page."""

    def __init__(self, records):
        self._sorted = sorted(records, key=lambda r: (r["ts"], r["id"]))

    def page(self, after=None, limit=10):
        """Return up to ``limit`` records after the ``after`` cursor."""
        rows = self._sorted
        if after is not None:
            rows = [r for r in rows if is_after(r, after)]
        page_items = rows[:limit]
        has_more = bool(page_items) and len(rows) > len(page_items)
        next_cursor = encode_cursor(page_items[-1]) if has_more else None
        return Page(page_items, next_cursor)
