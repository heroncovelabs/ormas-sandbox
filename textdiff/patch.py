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
    result = []
    source_index = 0

    for op in ops:
        try:
            kind, line = op
        except (TypeError, ValueError) as exc:
            raise PatchError("invalid edit operation") from exc

        if kind == "ins":
            result.append(line)
            continue
        if kind not in {"keep", "del"}:
            raise PatchError(f"unknown edit operation: {kind!r}")
        if source_index >= len(a) or a[source_index] != line:
            raise PatchError("edit script does not match the source")

        source_index += 1
        if kind == "keep":
            result.append(line)

    if source_index != len(a):
        raise PatchError("edit script did not consume the entire source")
    return result
