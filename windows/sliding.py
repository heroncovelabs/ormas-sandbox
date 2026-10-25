from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k.

    Uses a monotonic deque of indices (values strictly decreasing from front
    to back), so each element is pushed and popped at most once: O(n) total.
    """
    n = len(nums)
    if k <= 0 or k > n:
        raise ValueError(f"k must satisfy 1 <= k <= len(nums); got k={k}, len={n}")

    result = []
    dq = deque()
    for i, value in enumerate(nums):
        # Drop the front index once it has slid out of the window.
        if dq and dq[0] <= i - k:
            dq.popleft()
        # Discard smaller values from the back; they can never be a max again.
        while dq and nums[dq[-1]] <= value:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result
