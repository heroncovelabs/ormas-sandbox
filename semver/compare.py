import re

_IDENT = r"[0-9A-Za-z-]+"
_SEMVER = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+(" + _IDENT + r"(?:\." + _IDENT + r")*))?"
)


def _parse(version):
    if not isinstance(version, str):
        raise ValueError("version must be a string: %r" % (version,))
    m = _SEMVER.fullmatch(version)
    if m is None:
        raise ValueError("invalid semantic version: %r" % (version,))
    core = tuple(int(x) for x in m.group(1, 2, 3))
    pre = m.group(4)
    prerelease = tuple(pre.split(".")) if pre is not None else None
    return core, prerelease


def _cmp(x, y):
    return (x > y) - (x < y)


def _cmp_identifier(x, y):
    x_num, y_num = x.isdigit(), y.isdigit()
    if x_num and y_num:
        return _cmp(int(x), int(y))
    if x_num:
        return -1
    if y_num:
        return 1
    return _cmp(x, y)


def compare(a, b):
    """Compare two semantic versions, returning -1, 0, or 1 (see issue.md)."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)

    result = _cmp(core_a, core_b)
    if result:
        return result

    # A version without prerelease has higher precedence.
    if pre_a is None and pre_b is None:
        return 0
    if pre_a is None:
        return 1
    if pre_b is None:
        return -1

    for x, y in zip(pre_a, pre_b):
        result = _cmp_identifier(x, y)
        if result:
            return result
    return _cmp(len(pre_a), len(pre_b))
