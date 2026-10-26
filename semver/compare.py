import re

_NUM = r"(?:0|[1-9][0-9]*)"
_IDENT = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
_PATTERN = re.compile(
    r"(%s)\.(%s)\.(%s)"
    r"(?:-(%s(?:\.%s)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?" % (_NUM, _NUM, _NUM, _IDENT, _IDENT)
)


def _parse(version):
    if not isinstance(version, str):
        raise ValueError("version must be a string: %r" % (version,))
    m = _PATTERN.fullmatch(version)
    if m is None:
        raise ValueError("invalid semantic version: %r" % (version,))
    core = tuple(int(m.group(i)) for i in (1, 2, 3))
    pre = m.group(4)
    prerelease = pre.split(".") if pre else None
    return core, prerelease


def _cmp(x, y):
    return (x > y) - (x < y)


def _compare_identifier(x, y):
    x_num = x.isdigit()
    y_num = y.isdigit()
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

    if pre_a is None and pre_b is None:
        return 0
    if pre_a is None:
        return 1
    if pre_b is None:
        return -1

    for x, y in zip(pre_a, pre_b):
        result = _compare_identifier(x, y)
        if result:
            return result
    return _cmp(len(pre_a), len(pre_b))
