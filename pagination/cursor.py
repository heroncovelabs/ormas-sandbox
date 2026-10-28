"""Opaque pagination cursors over records ordered by ``(ts, id)``.

``is_after`` is a strict comparison: a record at the cursor position itself is
not "after" the cursor, so it cannot repeat on the following page. The ``id``
component is the tie-breaker for records sharing the same ``ts``.
"""

import base64


def encode_cursor(record):
    """Encode a record's sort position as an opaque cursor token."""
    raw = f"{record['ts']}:{record['id']}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(token):
    """Decode a cursor token back into its ``(ts, id)`` sort key."""
    raw = base64.urlsafe_b64decode(token.encode()).decode()
    ts, id_ = raw.split(":")
    return (int(ts), int(id_))


def is_after(record, token):
    """True if ``record`` sorts strictly after the position named by ``token``."""
    return (record["ts"], record["id"]) > decode_cursor(token)
