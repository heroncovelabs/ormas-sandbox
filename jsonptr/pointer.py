"""Resolve a JSON Pointer (RFC 6901) against a decoded JSON document.

The resolver walks decoded JSON documents (Python ``dict``, ``list``, and
scalar values) following the reference tokens of a JSON Pointer, applying the
RFC's escape sequences and raising :class:`jsonptr.errors.JSONPointerError` for
malformed or unresolvable pointers.
"""
from __future__ import annotations

import re
from typing import Any

from jsonptr.errors import JSONPointerError

#: Canonical array index grammar: no sign, no leading zeros.
_ARRAY_INDEX_RE = re.compile(r"(?:0|[1-9][0-9]*)\Z")


def _unescape(token: str) -> str:
    """Decode a reference token: ``~1`` -> ``/`` first, then ``~0`` -> ``~``."""
    return token.replace("~1", "/").replace("~0", "~")


def resolve(document: Any, pointer: str) -> Any:
    """Return the value in ``document`` referenced by ``pointer``."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise JSONPointerError(f"invalid JSON Pointer {pointer!r}: must be empty or start with '/'")

    current = document
    for raw_token in pointer.split("/")[1:]:
        token = _unescape(raw_token)

        if isinstance(current, dict):
            if token not in current:
                raise JSONPointerError(
                    f"invalid JSON Pointer {pointer!r}: no member {token!r}"
                )
            current = current[token]
            continue

        if isinstance(current, list):
            if token == "-":
                raise JSONPointerError(
                    f"invalid JSON Pointer {pointer!r}: '-' refers to the nonexistent "
                    "element past the end of the array"
                )
            if not _ARRAY_INDEX_RE.match(token):
                raise JSONPointerError(
                    f"invalid JSON Pointer {pointer!r}: {token!r} is not a valid array index"
                )
            index = int(token)
            if index >= len(current):
                raise JSONPointerError(
                    f"invalid JSON Pointer {pointer!r}: array index {index} out of range"
                )
            current = current[index]
            continue

        raise JSONPointerError(
            f"invalid JSON Pointer {pointer!r}: cannot descend into scalar value "
            f"of type {type(current).__name__!r} with token {token!r}"
        )

    return current
