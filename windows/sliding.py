from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k."""
    n = len(nums)
    if k <= 0 or k > n:
        raise ValueError("k must satisfy 0 < k <= len(nums)")

    result = []
    dq = deque()  # indices whose values are in decreasing order
    for i, value in enumerate(nums):
        while dq and nums[dq[-1]] <= value:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result
