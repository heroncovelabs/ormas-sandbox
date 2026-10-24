import re

# ASCII-only patterns; re.fullmatch enforces that the whole string is consumed.
_IDENT = r"[0-9A-Za-z-]+"
_CORE_NUM = r"(?:0|[1-9][0-9]*)"
_SEMVER_RE = re.compile(
    r"(?P<major>" + _CORE_NUM + r")\."
    r"(?P<minor>" + _CORE_NUM + r")\."
    r"(?P<patch>" + _CORE_NUM + r")"
    r"(?:-(?P<pre>" + _IDENT + r"(?:\." + _IDENT + r")*))?"
    r"(?:\+(?P<build>" + _IDENT + r"(?:\." + _IDENT + r")*))?"
)
_DIGITS_RE = re.compile(r"[0-9]+")


def _parse(version):
    """Validate a semver string and return (core, prerelease_identifiers).

    Core is a tuple of three digit strings. Prerelease identifiers is a list of
    strings (empty when the version is a release). Build metadata is validated
    but discarded because it does not affect precedence.
    Raises ValueError if the string is not valid SemVer 2.0.0.
    """
    if not isinstance(version, str):
        raise ValueError("semver version must be a string: %r" % (version,))
    m = _SEMVER_RE.fullmatch(version)
    if m is None:
        raise ValueError("invalid semantic version: %r" % (version,))
    pre = m.group("pre")
    pre_ids = pre.split(".") if pre is not None else []
    for ident in pre_ids:
        if _DIGITS_RE.fullmatch(ident) and len(ident) > 1 and ident[0] == "0":
            raise ValueError(
                "leading zero in prerelease identifier: %r" % (version,)
            )
    core = (m.group("major"), m.group("minor"), m.group("patch"))
    return core, pre_ids


def _cmp_numeric_str(x, y):
    """Compare two digit strings without leading zeros numerically."""
    if len(x) != len(y):
        return -1 if len(x) < len(y) else 1
    if x == y:
        return 0
    return -1 if x < y else 1


def _cmp_prerelease_ident(x, y):
    x_num = _DIGITS_RE.fullmatch(x) is not None
    y_num = _DIGITS_RE.fullmatch(y) is not None
    if x_num and y_num:
        return _cmp_numeric_str(x, y)
    if x_num:
        return -1  # numeric identifiers rank below alphanumeric ones
    if y_num:
        return 1
    if x == y:
        return 0
    return -1 if x < y else 1


def compare(a, b):
    """Compare two semantic versions by SemVer 2.0.0 precedence.

    Both arguments are fully validated first; a ValueError is raised if either
    is not a valid semantic version (MAJOR.MINOR.PATCH with optional
    -prerelease and +build sections).

    Precedence: MAJOR, MINOR, and PATCH are compared numerically in order.
    A version with a prerelease ranks below the same core without one.
    Prerelease identifiers are compared left to right: numeric identifiers
    numerically, numeric below alphanumeric, alphanumeric in ASCII order, and
    a longer sequence ranks higher when all shared identifiers are equal.
    Build metadata is ignored.

    Returns -1 if a has lower precedence than b, 0 if equal, and 1 if higher.
    """
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)

    for x, y in zip(core_a, core_b):
        c = _cmp_numeric_str(x, y)
        if c:
            return c

    if not pre_a and not pre_b:
        return 0
    if not pre_a:
        return 1
    if not pre_b:
        return -1

    for x, y in zip(pre_a, pre_b):
        c = _cmp_prerelease_ident(x, y)
        if c:
            return c

    if len(pre_a) == len(pre_b):
        return 0
    return -1 if len(pre_a) < len(pre_b) else 1
