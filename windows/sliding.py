"""Sliding-window maximum in O(n) time using a monotonic deque."""

from collections import deque


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k.

    Args:
        nums: Sequence of comparable values.
        k: Window length; must satisfy ``1 <= k <= len(nums)``.

    Returns:
        A list with ``len(nums) - k + 1`` entries, where entry ``i`` is
        ``max(nums[i:i+k])``.

    Raises:
        ValueError: If ``k <= 0`` or ``k > len(nums)``.

    The deque stores indices whose values are strictly decreasing, so the
    front of the deque is always the index of the current window's maximum.
    Each index is pushed and popped at most once, giving O(n) total time.
    """
    n = len(nums)
    if k <= 0 or k > n:
        raise ValueError(f"k must be in [1, {n}], got {k}")

    result = []
    # Deque of indices; nums[deque[0]] is the max of the current window.
    candidates = deque()

    for i, value in enumerate(nums):
        # Drop indices that have fallen out of the window.
        if candidates and candidates[0] <= i - k:
            candidates.popleft()
        # Drop smaller values dominated by the current one.
        while candidates and nums[candidates[-1]] <= value:
            candidates.pop()
        candidates.append(i)
        if i >= k - 1:
            result.append(nums[candidates[0]])

    return result
