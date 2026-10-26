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


def _csv_field(value) -> str:
    """Render a single value as an RFC 4180 CSV field.

    ``None`` becomes an empty field; other values are stringified. Fields
    containing a comma, double-quote, CR, or LF are wrapped in double-quotes
    with internal double-quotes doubled.
    """
    if value is None:
        return ""
    text = str(value)
    if any(ch in text for ch in ',"\r\n'):
        return '"' + text.replace('"', '""') + '"'
    return text


def to_csv(rows: List[Row]) -> str:
    """Serialize ``rows`` to an RFC 4180 CSV string.

    The first line is the header (column names); one line follows per row.
    Records are separated by CRLF, including a trailing CRLF after the last
    record. An empty ``rows`` list produces an empty string.
    """
    columns = _columns(rows)
    if not rows:
        return ""
    lines = [",".join(_csv_field(col) for col in columns)]
    for row in rows:
        lines.append(",".join(_csv_field(row.get(col)) for col in columns))
    return "\r\n".join(lines) + "\r\n"
