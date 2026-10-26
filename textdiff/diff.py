"""Compute a line-level diff between two sequences of lines.

``diff`` produces a minimal edit script — one whose ("keep", line) operations
form a longest common subsequence of the two inputs — made of
("keep"|"del"|"ins", line) operations, consumed by ``textdiff/patch.py``.
"""


def diff(a, b):
    """Return an edit script transforming list-of-lines ``a`` into ``b``.

    Each op is a tuple: ("keep", line) for a line common to both, ("del", line)
    for a line only in ``a``, ("ins", line) for a line only in ``b``. The kept
    lines must form a longest common subsequence of ``a`` and ``b``.
    """
    src = list(a)
    dst = list(b)
    n = len(src)
    m = len(dst)

    # lcs[i][j] = length of the longest common subsequence of src[i:] and dst[j:].
    lcs = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        row = lcs[i]
        below = lcs[i + 1]
        s = src[i]
        for j in range(m - 1, -1, -1):
            if s == dst[j]:
                row[j] = below[j + 1] + 1
            elif below[j] >= row[j + 1]:
                row[j] = below[j]
            else:
                row[j] = row[j + 1]

    ops = []
    i = 0
    j = 0
    while i < n and j < m:
        if src[i] == dst[j]:
            ops.append(("keep", src[i]))
            i += 1
            j += 1
        elif lcs[i + 1][j] >= lcs[i][j + 1]:
            # Deleting on ties keeps the output deterministic.
            ops.append(("del", src[i]))
            i += 1
        else:
            ops.append(("ins", dst[j]))
            j += 1

    while i < n:
        ops.append(("del", src[i]))
        i += 1
    while j < m:
        ops.append(("ins", dst[j]))
        j += 1

    return ops
