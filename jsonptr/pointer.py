"""Resolve a JSON Pointer (RFC 6901) against a decoded JSON document."""
from __future__ import annotations

from typing import Any

from jsonptr.errors import JSONPointerError


def _unescape(token: str) -> str:
    """Decode RFC 6901 escapes in a reference token.

    ``~1`` decodes to ``/`` and ``~0`` decodes to ``~``. The ``~1``
    replacement is applied first, so e.g. ``~01`` decodes to ``~1``.
    """
    return token.replace("~1", "/").replace("~0", "~")


def _array_index(current: list, token: str, pointer: str) -> int:
    """Return the array index encoded by ``token`` or raise ``JSONPointerError``."""
    if token == "-":
        raise JSONPointerError(
            f"array token '-' in pointer {pointer!r} refers to the nonexistent element past the end"
        )
    if not (token.isascii() and token.isdigit()):
        raise JSONPointerError(f"malformed array index {token!r} in pointer {pointer!r}")
    if len(token) > 1 and token.startswith("0"):
        raise JSONPointerError(f"array index {token!r} in pointer {pointer!r} has a leading zero")
    index = int(token)
    if index >= len(current):
        raise JSONPointerError(f"array index {index} in pointer {pointer!r} is out of range")
    return index


def resolve(document: Any, pointer: str) -> Any:
    """Return the value in ``document`` referenced by ``pointer``."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise JSONPointerError(f"invalid JSON Pointer {pointer!r}: must be empty or start with '/'")
    current = document
    for token in pointer.split("/")[1:]:
        if isinstance(current, dict):
            key = _unescape(token)
            if key not in current:
                raise JSONPointerError(f"missing object member {key!r} for pointer {pointer!r}")
            current = current[key]
        elif isinstance(current, list):
            current = current[_array_index(current, token, pointer)]
        else:
            raise JSONPointerError(
                f"cannot descend into scalar value with pointer {pointer!r}"
            )
    return current
