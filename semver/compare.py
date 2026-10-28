"""Semantic Versioning 2.0.0 precedence comparison."""

import re

_IDENT_RE = re.compile(r"^[0-9A-Za-z-]+$")
_NUM_RE = re.compile(r"^[0-9]+$")
_CORE_RE = re.compile(r"^(0|[1-9][0-9]*)$")


def _parse_prerelease(text):
    if text == "":
        raise ValueError("empty prerelease")
    identifiers = []
    for ident in text.split("."):
        if not ident or not _IDENT_RE.match(ident):
            raise ValueError("invalid prerelease identifier: %r" % (ident,))
        if _NUM_RE.match(ident):
            if len(ident) > 1 and ident[0] == "0":
                raise ValueError("leading zero in numeric identifier: %r" % (ident,))
            identifiers.append((0, int(ident), ident))
        else:
            identifiers.append((1, ident, ident))
    return identifiers


def _parse_build(text):
    if text == "":
        raise ValueError("empty build metadata")
    for ident in text.split("."):
        if not ident or not _IDENT_RE.match(ident):
            raise ValueError("invalid build identifier: %r" % (ident,))
    return text


def _parse(version):
    if not isinstance(version, str):
        raise ValueError("version must be a string: %r" % (version,))
    rest = version
    build = None
    if "+" in rest:
        rest, build = rest.split("+", 1)
        if "+" in build:
            raise ValueError("invalid build metadata: %r" % (version,))
        _parse_build(build)
    prerelease = None
    if "-" in rest:
        rest, prerelease = rest.split("-", 1)
    core = rest.split(".")
    if len(core) != 3:
        raise ValueError("expected MAJOR.MINOR.PATCH: %r" % (version,))
    numbers = []
    for part in core:
        if not _CORE_RE.match(part):
            raise ValueError("invalid numeric field: %r" % (part,))
        numbers.append(int(part))
    pre = _parse_prerelease(prerelease) if prerelease is not None else None
    return tuple(numbers), pre


def _sign(value):
    return (value > 0) - (value < 0)


def _compare_prerelease(a, b):
    if a is None and b is None:
        return 0
    if a is None:
        return 1
    if b is None:
        return -1
    for left, right in zip(a, b):
        if left == right:
            continue
        if left[0] != right[0]:
            return -1 if left[0] < right[0] else 1
        if left[0] == 0:
            return _sign(left[1] - right[1])
        return -1 if left[1] < right[1] else 1
    return _sign(len(a) - len(b))


def compare(a, b):
    """Compare two semantic versions, returning -1, 0, or 1."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)
    for left, right in zip(core_a, core_b):
        if left != right:
            return -1 if left < right else 1
    return _compare_prerelease(pre_a, pre_b)
