"""Apply an edit script produced by ``textdiff/diff.py``.

``apply`` walks the script against the source, validating that every
"keep"/"del" op matches the next unconsumed source line and that the script
consumes the source exactly.
"""


class PatchError(Exception):
    """Raised when an edit script does not apply cleanly to the given source."""


def apply(ops, a):
    """Apply edit script ``ops`` to list-of-lines ``a``, returning the result.

    "keep"/"del" ops must match the next line of ``a`` (else PatchError); "ins"
    ops add a line. Every line of ``a`` must be consumed (else PatchError).
    """
    result = []
    idx = 0
    n = len(a)
    for op in ops:
        kind, line = op[0], op[1]
        if kind == "ins":
            result.append(line)
        elif kind == "keep" or kind == "del":
            if idx >= n or a[idx] != line:
                raise PatchError(
                    "edit script expects %r at source line %d, found %r"
                    % (line, idx, a[idx] if idx < n else None)
                )
            if kind == "keep":
                result.append(line)
            idx += 1
        else:
            raise PatchError("unknown op kind: %r" % (kind,))
    if idx != n:
        raise PatchError(
            "edit script consumed %d of %d source lines" % (idx, n)
        )
    return result
