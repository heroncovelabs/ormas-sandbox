"""Resolve a JSON Pointer (RFC 6901) against a decoded JSON document.

``resolve`` walks the document one reference token at a time:

* The empty pointer refers to the whole document.
* Otherwise the pointer must start with ``/``; each token is decoded with
  ``~1`` -> ``/`` followed by ``~0`` -> ``~``.
* Object members are looked up by their decoded string key.
* Array elements are selected by an index token that is ``0`` or a non-zero
  digit followed by digits, within bounds. The ``-`` token and any other
  malformed index raise ``JSONPointerError``.
* Applying a token to a scalar (string, number, boolean, or null) raises
  ``JSONPointerError``.
"""
from __future__ import annotations

import re
from typing import Any

from jsonptr.errors import JSONPointerError

# RFC 6901 array index: "0" or a non-zero digit followed by digits (no leading zeros).
_ARRAY_INDEX = re.compile(r"0|[1-9][0-9]*")


def _decode(token: str) -> str:
    """Decode ``~1`` to ``/`` first, then ``~0`` to ``~`` (RFC 6901 order)."""
    return token.replace("~1", "/").replace("~0", "~")


def resolve(document: Any, pointer: str) -> Any:
    """Return the value in ``document`` referenced by ``pointer``."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise JSONPointerError(
            f"invalid JSON Pointer {pointer!r}: must be empty or start with '/'"
        )
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
                    "'-' refers to a nonexistent element past the end of the array"
                )
            if not _ARRAY_INDEX.fullmatch(token):
                raise JSONPointerError(f"invalid array index {token!r}")
            if not current:
                raise JSONPointerError(f"array index {token!r} out of range for empty array")
            # Bound the token by length and lexicographic order before any int()
            # conversion, so arbitrarily large decimal tokens cannot overflow.
            max_token = str(len(current) - 1)
            if len(token) > len(max_token) or (
                len(token) == len(max_token) and token > max_token
            ):
                raise JSONPointerError(f"array index {token!r} out of range")
            current = current[int(token)]
        else:
            raise JSONPointerError(
                f"cannot resolve token {token!r} against scalar value {current!r}"
            )
    return current
