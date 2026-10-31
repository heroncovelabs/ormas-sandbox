import re

_NUM = r"0|[1-9][0-9]*"
_PRE_ID = r"0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*"
_BUILD_ID = r"[0-9A-Za-z-]+"
_SEMVER = re.compile(
    rf"({_NUM})\.({_NUM})\.({_NUM})"
    rf"(?:-((?:{_PRE_ID})(?:\.(?:{_PRE_ID}))*))?"
    rf"(?:\+(?:{_BUILD_ID})(?:\.(?:{_BUILD_ID}))*)?"
)


def _parse(version):
    if not isinstance(version, str):
        raise ValueError(f"invalid semantic version: {version!r}")
    m = _SEMVER.fullmatch(version)
    if m is None:
        raise ValueError(f"invalid semantic version: {version!r}")
    core = tuple(int(m.group(i)) for i in (1, 2, 3))
    pre = m.group(4).split(".") if m.group(4) is not None else []
    return core, pre


def _cmp(x, y):
    return (x > y) - (x < y)


def _cmp_ident(x, y):
    x_num, y_num = x.isdigit(), y.isdigit()
    if x_num and y_num:
        return _cmp(int(x), int(y))
    if x_num != y_num:
        return -1 if x_num else 1
    return _cmp(x, y)


def compare(a, b):
    """Compare two semantic versions, returning -1, 0, or 1 (see issue.md)."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)
    if core_a != core_b:
        return _cmp(core_a, core_b)
    if not pre_a or not pre_b:
        # A release outranks any prerelease of the same core version.
        return _cmp(not pre_a, not pre_b)
    for x, y in zip(pre_a, pre_b):
        c = _cmp_ident(x, y)
        if c:
            return c
    return _cmp(len(pre_a), len(pre_b))
