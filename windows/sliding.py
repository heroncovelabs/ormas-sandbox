from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k."""
    if k <= 0 or k > len(nums):
        raise ValueError("k must satisfy 1 <= k <= len(nums)")

    # Monotonic deque of indices: values at these indices are in
    # decreasing order, and the front always holds the window maximum.
    dq = deque()
    result = []
    for i, value in enumerate(nums):
        # Drop indices that have slid out of the current window.
        while dq and dq[0] <= i - k:
            dq.popleft()
        # Drop indices whose values are <= the current value; they can
        # never be a maximum for any future window containing `value`.
        while dq and nums[dq[-1]] <= value:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result
