from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k.

    Uses a monotonic deque of indices so each element is pushed and popped at
    most once, giving O(n) time overall.
    """
    n = len(nums)
    if k <= 0 or k > n:
        raise ValueError("k must satisfy 0 < k <= len(nums)")

    result = []
    dq = deque()  # indices, with nums values decreasing from left to right

    for i, value in enumerate(nums):
        # Drop indices that fell out of the window.
        left = i - k + 1
        while dq and dq[0] < left:
            dq.popleft()
        # Drop smaller values; they can never be the maximum again.
        while dq and nums[dq[-1]] <= value:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])

    return result
