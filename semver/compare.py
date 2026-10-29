import re

_NUMERIC_CORE = r"(?:0|[1-9][0-9]*)"
_PRE_ID = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
_BUILD_ID = r"[0-9A-Za-z-]+"

_SEMVER_RE = re.compile(
    r"(?P<major>" + _NUMERIC_CORE + r")\."
    r"(?P<minor>" + _NUMERIC_CORE + r")\."
    r"(?P<patch>" + _NUMERIC_CORE + r")"
    r"(?:-(?P<pre>" + _PRE_ID + r"(?:\." + _PRE_ID + r")*))?"
    r"(?:\+(?P<build>" + _BUILD_ID + r"(?:\." + _BUILD_ID + r")*))?",
    re.ASCII,
)


def _parse_version(version):
    """Validate a semver string and return (core, prerelease).

    core is a tuple of three decimal strings; prerelease is a tuple of
    identifier strings, or None when absent. Build metadata is validated
    and omitted.
    """
    if not isinstance(version, str):
        raise ValueError(f"invalid semantic version: {version!r}")
    match = _SEMVER_RE.fullmatch(version)
    if match is None:
        raise ValueError(f"invalid semantic version: {version!r}")
    core = (match.group("major"), match.group("minor"), match.group("patch"))
    pre = match.group("pre")
    prerelease = tuple(pre.split(".")) if pre is not None else None
    return core, prerelease


def _compare_numeric(left, right):
    """Compare two validated decimal strings without leading zeros."""
    if len(left) != len(right):
        return -1 if len(left) < len(right) else 1
    if left == right:
        return 0
    return -1 if left < right else 1


def _is_numeric(identifier):
    return identifier.isdigit()


def _compare_identifier(left, right):
    left_num = _is_numeric(left)
    right_num = _is_numeric(right)
    if left_num and right_num:
        return _compare_numeric(left, right)
    if left_num != right_num:
        return -1 if left_num else 1
    if left == right:
        return 0
    return -1 if left < right else 1


def _compare_prerelease(left, right):
    if left is None and right is None:
        return 0
    if left is None:
        return 1
    if right is None:
        return -1
    for l_id, r_id in zip(left, right):
        result = _compare_identifier(l_id, r_id)
        if result != 0:
            return result
    if len(left) == len(right):
        return 0
    return -1 if len(left) < len(right) else 1


def compare(a, b):
    """Return -1, 0, or 1 by SemVer 2.0.0 precedence, ignoring build metadata.

    Raise ValueError if either version is invalid.
    """
    core_a, pre_a = _parse_version(a)
    core_b, pre_b = _parse_version(b)
    for field_a, field_b in zip(core_a, core_b):
        result = _compare_numeric(field_a, field_b)
        if result != 0:
            return result
    return _compare_prerelease(pre_a, pre_b)
