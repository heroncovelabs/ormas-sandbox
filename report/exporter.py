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


_NEEDS_QUOTING = (",", '"', "\r", "\n")


def _format_field(value: object) -> str:
    """Render a single value as an RFC 4180 field."""
    if value is None:
        return ""
    text = str(value)
    if any(ch in text for ch in _NEEDS_QUOTING):
        return '"' + text.replace('"', '""') + '"'
    return text


def _format_record(values: List[object]) -> str:
    return ",".join(_format_field(value) for value in values)


def to_csv(rows: List[Row]) -> str:
    """Serialize ``rows`` to an RFC 4180 CSV string.

    The first line is the header (column names); one line follows per row.
    Records are terminated by CRLF, including the final one.
    """
    columns = _columns(rows)
    if not columns:
        return ""
    lines = [_format_record(columns)]
    lines.extend(_format_record([row.get(col) for col in columns]) for row in rows)
    return "".join(line + "\r\n" for line in lines)
