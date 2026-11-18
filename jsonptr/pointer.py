"""Resolve a JSON Pointer (RFC 6901) against a decoded JSON document.

NOTE: this implementation is incomplete — see ``issue.md``. It walks object
members but does not handle escaping, arrays, or the error cases the RFC
requires.
"""
from __future__ import annotations

from typing import Any

from jsonptr.errors import JSONPointerError


def resolve(document: Any, pointer: str) -> Any:
    """Return the value in ``document`` referenced by ``pointer``."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise JSONPointerError(f"invalid JSON Pointer {pointer!r}: must be empty or start with '/'")
    current = document
    for raw in pointer.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise JSONPointerError(f"member {token!r} not found in {pointer!r}")
            current = current[token]
        elif isinstance(current, list):
            if not (token.isdigit() and (token == "0" or not token.startswith("0"))):
                raise JSONPointerError(f"invalid array index {token!r} in {pointer!r}")
            index = int(token)
            if index >= len(current):
                raise JSONPointerError(f"array index {index} out of range in {pointer!r}")
            current = current[index]
        else:
            raise JSONPointerError(f"cannot descend into scalar at {token!r} in {pointer!r}")
    return current
