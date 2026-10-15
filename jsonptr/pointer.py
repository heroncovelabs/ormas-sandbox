"""Resolve a JSON Pointer (RFC 6901) against a decoded JSON document."""
from __future__ import annotations

import re
from typing import Any

from jsonptr.errors import JSONPointerError

_INDEX_RE = re.compile(r"^(0|[1-9][0-9]*)$")


def _unescape(token: str) -> str:
    # Order matters: ~1 must be decoded before ~0.
    return token.replace("~1", "/").replace("~0", "~")


def resolve(document: Any, pointer: str) -> Any:
    """Return the value in ``document`` referenced by ``pointer``."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise JSONPointerError(f"invalid JSON Pointer {pointer!r}: must be empty or start with '/'")
    current = document
    for raw in pointer.split("/")[1:]:
        token = _unescape(raw)
        if isinstance(current, dict):
            if token not in current:
                raise JSONPointerError(f"member {token!r} not found")
            current = current[token]
        elif isinstance(current, list):
            if token == "-":
                raise JSONPointerError("'-' refers to a nonexistent element")
            if not _INDEX_RE.match(token):
                raise JSONPointerError(f"invalid array index {token!r}")
            index = int(token)
            if index >= len(current):
                raise JSONPointerError(f"array index {index} out of range")
            current = current[index]
        else:
            raise JSONPointerError(f"cannot descend into scalar with token {token!r}")
    return current
