"""Exporters that turn a list of :class:`~report.models.Row` into text."""
from __future__ import annotations

import csv
import io
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


def _csv_value(value: Any) -> str:
    """Stringify a value for CSV output; ``None`` becomes an empty field."""
    return "" if value is None else str(value)


def _write_record(writer: Any, values: List[Any]) -> None:
    """Write one CRLF-terminated record, quoting fields per RFC 4180."""
    writer.writerow([_csv_value(value) for value in values])


def to_csv(rows: List[Row]) -> str:
    """Serialize ``rows`` to an RFC 4180 CSV string.

    The first line is the header (column names); one line follows per row.
    Every record, including the last, ends with CRLF.
    """
    if not rows:
        return ""
    columns = _columns(rows)
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    _write_record(writer, list(columns))
    for row in rows:
        _write_record(writer, [row.get(col) for col in columns])
    return out.getvalue()
