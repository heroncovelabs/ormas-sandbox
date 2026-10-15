import re

_IDENT = r"[0-9A-Za-z-]+"
_VERSION = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+" + _IDENT + r"(?:\." + _IDENT + r")*)?"
)


def _parse(version):
    if not isinstance(version, str):
        raise ValueError("semver version must be a string: %r" % (version,))
    match = _VERSION.fullmatch(version)
    if match is None:
        raise ValueError("invalid semver version: %r" % (version,))
    major, minor, patch, prerelease = match.groups()
    core = (int(major), int(minor), int(patch))
    identifiers = None
    if prerelease is not None:
        identifiers = [(0, int(p), "") if p.isdigit() else (1, 0, p)
                       for p in prerelease.split(".")]
    return core, identifiers


def _cmp(x, y):
    return (x > y) - (x < y)


def compare(a, b):
    """Compare two semantic versions, returning -1, 0, or 1 (see issue.md)."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)
    result = _cmp(core_a, core_b)
    if result:
        return result
    if pre_a is None and pre_b is None:
        return 0
    if pre_a is None:
        return 1
    if pre_b is None:
        return -1
    for x, y in zip(pre_a, pre_b):
        result = _cmp(x, y)
        if result:
            return result
    return _cmp(len(pre_a), len(pre_b))
