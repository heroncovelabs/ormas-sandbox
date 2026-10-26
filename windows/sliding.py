from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k.

    Runs in O(n) time using a monotonic deque of indices whose values are
    decreasing from left to right.
    """
    n = len(nums)
    if k <= 0 or k > n:
        raise ValueError(f"window size k={k} must satisfy 0 < k <= {n}")

    result = []
    candidates = deque()

    for i, value in enumerate(nums):
        while candidates and nums[candidates[-1]] <= value:
            candidates.pop()
        candidates.append(i)

        while candidates[0] <= i - k:
            candidates.popleft()

        if i >= k - 1:
            result.append(nums[candidates[0]])

    return result
