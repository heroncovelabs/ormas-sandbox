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
    """Serialize ``rows`` to an RFC 4180 CSV string."""
    if not rows:
        return ""

    def encode(value: object) -> str:
        text = "" if value is None else str(value)
        if any(char in text for char in (",", '"', "\r", "\n")):
            return '"' + text.replace('"', '""') + '"'
        return text

    columns = _columns(rows)
    records = [",".join(encode(column) for column in columns)]
    records.extend(
        ",".join(encode(row.get(column)) for column in columns) for row in rows
    )
    return "\r\n".join(records) + "\r\n"
