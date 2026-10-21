"""Semantic Versioning 2.0.0 precedence comparison (semver.org section 11)."""

import re

_NUMERIC_ID = r"0|[1-9][0-9]*"
_PRE_ID = r"(?:%s|[0-9]*[A-Za-z-][0-9A-Za-z-]*)" % _NUMERIC_ID
_BUILD_ID = r"[0-9A-Za-z-]+"

_VERSION = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-(%s(?:\.%s)*))?"
    r"(?:\+(%s(?:\.%s)*))?" % (_PRE_ID, _PRE_ID, _BUILD_ID, _BUILD_ID),
    re.ASCII,
)


def _parse(version):
    """Return (core tuple, prerelease identifier list or None)."""
    if not isinstance(version, str):
        raise ValueError("version must be a string: %r" % (version,))
    match = _VERSION.fullmatch(version)
    if match is None:
        raise ValueError("invalid semantic version: %r" % (version,))
    major, minor, patch, pre, _build = match.groups()
    core = (int(major), int(minor), int(patch))
    if pre is None:
        return core, None
    return core, pre.split(".")


def _identifier_key(identifier):
    # Numeric identifiers sort below alphanumeric ones; numerics compare by value.
    if identifier.isdigit():
        return (0, int(identifier), "")
    return (1, 0, identifier)


def _prerelease_key(identifiers):
    return [_identifier_key(part) for part in identifiers]


def compare(a, b):
    """Return -1, 0, or 1 as version ``a`` has lower, equal, or higher precedence than ``b``."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)
    if core_a != core_b:
        return -1 if core_a < core_b else 1
    if pre_a == pre_b:
        return 0
    # A release (no prerelease) outranks any prerelease of the same core version.
    if pre_a is None:
        return 1
    if pre_b is None:
        return -1
    key_a, key_b = _prerelease_key(pre_a), _prerelease_key(pre_b)
    # Python list ordering gives "more identifiers wins" when all shared ones match.
    if key_a == key_b:
        return 0
    return -1 if key_a < key_b else 1
