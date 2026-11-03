import re


_NUMERIC = r"(?:0|[1-9][0-9]*)"
_IDENT = r"[0-9A-Za-z-]+"
_CORE = r"(" + _NUMERIC + r")\.(" + _NUMERIC + r")\.(" + _NUMERIC + r")"
_PRERELEASE = r"(" + _IDENT + r"(?:\." + _IDENT + r")*)"
_BUILD = r"(" + _IDENT + r"(?:\." + _IDENT + r")*)"
_SEMVER_RE = re.compile(
    _CORE + r"(?:-" + _PRERELEASE + r")?(?:\+" + _BUILD + r")?"
)
_ASCII_DIGITS = frozenset("0123456789")


def _parse(version):
    """Validate and split a semantic version into (core, prerelease_ids).

    core is a tuple of three canonical numeric ordering keys, one per
    MAJOR/MINOR/PATCH field, each a (length, digits) pair. Because leading
    zeros are rejected, comparing these pairs tuple-wise orders the fields
    numerically without integer conversion. prerelease_ids is a tuple of
    identifier strings (empty when there is no prerelease). Build metadata is
    validated but discarded.
    """
    if not isinstance(version, str):
        raise ValueError("semantic version must be a string: %r" % (version,))
    match = _SEMVER_RE.fullmatch(version)
    if match is None:
        raise ValueError("invalid semantic version: %r" % (version,))
    core = tuple((len(match.group(i)), match.group(i)) for i in (1, 2, 3))
    pre_text = match.group(4)
    if pre_text is None:
        prerelease = ()
    else:
        prerelease = tuple(pre_text.split("."))
        for ident in prerelease:
            # Numeric prerelease identifiers must not have leading zeros.
            if set(ident) <= _ASCII_DIGITS and len(ident) > 1 and ident[0] == "0":
                raise ValueError("invalid semantic version: %r" % (version,))
    return core, prerelease


def _sign(x, y):
    if x < y:
        return -1
    if x > y:
        return 1
    return 0


def _identifier_key(ident):
    # Numeric identifiers sort below alphanumeric ones; numeric ones compare
    # by digit count then digit text (leading zeros are rejected during
    # validation, so this matches numeric order), alphanumeric ones lexically
    # in ASCII order.
    if set(ident) <= _ASCII_DIGITS:
        return (0, len(ident), ident)
    return (1, 0, ident)


def _compare_prerelease(pa, pb):
    if not pa and not pb:
        return 0
    # A version without a prerelease has higher precedence.
    if not pa:
        return 1
    if not pb:
        return -1
    for ia, ib in zip(pa, pb):
        result = _sign(_identifier_key(ia), _identifier_key(ib))
        if result != 0:
            return result
    return _sign(len(pa), len(pb))


def compare(a, b):
    """Compare two semantic versions, returning -1, 0, or 1 (see issue.md)."""
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)
    result = _sign(core_a, core_b)
    if result != 0:
        return result
    return _compare_prerelease(pre_a, pre_b)
