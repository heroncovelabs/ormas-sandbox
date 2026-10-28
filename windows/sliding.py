from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k."""
    n = len(nums)
    if k <= 0 or k > n:
        raise ValueError("k must satisfy 0 < k <= len(nums)")

    result = []
    # Holds indices of the current window; their values are strictly decreasing.
    candidates = deque()

    for i, value in enumerate(nums):
        # Drop indices that have fallen out of the window.
        leftmost = i - k + 1
        if candidates and candidates[0] < leftmost:
            candidates.popleft()

        # Drop indices whose values are dominated by the incoming value.
        while candidates and nums[candidates[-1]] <= value:
            candidates.pop()

        candidates.append(i)

        if i >= k - 1:
            result.append(nums[candidates[0]])

    return result
