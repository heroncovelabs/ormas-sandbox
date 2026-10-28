"""Compute a line-level diff between two sequences of lines.

``diff`` produces a minimal edit script (longest common subsequence of kept
lines) made of ("keep"|"del"|"ins", line) operations, consumed by
``textdiff/patch.py``.
"""


def diff(a, b):
    """Return an edit script transforming list-of-lines ``a`` into ``b``.

    Each op is a tuple: ("keep", line) for a line common to both, ("del", line)
    for a line only in ``a``, ("ins", line) for a line only in ``b``. The kept
    lines must form a longest common subsequence of ``a`` and ``b``.
    """
    n, m = len(a), len(b)

    # lcs[i][j] == length of the LCS of a[i:] and b[j:]
    lcs = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        row, next_row = lcs[i], lcs[i + 1]
        ai = a[i]
        for j in range(m - 1, -1, -1):
            if ai == b[j]:
                row[j] = next_row[j + 1] + 1
            else:
                row[j] = next_row[j] if next_row[j] >= row[j + 1] else row[j + 1]

    ops = []
    i = j = 0
    while i < n and j < m:
        if a[i] == b[j]:
            ops.append(("keep", a[i]))
            i += 1
            j += 1
        elif lcs[i + 1][j] >= lcs[i][j + 1]:
            ops.append(("del", a[i]))
            i += 1
        else:
            ops.append(("ins", b[j]))
            j += 1
    while i < n:
        ops.append(("del", a[i]))
        i += 1
    while j < m:
        ops.append(("ins", b[j]))
        j += 1

    return ops
