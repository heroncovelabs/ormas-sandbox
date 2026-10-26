"""Semantic Versioning 2.0.0 precedence comparison (semver.org section 11)."""

import re

_SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

_NUMERIC_RE = re.compile(r"^\d+$")


def _parse(version):
    """Validate *version* and return (core, prerelease identifiers or None)."""
    if not isinstance(version, str):
        raise ValueError("version must be a string, got %r" % (version,))

    match = _SEMVER_RE.match(version)
    if match is None:
        raise ValueError("invalid semantic version: %r" % (version,))

    core = (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )

    prerelease = match.group("prerelease")
    if prerelease is None:
        identifiers = None
    else:
        identifiers = prerelease.split(".")
        for identifier in identifiers:
            if _NUMERIC_RE.match(identifier):
                if len(identifier) > 1 and identifier[0] == "0":
                    raise ValueError(
                        "invalid numeric prerelease identifier: %r" % (identifier,)
                    )
            elif not identifier:
                raise ValueError("empty prerelease identifier in %r" % (version,))

    return core, identifiers


def _compare_identifier(x, y):
    x_numeric = bool(_NUMERIC_RE.match(x))
    y_numeric = bool(_NUMERIC_RE.match(y))
    if x_numeric and y_numeric:
        xi, yi = int(x), int(y)
        return (xi > yi) - (xi < yi)
    if x_numeric:
        return -1
    if y_numeric:
        return 1
    return (x > y) - (x < y)


def _compare_prerelease(a_ids, b_ids):
    if a_ids is None and b_ids is None:
        return 0
    if a_ids is None:
        return 1
    if b_ids is None:
        return -1

    for x, y in zip(a_ids, b_ids):
        result = _compare_identifier(x, y)
        if result:
            return result

    return (len(a_ids) > len(b_ids)) - (len(a_ids) < len(b_ids))


def compare(a, b):
    """Compare two semantic versions, returning -1, 0, or 1 (see issue.md)."""
    a_core, a_ids = _parse(a)
    b_core, b_ids = _parse(b)

    if a_core != b_core:
        return (a_core > b_core) - (a_core < b_core)

    return _compare_prerelease(a_ids, b_ids)
