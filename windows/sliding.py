from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k."""
    if k <= 0 or k > len(nums):
        raise ValueError("k must be between 1 and len(nums)")

    maxima = []
    candidates = deque()

    for i, value in enumerate(nums):
        if candidates and candidates[0] <= i - k:
            candidates.popleft()

        while candidates and nums[candidates[-1]] <= value:
            candidates.pop()
        candidates.append(i)

        if i >= k - 1:
            maxima.append(nums[candidates[0]])

    return maxima
