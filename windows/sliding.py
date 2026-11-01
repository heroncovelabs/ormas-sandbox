from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k."""
    n = len(nums)
    if k <= 0 or k > n:
        raise ValueError("k must satisfy 1 <= k <= len(nums)")
    dq = deque()
    out = []
    for i, x in enumerate(nums):
        while dq and nums[dq[-1]] <= x:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
        if i >= k - 1:
            out.append(nums[dq[0]])
    return out
