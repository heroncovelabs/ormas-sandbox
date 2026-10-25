import re

# ASCII-only SemVer 2.0.0 grammar. Numeric identifiers forbid leading zeros.
_NUMERIC_ID = r"(?:0|[1-9][0-9]*)"
_ALNUM_ID = r"(?:[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
_PRE_ID = r"(?:%s|%s)" % (_NUMERIC_ID, _ALNUM_ID)
_BUILD_ID = r"(?:[0-9A-Za-z-]+)"

_SEMVER_RE = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-(%s(?:\.%s)*))?"
    r"(?:\+(%s(?:\.%s)*))?" % (_PRE_ID, _PRE_ID, _BUILD_ID, _BUILD_ID)
)


def _parse(version):
    """Validate a full version string; return (core tuple, prerelease keys or None)."""
    if not isinstance(version, str):
        raise ValueError("version must be a string: %r" % (version,))
    m = _SEMVER_RE.fullmatch(version)
    if m is None:
        raise ValueError("invalid semantic version: %r" % (version,))
    # Canonical decimal fields (no leading zeros): length first, then lexical
    # order, gives numeric ordering without integer conversion.
    core = tuple((len(f), f) for f in (m.group(1), m.group(2), m.group(3)))
    pre = m.group(4)
    if pre is None:
        return core, None
    keys = []
    for ident in pre.split("."):
        if ident.isdigit():
            # Numeric identifiers sort below alphanumeric ones.
            keys.append((0, len(ident), ident))
        else:
            keys.append((1, 0, ident))
    return core, keys


def compare(a, b):
    """Return -1, 0, or 1 according to SemVer 2.0.0 precedence.

    Build metadata is ignored. Both versions must be valid semantic-version
    strings; invalid input raises ValueError.
    """
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)

    if core_a != core_b:
        return -1 if core_a < core_b else 1

    if pre_a is None and pre_b is None:
        return 0
    if pre_a is None:
        return 1
    if pre_b is None:
        return -1

    # Identifier lists: element-wise comparison, then shorter list is lower.
    if pre_a == pre_b:
        return 0
    return -1 if pre_a < pre_b else 1
