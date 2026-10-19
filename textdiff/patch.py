"""Apply an edit script produced by ``textdiff/diff.py``.

NOTE: apply is not implemented — see issue.md.
"""


class PatchError(Exception):
    """Raised when an edit script does not apply cleanly to the given source."""


def apply(ops, a):
    """Apply edit script ``ops`` to list-of-lines ``a``, returning the result.

    "keep"/"del" ops must match the next line of ``a`` (else PatchError); "ins"
    ops add a line. Every line of ``a`` must be consumed (else PatchError).
    """
    out = []
    pos = 0
    for kind, line in ops:
        if kind == "ins":
            out.append(line)
        elif kind in ("keep", "del"):
            if pos >= len(a) or a[pos] != line:
                raise PatchError("%s %r does not match source at line %d" % (kind, line, pos))
            pos += 1
            if kind == "keep":
                out.append(line)
        else:
            raise PatchError("unknown op kind %r" % (kind,))
    if pos != len(a):
        raise PatchError("script did not consume all of source")
    return out
