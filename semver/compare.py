import re


_VERSION = re.compile(
    r"(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


def _precedence_key(version):
    match = _VERSION.fullmatch(version) if isinstance(version, str) else None
    if match is None:
        raise ValueError(f"Invalid semantic version: {version!r}")

    # Length followed by ASCII digits gives numeric order for any size integer.
    core = tuple((len(part), part) for part in match.group(1, 2, 3))
    prerelease = match.group(4)
    identifiers = []
    if prerelease is not None:
        for identifier in prerelease.split("."):
            if identifier.isdigit():
                if len(identifier) > 1 and identifier.startswith("0"):
                    raise ValueError(f"Invalid semantic version: {version!r}")
                identifiers.append((0, len(identifier), identifier))
            else:
                identifiers.append((1, identifier))

    # The release flag sorts releases above prereleases of the same core.
    # Build metadata has been validated by the regex and is omitted here.
    return core, prerelease is None, tuple(identifiers)


def compare(a, b):
    """Return -1, 0, or 1 for SemVer 2.0.0 precedence; reject invalid versions."""
    a_key = _precedence_key(a)
    b_key = _precedence_key(b)
    return (a_key > b_key) - (a_key < b_key)
