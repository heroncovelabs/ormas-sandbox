"""Semantic Versioning 2.0.0 precedence comparison."""

import re


_SEMVER = re.compile(
    r"(?P<major>0|[1-9][0-9]*)\."
    r"(?P<minor>0|[1-9][0-9]*)\."
    r"(?P<patch>0|[1-9][0-9]*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


def _parse(version):
    if not isinstance(version, str):
        raise ValueError(f"Invalid semantic version: {version!r}")

    match = _SEMVER.fullmatch(version)
    if match is None:
        raise ValueError(f"Invalid semantic version: {version!r}")

    core = tuple(int(match[field]) for field in ("major", "minor", "patch"))
    prerelease = match["prerelease"]
    if prerelease is None:
        return core, None

    identifiers = []
    for identifier in prerelease.split("."):
        if identifier.isdigit():
            if len(identifier) > 1 and identifier.startswith("0"):
                raise ValueError(f"Invalid semantic version: {version!r}")
            identifiers.append(int(identifier))
        else:
            identifiers.append(identifier)
    return core, identifiers


def _cmp(a, b):
    return (a > b) - (a < b)


def compare(a, b):
    """Return -1, 0, or 1 according to SemVer precedence of *a* and *b*."""
    a_core, a_prerelease = _parse(a)
    b_core, b_prerelease = _parse(b)

    if a_core != b_core:
        return _cmp(a_core, b_core)
    if a_prerelease is None or b_prerelease is None:
        if a_prerelease is None and b_prerelease is None:
            return 0
        return 1 if a_prerelease is None else -1

    for a_identifier, b_identifier in zip(a_prerelease, b_prerelease):
        if a_identifier == b_identifier:
            continue
        if isinstance(a_identifier, int):
            if isinstance(b_identifier, int):
                return _cmp(a_identifier, b_identifier)
            return -1
        if isinstance(b_identifier, int):
            return 1
        return _cmp(a_identifier, b_identifier)

    return _cmp(len(a_prerelease), len(b_prerelease))
