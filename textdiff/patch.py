"""Apply an edit script produced by ``textdiff/diff.py`` to a validated source."""


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
                raise PatchError(f"Source mismatch at line {index}")
            index += 1
            if kind == "keep":
                result.append(line)
        else:
            raise PatchError(f"Unknown operation kind: {kind!r}")

    if index != len(a):
        raise PatchError(f"Unconsumed source starting at line {index}")
    return result
