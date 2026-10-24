"""Apply an edit script produced by ``textdiff/diff.py``."""


class PatchError(Exception):
    """Raised when an edit script does not apply cleanly to the given source."""


def apply(ops, a):
    """Apply edit script ``ops`` to list-of-lines ``a``, returning the result.

    "keep"/"del" ops must match the next unconsumed line of ``a`` (else
    PatchError); "ins" ops add a line without consuming ``a``. Every line of
    ``a`` must be consumed (else PatchError).
    """
    a = list(a)
    out = []
    pos = 0
    for op in ops:
        kind, line = op
        if kind in ("keep", "del"):
            if pos >= len(a) or a[pos] != line:
                raise PatchError("script does not match source at line %d" % pos)
            pos += 1
            if kind == "keep":
                out.append(line)
        elif kind == "ins":
            out.append(line)
        else:
            raise PatchError("unknown op kind: %r" % (kind,))
    if pos != len(a):
        raise PatchError("script left %d source line(s) unconsumed" % (len(a) - pos))
    return out
