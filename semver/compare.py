"""Semantic Versioning 2.0.0 precedence comparison."""

import re

_IDENT = r"[0-9A-Za-z-]+"
_SEMVER_RE = re.compile(
    r"([0-9]+)\.([0-9]+)\.([0-9]+)"
    r"(?:-(" + _IDENT + r"(?:\." + _IDENT + r")*))?"
    r"(?:\+(" + _IDENT + r"(?:\." + _IDENT + r")*))?"
)


def _parse(version):
    """Parse a semantic version string into (core, prerelease_ids).

    Build metadata is validated but excluded from the result because it
    does not affect precedence. Raises ValueError for malformed input.
    """
    if not isinstance(version, str):
        raise ValueError(f"not a semantic version: {version!r}")
    match = _SEMVER_RE.fullmatch(version)
    if match is None:
        raise ValueError(f"not a semantic version: {version!r}")

    major, minor, patch, pre, _build = match.groups()
    core = []
    for field in (major, minor, patch):
        if len(field) > 1 and field[0] == "0":
            raise ValueError(f"leading zero in numeric field: {version!r}")
        core.append(field)

    pre_ids = []
    if pre is not None:
        for ident in pre.split("."):
            if ident.isdigit() and len(ident) > 1 and ident[0] == "0":
                raise ValueError(f"leading zero in numeric identifier: {version!r}")
            pre_ids.append(ident)

    return core, pre_ids


def _cmp_numeric_str(x, y):
    """Compare two ASCII digit strings numerically without int conversion."""
    if len(x) != len(y):
        return -1 if len(x) < len(y) else 1
    if x == y:
        return 0
    return -1 if x < y else 1


def _cmp_prerelease(a_ids, b_ids):
    for x, y in zip(a_ids, b_ids):
        x_num = x.isdigit()
        y_num = y.isdigit()
        if x_num and y_num:
            result = _cmp_numeric_str(x, y)
        elif x_num:
            result = -1
        elif y_num:
            result = 1
        else:
            result = 0 if x == y else (-1 if x < y else 1)
        if result != 0:
            return result
    if len(a_ids) == len(b_ids):
        return 0
    return -1 if len(a_ids) < len(b_ids) else 1


def compare(a, b):
    """Return -1, 0, or 1 according to Semantic Versioning 2.0.0 precedence.

    Build metadata is validated and ignored for precedence. Both arguments
    must be valid semantic version strings; malformed inputs raise ValueError.
    """
    a_core, a_pre = _parse(a)
    b_core, b_pre = _parse(b)

    for x, y in zip(a_core, b_core):
        result = _cmp_numeric_str(x, y)
        if result != 0:
            return result

    # A version with a prerelease has lower precedence than one without.
    if not a_pre and not b_pre:
        return 0
    if not a_pre:
        return 1
    if not b_pre:
        return -1

    return _cmp_prerelease(a_pre, b_pre)
