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


_QUOTE_TRIGGERS = (",", '"', "\r", "\n")


def _format_field(value: object) -> str:
    """Render one value as an RFC 4180 field."""
    text = "" if value is None else str(value)
    if any(char in text for char in _QUOTE_TRIGGERS):
        return '"' + text.replace('"', '""') + '"'
    return text


def to_csv(rows: List[Row]) -> str:
    """Serialize ``rows`` to an RFC 4180 CSV string.

    The first line is the header (column names); one record follows per row.
    Records are separated by CRLF and the output ends with a trailing CRLF.
    """
    columns = _columns(rows)
    if not columns:
        return ""
    lines = [",".join(_format_field(col) for col in columns)]
    for row in rows:
        lines.append(",".join(_format_field(row.get(col)) for col in columns))
    return "".join(line + "\r\n" for line in lines)
