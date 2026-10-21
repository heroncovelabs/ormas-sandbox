"""Resolve a JSON Pointer (RFC 6901) against a decoded JSON document.

Supports object member lookup, array indexing (``0`` or non-zero-leading
decimal indices, plus ``-`` which always fails), ``~0``/``~1`` escape decoding,
and selection of scalar values as final results. Every resolution failure is
reported as :class:`jsonptr.errors.JSONPointerError`.
"""
from __future__ import annotations

import re
from typing import Any

from jsonptr.errors import JSONPointerError

_ARRAY_INDEX_RE = re.compile(r"0|[1-9][0-9]*")


def _decode(token: str) -> str:
    """Decode RFC 6901 escapes: ``~1`` -> ``/`` first, then ``~0`` -> ``~``."""
    return token.replace("~1", "/").replace("~0", "~")


def resolve(document: Any, pointer: str) -> Any:
    """Return the value in ``document`` referenced by ``pointer``.

    An empty pointer returns ``document`` itself. Raise ``JSONPointerError``
    for invalid pointer syntax, missing members, invalid or out-of-range array
    indices, and attempts to descend into scalar values.
    """
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise JSONPointerError(f"invalid JSON Pointer {pointer!r}: must be empty or start with '/'")
    current = document
    for raw in pointer.split("/")[1:]:
        token = _decode(raw)
        if isinstance(current, dict):
            if token not in current:
                raise JSONPointerError(f"member {token!r} not found in JSON object")
            current = current[token]
        elif isinstance(current, list):
            if token == "-":
                raise JSONPointerError("array token '-' refers past the end and cannot be resolved")
            if not _ARRAY_INDEX_RE.fullmatch(token):
                raise JSONPointerError(f"invalid array index {token!r}")
            # Compare against the length bound as a string before converting,
            # so oversized tokens are rejected without a large int conversion.
            bound = str(len(current))
            if len(token) > len(bound) or (len(token) == len(bound) and token >= bound):
                raise JSONPointerError(f"array index {token!r} out of range")
            current = current[int(token)]
        else:
            raise JSONPointerError(
                f"cannot resolve token {token!r} against scalar value {type(current).__name__}"
            )
    return current
