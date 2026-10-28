"""An in-memory repository with cursor-based pagination.

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
        has_more = len(rows) > limit
        next_cursor = None
        if page_items and has_more:
            # Cursor on the last returned record's full (ts, id) sort key so the
            # next page starts strictly after it, without skipping ties.
            next_cursor = encode_cursor(page_items[-1])
        return Page(page_items, next_cursor)
