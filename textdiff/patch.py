"""Apply an edit script produced by ``textdiff/diff.py`` to its source."""


class PatchError(Exception):
    """Raised when an edit script does not apply cleanly to the given source."""


def apply(ops, a):
    """Apply edit script ``ops`` to list-of-lines ``a``, returning the result.

    "keep"/"del" ops must match the next line of ``a`` (else PatchError); "ins"
    ops add a line. Every line of ``a`` must be consumed (else PatchError).
    """
    result = []
    index = 0
    for kind, line in ops:
        if kind == "ins":
            result.append(line)
        elif kind in ("keep", "del"):
            if index >= len(a) or a[index] != line:
                raise PatchError("Source mismatch at line {}".format(index))
            index += 1
            if kind == "keep":
                result.append(line)
        else:
            raise PatchError("Unknown operation kind: {!r}".format(kind))

    if index != len(a):
        raise PatchError("Edit script leaves source lines unconsumed")
    return result
