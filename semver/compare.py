"""Semantic Versioning 2.0.0 precedence comparison."""

import re

__all__ = ["compare"]

_NUMERIC = re.compile(r"[0-9]+")
_IDENTIFIER = re.compile(r"[0-9A-Za-z-]+")
_VERSION = re.compile(
    r"(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<patch>[0-9]+)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)


class _Version:
    """A parsed semantic version."""

    __slots__ = ("major", "minor", "patch", "prerelease")

    def __init__(self, major, minor, patch, prerelease):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.prerelease = prerelease


def _parse_numeric(text, label):
    """Parse a numeric core field, rejecting leading zeros."""
    if not _NUMERIC.fullmatch(text):
        raise ValueError(f"invalid {label}: {text!r}")
    if len(text) > 1 and text[0] == "0":
        raise ValueError(f"leading zero in {label}: {text!r}")
    return int(text)


def _parse(version):
    """Parse and validate a semantic version string."""
    if not isinstance(version, str):
        raise ValueError(f"version must be a string, got {type(version).__name__}")
    match = _VERSION.fullmatch(version)
    if match is None:
        raise ValueError(f"invalid semantic version: {version!r}")

    major = _parse_numeric(match.group("major"), "major")
    minor = _parse_numeric(match.group("minor"), "minor")
    patch = _parse_numeric(match.group("patch"), "patch")

    prerelease = ()
    raw_prerelease = match.group("prerelease")
    if raw_prerelease is not None:
        identifiers = []
        for identifier in raw_prerelease.split("."):
            if not identifier or not _IDENTIFIER.fullmatch(identifier):
                raise ValueError(f"invalid prerelease identifier: {identifier!r}")
            if identifier.isdigit():
                if len(identifier) > 1 and identifier[0] == "0":
                    raise ValueError(
                        f"leading zero in numeric prerelease identifier: {identifier!r}"
                    )
                identifiers.append((0, int(identifier), ""))
            else:
                identifiers.append((1, 0, identifier))
        prerelease = tuple(identifiers)
    elif raw_prerelease == "":
        raise ValueError(f"empty prerelease in: {version!r}")

    # Build metadata is parsed only for validity; it is ignored for precedence.
    raw_build = match.group("build")
    if raw_build is not None:
        for identifier in raw_build.split("."):
            if not identifier or not _IDENTIFIER.fullmatch(identifier):
                raise ValueError(f"invalid build identifier: {identifier!r}")

    return _Version(major, minor, patch, prerelease)


def _compare_core(a, b):
    """Compare the numeric core fields."""
    for field in ("major", "minor", "patch"):
        left = getattr(a, field)
        right = getattr(b, field)
        if left != right:
            return -1 if left < right else 1
    return 0


def _compare_prerelease(a, b):
    """Compare prerelease identifier tuples."""
    if not a and not b:
        return 0
    if not a:
        return 1  # a release has higher precedence than a prerelease
    if not b:
        return -1
    for left, right in zip(a, b):
        if left != right:
            return -1 if left < right else 1
    if len(a) == len(b):
        return 0
    return -1 if len(a) < len(b) else 1


def _sign(value):
    """Normalize an integer to -1, 0, or 1."""
    if value < 0:
        return -1
    if value > 0:
        return 1
    return 0


def compare(a, b):
    """Compare two semantic versions, returning -1, 0, or 1.

    Raises:
        ValueError: If either argument is not a valid semantic version.
    """
    left = _parse(a)
    right = _parse(b)
    result = _compare_core(left, right)
    if result == 0:
        result = _compare_prerelease(left.prerelease, right.prerelease)
    return _sign(result)
