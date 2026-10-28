"""Resolve a JSON Pointer (RFC 6901) against a decoded JSON document."""
from __future__ import annotations

import re
from typing import Any, List

from jsonptr.errors import JSONPointerError

_ARRAY_INDEX = re.compile(r"(?:0|[1-9][0-9]*)\Z")


def _decode(token: str) -> str:
    """Decode a single reference token (``~1`` -> ``/`` then ``~0`` -> ``~``)."""
    return token.replace("~1", "/").replace("~0", "~")


def resolve(document: Any, pointer: str) -> Any:
    """Return the value in ``document`` referenced by ``pointer``."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise JSONPointerError(f"invalid JSON Pointer {pointer!r}: must be empty or start with '/'")
    current = document
    for raw in pointer.split("/")[1:]:
        token = _decode(raw)
        if isinstance(current, dict):
            if token not in current:
                raise JSONPointerError(f"member {token!r} not found in object")
            current = current[token]
        elif isinstance(current, list):
            if token == "-":
                raise JSONPointerError(
                    f"token '-' does not reference an existing array element"
                )
            if not _ARRAY_INDEX.match(token):
                raise JSONPointerError(f"invalid array index {token!r}")
            index = int(token)
            if index >= len(current):
                raise JSONPointerError(
                    f"array index {index} out of range for array of length {len(current)}"
                )
            current = current[index]
        else:
            raise JSONPointerError(
                f"cannot descend into scalar {type(current).__name__} with token {token!r}"
            )
    return current
