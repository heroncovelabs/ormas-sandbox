from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k.

    Uses a monotonic deque of indices whose values are strictly decreasing,
    so every element is pushed and popped at most once: O(n) time overall.
    """
    n = len(nums)
    if k <= 0 or k > n:
        raise ValueError(f"k must satisfy 1 <= k <= len(nums); got k={k}, len={n}")

    result = []
    window = deque()  # indices into nums; values are decreasing front to back
    for i, value in enumerate(nums):
        # Drop indices that have left the current window.
        while window and window[0] <= i - k:
            window.popleft()
        # Drop smaller values; they can never be a window maximum again.
        while window and nums[window[-1]] <= value:
            window.pop()
        window.append(i)
        if i >= k - 1:
            result.append(nums[window[0]])
    return result
