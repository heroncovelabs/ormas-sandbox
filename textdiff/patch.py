"""Apply an edit script produced by ``textdiff/diff.py``."""


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
    for kind, line in ops:
        if kind == "ins":
            out.append(line)
        elif kind in ("keep", "del"):
            if pos >= len(a) or a[pos] != line:
                raise PatchError(
                    f"{kind} op {line!r} does not match source at line {pos}"
                )
            pos += 1
            if kind == "keep":
                out.append(line)
        else:
            raise PatchError(f"unknown op kind {kind!r}")
    if pos != len(a):
        raise PatchError(f"{len(a) - pos} source line(s) left unconsumed")
    return out
