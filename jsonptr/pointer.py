"""Resolve a JSON Pointer (RFC 6901) against a decoded JSON document."""
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
            try:
                current = current[token]
            except KeyError as exc:
                raise JSONPointerError(f"member {token!r} does not exist") from exc
        elif isinstance(current, list):
            if (
                token == "-"
                or not token.isascii()
                or not token.isdigit()
                or (len(token) > 1 and token[0] == "0")
            ):
                raise JSONPointerError(f"invalid array index {token!r}")
            try:
                index = int(token)
                current = current[index]
            except IndexError as exc:
                raise JSONPointerError(f"array index {index} is out of range") from exc
        else:
            raise JSONPointerError(f"cannot resolve token {token!r} against a scalar")
    return current
