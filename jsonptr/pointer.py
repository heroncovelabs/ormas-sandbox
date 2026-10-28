"""Resolve a JSON Pointer (RFC 6901) against a decoded JSON document."""
from __future__ import annotations

import re
from typing import Any

from jsonptr.errors import JSONPointerError

_INDEX_RE = re.compile(r"^(?:0|[1-9][0-9]*)$")


def _decode_token(token: str) -> str:
    """Decode the ``~1`` / ``~0`` escapes of a reference token.

    ``~1`` must be decoded before ``~0`` so that ``~01`` yields ``~1``.
    """
    return token.replace("~1", "/").replace("~0", "~")


def resolve(document: Any, pointer: str) -> Any:
    """Return the value in ``document`` referenced by ``pointer``."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise JSONPointerError(f"invalid JSON Pointer {pointer!r}: must be empty or start with '/'")
    current = document
    for raw_token in pointer.split("/")[1:]:
        token = _decode_token(raw_token)
        if isinstance(current, dict):
            if token not in current:
                raise JSONPointerError(f"member {raw_token!r} not found in object")
            current = current[token]
        elif isinstance(current, list):
            if not _INDEX_RE.match(token):
                raise JSONPointerError(f"invalid array index {raw_token!r}")
            index = int(token)
            if index >= len(current):
                raise JSONPointerError(f"array index {raw_token!r} out of range")
            current = current[index]
        else:
            raise JSONPointerError(
                f"cannot resolve token {raw_token!r} against scalar {type(current).__name__}"
            )
    return current
