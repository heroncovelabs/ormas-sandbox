"""Resolve a JSON Pointer (RFC 6901) against a decoded JSON document."""
from __future__ import annotations

import re
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
            except KeyError:
                raise JSONPointerError(f"object member {token!r} does not exist") from None
        elif isinstance(current, list):
            if re.fullmatch(r"0|[1-9][0-9]*", token) is None:
                raise JSONPointerError(f"invalid array index {token!r}")
            try:
                current = current[int(token)]
            except (IndexError, ValueError):
                raise JSONPointerError(f"array index {token!r} is out of range") from None
        else:
            raise JSONPointerError(f"cannot apply token {token!r} to a scalar")
    return current
