import re

_NUM = r"(?:0|[1-9][0-9]*)"
_PRE_ID = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
_BUILD_ID = r"[0-9A-Za-z-]+"
_RE = re.compile(
    r"(%s)\.(%s)\.(%s)(?:-(%s(?:\.%s)*))?(?:\+(%s(?:\.%s)*))?\Z"
    % (_NUM, _NUM, _NUM, _PRE_ID, _PRE_ID, _BUILD_ID, _BUILD_ID)
)
_DIGITS = re.compile(r"[0-9]+\Z")


def _parse(v):
    if not isinstance(v, str):
        raise ValueError("version must be a string: %r" % (v,))
    m = _RE.match(v)
    if not m:
        raise ValueError("invalid semantic version: %r" % (v,))
    core = tuple(int(m.group(i)) for i in (1, 2, 3))
    pre = m.group(4).split(".") if m.group(4) is not None else None
    return core, pre


def _cmp(x, y):
    return (x > y) - (x < y)


def compare(a, b):
    """Compare two semantic versions, returning -1, 0, or 1."""
    ca, pa = _parse(a)
    cb, pb = _parse(b)
    if ca != cb:
        return _cmp(ca, cb)
    if pa is None and pb is None:
        return 0
    if pa is None:
        return 1
    if pb is None:
        return -1
    for x, y in zip(pa, pb):
        nx, ny = bool(_DIGITS.match(x)), bool(_DIGITS.match(y))
        if nx and ny:
            r = _cmp(int(x), int(y))
        elif nx:
            r = -1
        elif ny:
            r = 1
        else:
            r = _cmp(x, y)
        if r:
            return r
    return _cmp(len(pa), len(pb))
