import re


_VERSION_PATTERN = re.compile(
    r"(?P<major>0|[1-9][0-9]*)\."
    r"(?P<minor>0|[1-9][0-9]*)\."
    r"(?P<patch>0|[1-9][0-9]*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


def _parse_version(version):
    """Validate a version and return its core and prerelease identifiers."""
    if not isinstance(version, str):
        raise ValueError("Version must be a string")

    match = _VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise ValueError(f"Invalid semantic version: {version!r}")

    prerelease = match.group("prerelease")
    if prerelease is not None:
        prerelease = tuple(prerelease.split("."))
        if any(
            len(identifier) > 1 and identifier[0] == "0" and identifier.isdigit()
            for identifier in prerelease
        ):
            raise ValueError(f"Invalid semantic version: {version!r}")

    return (match.group("major", "minor", "patch"), prerelease)


def _compare_numeric(a, b):
    """Compare canonical numeric identifiers without converting them to integers."""
    return (len(a) > len(b)) - (len(a) < len(b)) or (a > b) - (a < b)


def compare(a, b):
    """Compare two semantic versions, returning -1, 0, or 1."""
    core_a, prerelease_a = _parse_version(a)
    core_b, prerelease_b = _parse_version(b)

    for component_a, component_b in zip(core_a, core_b):
        result = _compare_numeric(component_a, component_b)
        if result:
            return result

    if prerelease_a is None:
        return 0 if prerelease_b is None else 1
    if prerelease_b is None:
        return -1

    for identifier_a, identifier_b in zip(prerelease_a, prerelease_b):
        numeric_a = identifier_a.isdigit()
        numeric_b = identifier_b.isdigit()
        if numeric_a and numeric_b:
            result = _compare_numeric(identifier_a, identifier_b)
        elif numeric_a != numeric_b:
            return -1 if numeric_a else 1
        else:
            result = (identifier_a > identifier_b) - (identifier_a < identifier_b)
        if result:
            return result

    return (len(prerelease_a) > len(prerelease_b)) - (
        len(prerelease_a) < len(prerelease_b)
    )
