from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k.

    Runs in O(n) time using a monotonic deque of indices whose values are
    in decreasing order; each index is pushed and popped at most once.
    """
    if k <= 0 or k > len(nums):
        raise ValueError(f"k must satisfy 1 <= k <= len(nums), got k={k}")
    result = []
    window = deque()  # indices into nums; values strictly decreasing
    for i, value in enumerate(nums):
        if window and window[0] <= i - k:
            window.popleft()
        while window and nums[window[-1]] <= value:
            window.pop()
        window.append(i)
        if i >= k - 1:
            result.append(nums[window[0]])
    return result
