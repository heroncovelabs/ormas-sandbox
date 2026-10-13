import re


_VERSION = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


def _parse(version):
    if not isinstance(version, str):
        raise ValueError("A semantic version must be a string")
    match = _VERSION.fullmatch(version)
    if match is None:
        raise ValueError("Invalid semantic version: {!r}".format(version))
    prerelease = tuple(match.group(4).split(".")) if match.group(4) else ()
    for identifier in prerelease:
        if identifier.isdigit() and len(identifier) > 1 and identifier[0] == "0":
            raise ValueError("Numeric prerelease identifiers must have no leading zeros")
    return match.group(1, 2, 3), prerelease


def _order(a, b):
    return (a > b) - (a < b)


def _numeric_order(a, b):
    # Valid numeric identifiers have no leading zeros; length gives magnitude.
    return _order((len(a), a), (len(b), b))


def compare(a, b):
    """Return -1, 0, or 1 according to Semantic Versioning 2.0.0 precedence.

    Both versions are validated before comparison. Build metadata is ignored.
    Invalid versions raise ValueError.
    """
    core_a, prerelease_a = _parse(a)
    core_b, prerelease_b = _parse(b)
    for left, right in zip(core_a, core_b):
        result = _numeric_order(left, right)
        if result:
            return result

    if not prerelease_a or not prerelease_b:
        return _order(bool(prerelease_b), bool(prerelease_a))

    for left, right in zip(prerelease_a, prerelease_b):
        numeric_left, numeric_right = left.isdigit(), right.isdigit()
        if numeric_left and numeric_right:
            result = _numeric_order(left, right)
        elif numeric_left != numeric_right:
            result = -1 if numeric_left else 1
        else:
            result = _order(left, right)
        if result:
            return result
    return _order(len(prerelease_a), len(prerelease_b))
