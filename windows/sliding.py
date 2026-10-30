from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k.

    Uses a monotonic deque of indices whose values are decreasing, so the
    front always holds the index of the current window's maximum. Each index
    is pushed and popped at most once, giving O(n) total time.
    """
    n = len(nums)
    if k <= 0 or k > n:
        raise ValueError(f"k must satisfy 1 <= k <= len(nums); got k={k}, len={n}")

    result = []
    window = deque()  # indices into nums; values are strictly decreasing
    for i, value in enumerate(nums):
        # Drop the front index once it falls out of the current window.
        if window and window[0] <= i - k:
            window.popleft()
        # Drop smaller values from the back; they can never be a window max.
        while window and nums[window[-1]] <= value:
            window.pop()
        window.append(i)
        if i >= k - 1:
            result.append(nums[window[0]])
    return result
