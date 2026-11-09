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
    result = []
    i = 0
    for op in ops:
        kind, line = op
        if kind == "ins":
            result.append(line)
            continue
        if kind not in ("keep", "del"):
            raise PatchError("unknown op kind: %r" % (kind,))
        if i >= len(a) or a[i] != line:
            raise PatchError("script does not match source at line %d" % i)
        if kind == "keep":
            result.append(line)
        i += 1
    if i != len(a):
        raise PatchError("source not fully consumed (%d of %d lines)" % (i, len(a)))
    return result
