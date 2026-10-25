"""Compute a line-level diff between two sequences of lines.

NOTE: diff is not implemented — see issue.md. It must produce a minimal edit
script (longest common subsequence of kept lines) made of ("keep"|"del"|"ins",
line) operations, consumed by ``textdiff/patch.py``.
"""


def diff(a, b):
    """Return an edit script transforming list-of-lines ``a`` into ``b``.

    Each op is a tuple: ("keep", line) for a line common to both, ("del", line)
    for a line only in ``a``, ("ins", line) for a line only in ``b``. The kept
    lines must form a longest common subsequence of ``a`` and ``b``.
    """
    a = list(a)
    b = list(b)
    n, m = len(a), len(b)

    # lcs[i][j] is the LCS length of a[i:] and b[j:]. Keeping the full
    # table lets us reconstruct a script without a separate backtrack pass.
    lcs = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if a[i] == b[j]:
                lcs[i][j] = lcs[i + 1][j + 1] + 1
            else:
                lcs[i][j] = max(lcs[i + 1][j], lcs[i][j + 1])

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

    ops.extend(("del", line) for line in a[i:])
    ops.extend(("ins", line) for line in b[j:])
    return ops
