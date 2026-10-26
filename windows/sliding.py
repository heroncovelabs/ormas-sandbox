from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k."""
    n = len(nums)
    if k <= 0 or k > n:
        raise ValueError("k must satisfy 0 < k <= len(nums)")

    result = []
    candidates = deque()
    for i, value in enumerate(nums):
        # Drop indices that have fallen out of the current window.
        left = i - k + 1
        while candidates and candidates[0] < left:
            candidates.popleft()
        # Drop dominated candidates from the back.
        while candidates and nums[candidates[-1]] <= value:
            candidates.pop()
        candidates.append(i)
        if left >= 0:
            result.append(nums[candidates[0]])
    return result
