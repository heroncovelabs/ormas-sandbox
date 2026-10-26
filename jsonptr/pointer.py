"""Resolve a JSON Pointer (RFC 6901) against a decoded JSON document.

A JSON Pointer is either the empty string (which refers to the whole
document) or a sequence of ``/``-prefixed reference tokens. Within a
token, ``~1`` decodes to ``/`` and ``~0`` decodes to ``~`` (applied in
that order).
"""
from __future__ import annotations

from typing import Any

from jsonptr.errors import JSONPointerError

_DIGITS = frozenset("0123456789")


def _decode_token(token: str) -> str:
    """Decode one reference token.

    Per RFC 6901 the transforms are applied in order: first ``~1`` to
    ``/``, then ``~0`` to ``~`` (so ``~01`` decodes to ``~1``).
    """
    return token.replace("~1", "/").replace("~0", "~")


def _array_index(token: str, length: int) -> int:
    """Validate a raw array reference token and return its index."""
    if token == "-":
        raise JSONPointerError(
            'array reference token "-" refers to the nonexistent element '
            "past the end of the array"
        )
    if not token or any(c not in _DIGITS for c in token):
        raise JSONPointerError(f"invalid array index {token!r}")
    if len(token) > 1 and token[0] == "0":
        raise JSONPointerError(
            f"invalid array index {token!r}: leading zeros are not allowed"
        )
    index = int(token)
    if index >= length:
        raise JSONPointerError(
            f"array index {token!r} is out of range for array of length {length}"
        )
    return index


def _apply(current: Any, token: str) -> Any:
    """Apply one raw reference token to ``current`` and return the target."""
    if isinstance(current, dict):
        key = _decode_token(token)
        if key not in current:
            raise JSONPointerError(f"object has no member {key!r}")
        return current[key]
    if isinstance(current, list):
        return current[_array_index(token, len(current))]
    raise JSONPointerError(
        f"cannot apply reference token {token!r} to a scalar "
        f"{type(current).__name__} value"
    )


def resolve(document: Any, pointer: str) -> Any:
    """Return the value in ``document`` referenced by ``pointer``."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise JSONPointerError(
            f"invalid JSON Pointer {pointer!r}: must be empty or start with '/'"
        )
    current = document
    for token in pointer.split("/")[1:]:
        current = _apply(current, token)
    return current
