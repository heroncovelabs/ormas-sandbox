"""Apply an edit script produced by ``textdiff/diff.py``."""


class PatchError(Exception):
    """Raised when an edit script does not apply cleanly to the given source."""


def apply(ops, a):
    """Apply edit script ``ops`` to list-of-lines ``a``, returning the result.

    "keep"/"del" ops must match the next line of ``a`` (else PatchError); "ins"
    ops add a line. Every line of ``a`` must be consumed (else PatchError).
    """
    source = list(a)
    out = []
    cursor = 0
    for op in ops:
        kind, line = op
        if kind in ("keep", "del"):
            if cursor >= len(source):
                raise PatchError(
                    f"{kind!r} at source index {cursor}: source exhausted"
                )
            if source[cursor] != line:
                raise PatchError(
                    f"{kind!r} mismatch at source index {cursor}: "
                    f"expected {line!r}, found {source[cursor]!r}"
                )
            cursor += 1
            if kind == "keep":
                out.append(line)
        elif kind == "ins":
            out.append(line)
        else:
            raise PatchError(f"unknown op kind: {kind!r}")
    if cursor != len(source):
        raise PatchError(
            f"script consumed {cursor} of {len(source)} source lines"
        )
    return out
