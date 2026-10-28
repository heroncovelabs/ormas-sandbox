"""Apply an edit script produced by ``textdiff/diff.py``."""


class PatchError(Exception):
    """Raised when an edit script does not apply cleanly to the given source."""


def apply(ops, a):
    """Apply edit script ``ops`` to list-of-lines ``a``, returning the result.

    "keep"/"del" ops must match the next line of ``a`` (else PatchError); "ins"
    ops add a line. Every line of ``a`` must be consumed (else PatchError).
    """
    source = list(a)
    result = []
    index = 0
    for op in ops:
        kind, line = op
        if kind == "ins":
            result.append(line)
        elif kind in ("keep", "del"):
            if index >= len(source) or source[index] != line:
                raise PatchError(
                    f"{kind!r} op for {line!r} does not match source at index {index}"
                )
            if kind == "keep":
                result.append(line)
            index += 1
        else:
            raise PatchError(f"unknown operation kind: {kind!r}")
    if index != len(source):
        raise PatchError(
            f"edit script consumed {index} of {len(source)} source lines"
        )
    return result
