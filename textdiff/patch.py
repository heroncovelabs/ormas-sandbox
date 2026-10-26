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
    a = list(a)
    out = []
    pos = 0
    for op in ops:
        kind, line = op
        if kind == "ins":
            out.append(line)
            continue
        if kind not in ("keep", "del"):
            raise PatchError("unknown op kind: %r" % (kind,))
        if pos >= len(a) or a[pos] != line:
            raise PatchError("script does not match source at line %d" % pos)
        pos += 1
        if kind == "keep":
            out.append(line)
    if pos != len(a):
        raise PatchError("script consumed %d of %d source lines" % (pos, len(a)))
    return out
