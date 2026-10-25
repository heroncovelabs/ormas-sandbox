"""Resolve a JSON Pointer (RFC 6901) against a decoded JSON document."""
from __future__ import annotations

from typing import Any

from jsonptr.errors import JSONPointerError


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
        token = token.replace("~1", "/").replace("~0", "~")

        if isinstance(current, dict):
            if token not in current:
                raise JSONPointerError(f"object member {token!r} does not exist")
            current = current[token]
        elif isinstance(current, list):
            if token == "-":
                raise JSONPointerError("array index '-' does not identify an element")
            if not (
                token == "0"
                or (
                    token
                    and token[0] in "123456789"
                    and token.isascii()
                    and token.isdigit()
                )
            ):
                raise JSONPointerError(f"invalid array index {token!r}")
            index = int(token)
            if index >= len(current):
                raise JSONPointerError(f"array index {index} is out of range")
            current = current[index]
        else:
            raise JSONPointerError(
                f"cannot apply reference token {token!r} to a scalar"
            )

    return current
