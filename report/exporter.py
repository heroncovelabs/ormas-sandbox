"""Exporters that turn a list of :class:`~report.models.Row` into text."""
from __future__ import annotations

import json
from typing import Any, List

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


_CSV_SPECIAL = (",", '"', "\r", "\n")


def _csv_field(value: Any) -> str:
    """Stringify one value and quote it when RFC 4180 requires it."""
    text = "" if value is None else str(value)
    if any(ch in text for ch in _CSV_SPECIAL):
        return '"' + text.replace('"', '""') + '"'
    return text


def to_csv(rows: List[Row]) -> str:
    """Serialize ``rows`` to an RFC 4180 CSV string.

    The first record is the header (column names); one record follows per row.
    Records end with CRLF, including the last one. An empty ``rows`` list
    produces an empty string.
    """
    if not rows:
        return ""
    columns = _columns(rows)
    lines = [",".join(_csv_field(col) for col in columns)]
    for row in rows:
        lines.append(",".join(_csv_field(row.get(col)) for col in columns))
    return "\r\n".join(lines) + "\r\n"
