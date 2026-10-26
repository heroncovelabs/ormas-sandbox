"""Apply an edit script produced by ``textdiff/diff.py``."""


class PatchError(Exception):
    """Raised when an edit script does not apply cleanly to the given source."""


def apply(ops, a):
    """Apply edit script ``ops`` to list-of-lines ``a``, returning the result.

    "keep"/"del" ops must match the next line of ``a`` (else PatchError); "ins"
    ops add a line. Every line of ``a`` must be consumed (else PatchError).
    """
    src = list(a)
    cursor = 0
    result = []

    for op in ops:
        kind, line = op
        if kind == "ins":
            result.append(line)
        elif kind in ("keep", "del"):
            if cursor >= len(src) or src[cursor] != line:
                raise PatchError(
                    f"operation {kind!r} for line {line!r} does not match source "
                    f"at position {cursor}"
                )
            cursor += 1
            if kind == "keep":
                result.append(line)
        else:
            raise PatchError(f"unknown operation kind: {kind!r}")

    if cursor != len(src):
        raise PatchError(
            f"script consumed {cursor} of {len(src)} source lines"
        )

    return result
