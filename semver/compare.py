"""Semantic Versioning 2.0.0 precedence comparison.

``compare(a, b)`` returns -1, 0, or 1 according to whether version ``a`` has
lower, equal, or higher precedence than ``b``, per semver.org section 11.
"""

import re

# The official semver.org 2.0.0 pattern. It rejects wrong field counts,
# leading zeros in numeric fields (major/minor/patch and numeric prerelease
# identifiers), empty prereleases, empty identifiers, and stray characters.
_VERSION_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?P<pre>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?\Z"
)


def _parse(version):
    """Split a valid semver string into (major, minor, patch, prerelease).

    ``prerelease`` is None for a release, otherwise a tuple of its
    dot-separated identifiers. Build metadata is validated but discarded:
    it never affects precedence.
    """
    if not isinstance(version, str):
        raise ValueError("version must be a string, got %r" % (version,))
    match = _VERSION_RE.match(version)
    if match is None:
        raise ValueError("invalid semantic version: %r" % (version,))
    major, minor, patch = (int(part) for part in match.group(1, 2, 3))
    raw = match.group("pre")
    prerelease = tuple(raw.split(".")) if raw is not None else None
    return major, minor, patch, prerelease


def _sign(value):
    return (value > 0) - (value < 0)


def _compare_prerelease(left, right):
    """Compare prerelease identifier tuples (semver.org rule 11.4)."""
    for x, y in zip(left, right):
        if x == y:
            continue
        if x.isdigit() and y.isdigit():
            return _sign(int(x) - int(y))  # numeric: compare numerically
        if x.isdigit():  # numeric identifiers rank below alphanumeric ones
            return -1
        if y.isdigit():
            return 1
        return (x > y) - (x < y)  # alphanumeric: ASCII lexical order
    return _sign(len(left) - len(right))  # more identifiers: higher precedence


def compare(a, b):
    """Return -1, 0, or 1 as ``a`` is lower, equal, or higher than ``b``.

    Both arguments must be valid Semantic Versioning 2.0.0 strings;
    anything else raises ValueError. Build metadata is ignored.
    """
    major_a, minor_a, patch_a, pre_a = _parse(a)
    major_b, minor_b, patch_b, pre_b = _parse(b)
    for left, right in ((major_a, major_b), (minor_a, minor_b), (patch_a, patch_b)):
        if left != right:
            return -1 if left < right else 1
    if pre_a is None and pre_b is None:
        return 0
    if pre_a is None:  # a release outranks any prerelease of the same triple
        return 1
    if pre_b is None:
        return -1
    return _compare_prerelease(pre_a, pre_b)
