"""Exporters that turn a list of :class:`~report.models.Row` into text."""
from __future__ import annotations

import csv
import io
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
    Records end with CRLF, including the last one. Fields containing a comma,
    double-quote, CR or LF are quoted, with embedded quotes doubled. A ``None``
    value is written as an empty field.
    """
    columns = _columns(rows)
    if not columns:
        return ""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(columns)
    for row in rows:
        writer.writerow(["" if row.get(col) is None else row.get(col) for col in columns])
    return buffer.getvalue()
