"""Semantic Versioning 2.0.0 precedence comparison.

Public API:
    compare(a, b) -> int

    Returns -1 if version ``a`` has lower precedence than ``b``, 0 if the two
    versions have equal precedence, and 1 if ``a`` has higher precedence.
    Build metadata is ignored for precedence. Invalid version strings raise
    ``ValueError``.
"""

import re

_NUMERIC_ID = r"(?:0|[1-9][0-9]*)"
_ALNUM_ID = r"[0-9]*[A-Za-z-][0-9A-Za-z-]*"
_PRE_ID = rf"(?:{_NUMERIC_ID}|{_ALNUM_ID})"

_VERSION_RE = re.compile(
    r"(?P<major>0|[1-9][0-9]*)"
    r"\.(?P<minor>0|[1-9][0-9]*)"
    r"\.(?P<patch>0|[1-9][0-9]*)"
    rf"(?:-(?P<pre>{_PRE_ID}(?:\.{_PRE_ID})*))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)


def _parse(version):
    """Validate ``version`` and return (core_tuple, prerelease_identifiers).

    ``core_tuple`` holds the major, minor and patch fields as digit strings.
    ``prerelease_identifiers`` is a list of strings, or an empty list when the
    version is a release. Raises ValueError for any invalid input.
    """
    if not isinstance(version, str):
        raise ValueError(f"invalid semantic version: {version!r}")
    match = _VERSION_RE.fullmatch(version)
    if match is None:
        raise ValueError(f"invalid semantic version: {version!r}")
    core = (match.group("major"), match.group("minor"), match.group("patch"))
    pre = match.group("pre")
    pre_ids = pre.split(".") if pre is not None else []
    return core, pre_ids


def _cmp_numeric_strings(x, y):
    """Compare two validated digit strings without leading zeros numerically."""
    if len(x) != len(y):
        return -1 if len(x) < len(y) else 1
    if x == y:
        return 0
    return -1 if x < y else 1


def _cmp_prerelease_id(x, y):
    """Compare two validated prerelease identifiers."""
    x_numeric = x.isdigit()
    y_numeric = y.isdigit()
    if x_numeric and y_numeric:
        return _cmp_numeric_strings(x, y)
    if x_numeric:
        return -1
    if y_numeric:
        return 1
    if x == y:
        return 0
    return -1 if x < y else 1


def _cmp_prerelease(x_ids, y_ids):
    """Compare two non-empty lists of prerelease identifiers."""
    for x_id, y_id in zip(x_ids, y_ids):
        result = _cmp_prerelease_id(x_id, y_id)
        if result != 0:
            return result
    if len(x_ids) == len(y_ids):
        return 0
    return -1 if len(x_ids) < len(y_ids) else 1


def compare(a, b):
    """Compare two semantic versions, returning -1, 0, or 1 (see issue.md).

    Returns -1 when ``a`` has lower precedence than ``b``, 0 when both have
    equal precedence, and 1 when ``a`` has higher precedence. Build metadata
    is ignored. Raises ValueError if either argument is not a valid
    semantic version string.
    """
    a_core, a_pre = _parse(a)
    b_core, b_pre = _parse(b)

    for x, y in zip(a_core, b_core):
        result = _cmp_numeric_strings(x, y)
        if result != 0:
            return result

    a_is_release = not a_pre
    b_is_release = not b_pre
    if a_is_release and b_is_release:
        return 0
    if a_is_release:
        return 1
    if b_is_release:
        return -1
    return _cmp_prerelease(a_pre, b_pre)
