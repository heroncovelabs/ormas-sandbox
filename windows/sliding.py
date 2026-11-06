from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k."""
    if k < 1 or k > len(nums):
        raise ValueError("k must be between 1 and len(nums)")
    result = []
    dq = deque()  # indices whose values are in decreasing order
    for i, value in enumerate(nums):
        while dq and dq[0] <= i - k:
            dq.popleft()
        while dq and nums[dq[-1]] <= value:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result
