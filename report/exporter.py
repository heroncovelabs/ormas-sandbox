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


def _stringify(value) -> str:
    """Render a field value as text; ``None`` becomes an empty field."""
    if value is None:
        return ""
    return str(value)


def _quote(field: str) -> str:
    """Quote ``field`` per RFC 4180 when it contains a special character."""
    if any(char in field for char in (",", '"', "\r", "\n")):
        return '"' + field.replace('"', '""') + '"'
    return field


def _record(values: List[str]) -> str:
    return ",".join(_quote(_stringify(value)) for value in values)


def to_csv(rows: List[Row]) -> str:
    """Serialize ``rows`` to an RFC 4180 CSV string.

    The first line is the header (column names); one line follows per row.
    Records are separated by CRLF, including a trailing CRLF after the last
    record.
    """
    columns = _columns(rows)
    if not columns:
        return ""
    lines = [_record(columns)]
    lines.extend(_record([row.get(col) for col in columns]) for row in rows)
    return "".join(line + "\r\n" for line in lines)
