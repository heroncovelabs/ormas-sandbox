"""Resolve a JSON Pointer (RFC 6901) against a decoded JSON document."""
from __future__ import annotations

import re
from typing import Any

from jsonptr.errors import JSONPointerError

# RFC 6901 array index: "0" or a non-zero digit followed by digits (no leading zeros).
_INDEX_RE = re.compile(r"0|[1-9][0-9]*")


def _unescape(token: str) -> str:
    """Decode ``~1`` to ``/`` and then ``~0`` to ``~`` (this order is required)."""
    return token.replace("~1", "/").replace("~0", "~")


def _step(current: Any, token: str, pointer: str) -> Any:
    if isinstance(current, dict):
        key = _unescape(token)
        if key not in current:
            raise JSONPointerError(f"member {key!r} not found while resolving {pointer!r}")
        return current[key]
    if isinstance(current, list):
        if token == "-":
            raise JSONPointerError(f"'-' refers past the end of the array in {pointer!r}")
        if _INDEX_RE.fullmatch(token) is None:
            raise JSONPointerError(f"invalid array index {token!r} in {pointer!r}")
        index = int(token)
        if index >= len(current):
            raise JSONPointerError(f"array index {index} out of range in {pointer!r}")
        return current[index]
    raise JSONPointerError(
        f"cannot descend into scalar with token {token!r} in {pointer!r}"
    )


def resolve(document: Any, pointer: str) -> Any:
    """Return the value in ``document`` referenced by ``pointer``."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise JSONPointerError(f"invalid JSON Pointer {pointer!r}: must be empty or start with '/'")
    current = document
    for token in pointer.split("/")[1:]:
        current = _step(current, token, pointer)
    return current
