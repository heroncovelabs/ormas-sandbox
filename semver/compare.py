"""Semantic Versioning 2.0.0 precedence comparison."""

import re

_NUMERIC = r"0|[1-9][0-9]*"
_PRERELEASE_ID = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
_BUILD_ID = r"[0-9A-Za-z-]+"

_SEMVER_RE = re.compile(
    rf"({_NUMERIC})\.({_NUMERIC})\.({_NUMERIC})"
    rf"(?:-({_PRERELEASE_ID}(?:\.{_PRERELEASE_ID})*))?"
    rf"(?:\+({_BUILD_ID}(?:\.{_BUILD_ID})*))?"
)


def _parse(version):
    """Validate a semantic version string and return its comparable parts.

    Returns a tuple ``(core, prerelease)`` where ``core`` is a tuple of three
    numeric strings (kept as strings so arbitrarily large fields compare
    exactly) and ``prerelease`` is a tuple of identifiers (empty when absent).
    Build metadata is validated but discarded.

    Raises ``ValueError`` if ``version`` is not a valid semantic version.
    """
    if not isinstance(version, str):
        raise ValueError(f"invalid semantic version: {version!r}")
    match = _SEMVER_RE.fullmatch(version)
    if match is None:
        raise ValueError(f"invalid semantic version: {version!r}")
    major, minor, patch, prerelease, _build = match.groups()
    core = (major, minor, patch)
    pre_ids = tuple(prerelease.split(".")) if prerelease else ()
    return core, pre_ids


def _is_numeric(text):
    # Validated identifiers are ASCII-only, so checking the characters is exact.
    return bool(text) and all("0" <= ch <= "9" for ch in text)


def _compare_numeric_strings(x, y):
    """Three-way compare of canonical numeric strings (no leading zeros)."""
    if len(x) != len(y):
        return (len(x) > len(y)) - (len(x) < len(y))
    return (x > y) - (x < y)


def _compare_identifiers(x, y):
    x_numeric = _is_numeric(x)
    y_numeric = _is_numeric(y)
    if x_numeric and y_numeric:
        return _compare_numeric_strings(x, y)
    if x_numeric != y_numeric:
        # Numeric identifiers always have lower precedence than alphanumeric.
        return -1 if x_numeric else 1
    return (x > y) - (x < y)


def _compare_prerelease(x, y):
    # A version without a prerelease has higher precedence.
    if not x and not y:
        return 0
    if not x:
        return 1
    if not y:
        return -1
    for xi, yi in zip(x, y):
        result = _compare_identifiers(xi, yi)
        if result:
            return result
    return (len(x) > len(y)) - (len(x) < len(y))


def compare(a, b):
    """Compare the precedence of two semantic versions.

    Returns -1 if ``a`` has lower precedence than ``b``, 0 if they have equal
    precedence, and 1 if ``a`` has higher precedence. Build metadata is ignored.

    Both arguments are validated before any comparison. Raises ``ValueError``
    if either is not a valid semantic version.
    """
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)
    for xa, xb in zip(core_a, core_b):
        result = _compare_numeric_strings(xa, xb)
        if result:
            return result
    return _compare_prerelease(pre_a, pre_b)
