import re


_NUMERIC = r"(0|[1-9][0-9]*)"
_IDENTIFIER = r"[0-9A-Za-z-]+"
_VERSION = re.compile(
    rf"{_NUMERIC}\.{_NUMERIC}\.{_NUMERIC}"
    rf"(?:-({_IDENTIFIER}(?:\.{_IDENTIFIER})*))?"
    rf"(?:\+{_IDENTIFIER}(?:\.{_IDENTIFIER})*)?"
)


def _numeric_key(identifier):
    # Validated numbers have no leading zeros; this supports any digit count.
    return len(identifier), identifier


def _parse(version):
    match = _VERSION.fullmatch(version) if isinstance(version, str) else None
    if match is None:
        raise ValueError(f"Invalid semantic version: {version!r}")

    core = tuple(_numeric_key(part) for part in match.group(1, 2, 3))
    prerelease = match.group(4)
    identifiers = prerelease.split(".") if prerelease is not None else ()
    for identifier in identifiers:
        if identifier.isdigit() and len(identifier) > 1 and identifier[0] == "0":
            raise ValueError(f"Invalid semantic version: {version!r}")
    return core, identifiers


def compare(a, b):
    """Return -1, 0, or 1 according to Semantic Versioning 2.0.0 precedence.

    Both versions must be valid; build metadata is ignored for precedence.
    """
    core_a, prerelease_a = _parse(a)
    core_b, prerelease_b = _parse(b)
    if core_a != core_b:
        return (core_a > core_b) - (core_a < core_b)

    if not prerelease_a or not prerelease_b:
        return int(bool(prerelease_b)) - int(bool(prerelease_a))

    for identifier_a, identifier_b in zip(prerelease_a, prerelease_b):
        if identifier_a == identifier_b:
            continue
        numeric_a = identifier_a.isdigit()
        numeric_b = identifier_b.isdigit()
        if numeric_a != numeric_b:
            return -1 if numeric_a else 1
        if numeric_a:
            key_a = _numeric_key(identifier_a)
            key_b = _numeric_key(identifier_b)
        else:
            key_a, key_b = identifier_a, identifier_b
        return (key_a > key_b) - (key_a < key_b)

    return (len(prerelease_a) > len(prerelease_b)) - (
        len(prerelease_a) < len(prerelease_b)
    )
