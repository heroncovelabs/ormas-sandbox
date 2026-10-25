"""Compute a minimal line-level edit script using a longest common subsequence."""


def diff(a, b):
    """Return an edit script transforming the lines in ``a`` into ``b``."""
    n, m = len(a), len(b)
    lengths = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if a[i] == b[j]:
                lengths[i][j] = lengths[i + 1][j + 1] + 1
            else:
                lengths[i][j] = max(lengths[i + 1][j], lengths[i][j + 1])

    ops = []
    i = j = 0
    while i < n and j < m:
        if a[i] == b[j]:
            ops.append(("keep", a[i]))
            i += 1
            j += 1
        elif lengths[i + 1][j] <= lengths[i][j + 1]:
            ops.append(("ins", b[j]))
            j += 1
        else:
            ops.append(("del", a[i]))
            i += 1

    while i < n:
        ops.append(("del", a[i]))
        i += 1
    while j < m:
        ops.append(("ins", b[j]))
        j += 1
    return ops
