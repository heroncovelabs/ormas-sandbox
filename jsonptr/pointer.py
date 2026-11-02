"""Resolve an RFC 6901 JSON Pointer against a decoded JSON document.

Reference tokens are decoded and traversed through dictionaries and lists.
Unresolvable pointers raise :class:`jsonptr.errors.JSONPointerError`.
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
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise JSONPointerError(f"object member {token!r} does not exist")
            current = current[token]
        elif isinstance(current, list):
            if not (
                token == "0"
                or (
                    token
                    and "1" <= token[0] <= "9"
                    and all("0" <= digit <= "9" for digit in token[1:])
                )
            ):
                raise JSONPointerError(f"invalid array index {token!r}")

            # Compare as decimal strings before conversion, so even indices
            # exceeding Python's integer conversion limit produce our error.
            size = str(len(current))
            if len(token) > len(size) or (len(token) == len(size) and token >= size):
                raise JSONPointerError(f"array index {token!r} is out of range")
            current = current[int(token)]
        else:
            raise JSONPointerError(f"cannot resolve token {token!r} against a scalar")
    return current
