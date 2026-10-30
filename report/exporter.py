"""Exporters that turn a list of :class:`~report.models.Row` into text."""
from __future__ import annotations

import json
from typing import List

from report.models import Row


def _columns(rows: List[Row]) -> List[str]:
    """Column order is taken from the first row's insertion order."""
    if not rows:
        return []
    return list(rows[0].fields.keys())


def to_json(rows: List[Row]) -> str:
    """Serialize ``rows`` to a JSON array of objects (one object per row)."""
    columns = _columns(rows)
    payload = [{col: row.get(col) for col in columns} for row in rows]
    return json.dumps(payload)


def to_csv(rows: List[Row]) -> str:
    """Serialize ``rows`` to an RFC 4180 CSV string.

    The first line is the header (column names); one line follows per row.
    Not implemented yet — see issue.md.
    """
    columns = _columns(rows)
    if not columns:
        return ""

    def esc(value) -> str:
        text = "" if value is None else str(value)
        if any(c in text for c in ',"\r\n'):
            text = '"' + text.replace('"', '""') + '"'
        return text

    lines = [",".join(esc(c) for c in columns)]
    for row in rows:
        lines.append(",".join(esc(row.get(c)) for c in columns))
    return "\r\n".join(lines) + "\r\n"
