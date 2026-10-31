import re


_VERSION = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


def _parse(version):
    """Validate a version and produce core and prerelease precedence keys."""
    match = _VERSION.fullmatch(version) if isinstance(version, str) else None
    if match is None:
        raise ValueError(f"Invalid semantic version: {version!r}")

    # Length then ASCII digits gives numeric order for arbitrarily large fields.
    core = tuple((len(part), part) for part in match.group(1, 2, 3))
    prerelease = match.group(4)
    if prerelease is None:
        return core, None

    identifiers = []
    for identifier in prerelease.split("."):
        if identifier.isdigit():
            if len(identifier) > 1 and identifier.startswith("0"):
                raise ValueError(f"Invalid semantic version: {version!r}")
            identifiers.append((0, len(identifier), identifier))
        else:
            identifiers.append((1, identifier))
    return core, tuple(identifiers)


def compare(a, b):
    """Return -1, 0, or 1 according to Semantic Versioning 2.0.0 precedence.

    Both versions are validated, and build metadata is ignored.
    """
    core_a, prerelease_a = _parse(a)
    core_b, prerelease_b = _parse(b)
    if core_a != core_b:
        return (core_a > core_b) - (core_a < core_b)
    if prerelease_a is None:
        return int(prerelease_b is not None)
    if prerelease_b is None:
        return -1
    return (prerelease_a > prerelease_b) - (prerelease_a < prerelease_b)
