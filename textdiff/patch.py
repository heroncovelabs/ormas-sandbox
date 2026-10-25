"""Apply and validate edit scripts produced by :mod:`textdiff.diff`."""


class PatchError(Exception):
    """Raised when an edit script does not apply cleanly to its source."""


def apply(ops, a):
    """Apply ``ops`` to the lines in ``a``, returning the reconstructed lines."""
    result = []
    position = 0

    for kind, line in ops:
        if kind == "ins":
            result.append(line)
        elif kind in ("keep", "del"):
            if position >= len(a) or a[position] != line:
                raise PatchError("edit script does not match the source")
            position += 1
            if kind == "keep":
                result.append(line)
        else:
            raise PatchError("unknown edit operation: {!r}".format(kind))

    if position != len(a):
        raise PatchError("edit script did not consume the entire source")
    return result
