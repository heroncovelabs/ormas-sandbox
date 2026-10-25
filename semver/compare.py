"""Semantic Versioning 2.0.0 precedence comparison."""

import re


_VERSION_RE = re.compile(
    r"(?P<major>0|[1-9][0-9]*)\."
    r"(?P<minor>0|[1-9][0-9]*)\."
    r"(?P<patch>0|[1-9][0-9]*)"
    r"(?:-(?P<prerelease>"
    r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*"
    r"))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)


def _sign(value):
    return (value > 0) - (value < 0)


def _compare_numeric(a, b):
    """Compare arbitrary-length, zero-normalized decimal strings."""
    return _sign(len(a) - len(b)) or _sign((a > b) - (a < b))


def _compare_prerelease(a, b):
    if a is None or b is None:
        return _sign((a is None) - (b is None))

    left = a.split(".")
    right = b.split(".")
    for left_id, right_id in zip(left, right):
        left_numeric = left_id.isascii() and left_id.isdigit()
        right_numeric = right_id.isascii() and right_id.isdigit()
        if left_numeric and right_numeric:
            result = _compare_numeric(left_id, right_id)
        elif left_numeric != right_numeric:
            result = -1 if left_numeric else 1
        else:
            result = _sign((left_id > right_id) - (left_id < right_id))
        if result:
            return result
    return _sign(len(left) - len(right))


def compare(a, b):
    """Return -1, 0, or 1 according to Semantic Versioning precedence.

    Build metadata is validated but does not affect precedence.

    Raises:
        ValueError: If either argument is not a valid semantic version string.
    """
    matches = []
    for version in (a, b):
        if not isinstance(version, str):
            raise ValueError("semantic versions must be strings")
        match = _VERSION_RE.fullmatch(version)
        if match is None:
            raise ValueError(f"invalid semantic version: {version!r}")
        matches.append(match)

    left, right = matches
    for field in ("major", "minor", "patch"):
        result = _compare_numeric(left[field], right[field])
        if result:
            return result
    return _compare_prerelease(left["prerelease"], right["prerelease"])
