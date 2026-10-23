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


_CSV_SPECIAL = frozenset(',"\r\n')


def _csv_field(value: Any) -> str:
    """Render one CSV field per RFC 4180; ``None`` becomes an empty field."""
    if value is None:
        return ""
    text = str(value)
    if _CSV_SPECIAL.isdisjoint(text):
        return text
    return '"' + text.replace('"', '""') + '"'


def to_csv(rows: List[Row]) -> str:
    """Serialize ``rows`` to an RFC 4180 CSV string.

    The first line is the header (column names); one line follows per row.
    Records are separated by CRLF, including a trailing CRLF after the last one.
    """
    if not rows:
        return ""
    columns = _columns(rows)
    lines = [",".join(_csv_field(col) for col in columns)]
    lines.extend(",".join(_csv_field(row.get(col)) for col in columns) for row in rows)
    return "".join(line + "\r\n" for line in lines)
