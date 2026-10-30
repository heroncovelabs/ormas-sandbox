"""Apply an edit script produced by ``textdiff/diff.py``, validating its source."""


class PatchError(Exception):
    """Raised when an edit script does not apply cleanly to the given source."""


def apply(ops, a):
    """Apply edit script ``ops`` to list-of-lines ``a``, returning the result.

    "keep"/"del" ops must match the next line of ``a`` (else PatchError); "ins"
    ops add a line. Every line of ``a`` must be consumed (else PatchError).
    """
    result = []
    position = 0
    for kind, line in ops:
        if kind == "ins":
            result.append(line)
        elif kind in ("keep", "del"):
            if position >= len(a) or a[position] != line:
                raise PatchError("Source mismatch at line {}".format(position))
            position += 1
            if kind == "keep":
                result.append(line)
        else:
            raise PatchError("Unknown operation kind: {!r}".format(kind))

    if position != len(a):
        raise PatchError("Edit script left unconsumed source lines")
    return result
