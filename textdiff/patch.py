"""Apply an edit script produced by ``textdiff/diff.py``."""


class PatchError(Exception):
    """Raised when an edit script does not apply cleanly to the given source."""


def apply(ops, a):
    """Apply edit script ``ops`` to list-of-lines ``a``, returning the result.

    "keep"/"del" ops must match the next line of ``a`` (else PatchError); "ins"
    ops add a line. Every line of ``a`` must be consumed (else PatchError).
    """
    result = []
    pos = 0
    total = len(a)
    for op, line in ops:
        if op == "keep":
            if pos >= total or a[pos] != line:
                raise PatchError("keep line does not match next source line")
            result.append(line)
            pos += 1
        elif op == "del":
            if pos >= total or a[pos] != line:
                raise PatchError("del line does not match next source line")
            pos += 1
        elif op == "ins":
            result.append(line)
        else:
            raise PatchError("unknown op kind: %r" % (op,))
    if pos != total:
        raise PatchError("script finished with source lines unconsumed")
    return result
