"""Compute a line-level diff between two sequences of lines.

``diff`` produces a minimal edit script (the kept lines form a longest common
subsequence of the inputs) made of ("keep"|"del"|"ins", line) operations,
consumed by ``textdiff/patch.py``.
"""


def diff(a, b):
    """Return an edit script transforming list-of-lines ``a`` into ``b``.

    Each op is a tuple: ("keep", line) for a line common to both, ("del", line)
    for a line only in ``a``, ("ins", line) for a line only in ``b``. The kept
    lines must form a longest common subsequence of ``a`` and ``b``.
    """
    n, m = len(a), len(b)

    # dp[i][j] = length of the LCS of a[i:] and b[j:].
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        below = dp[i + 1]
        row = dp[i]
        ai = a[i]
        for j in range(m - 1, -1, -1):
            if ai == b[j]:
                row[j] = below[j + 1] + 1
            else:
                down = below[j]
                right = row[j + 1]
                row[j] = down if down >= right else right

    # Walk the table from (0, 0), emitting ops in source order. On a tie
    # (dp[i+1][j] == dp[i][j+1]) prefer deleting, so deletions precede the
    # insertions they pair with.
    ops = []
    i = j = 0
    while i < n and j < m:
        if a[i] == b[j]:
            ops.append(("keep", a[i]))
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
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
