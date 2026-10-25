import collections


def max_sliding_window(nums, k):
    """Return the maximum of each contiguous window of size k.

    Uses a monotonic deque of indices whose corresponding values are strictly
    decreasing from front to back. Each index enters and leaves the deque at
    most once, so the whole scan is O(n) time and O(k) space.
    """
    try:
        n = len(nums)
    except TypeError:
        nums = list(nums)
        n = len(nums)

    if k <= 0 or k > n:
        raise ValueError(
            f"window size k must satisfy 0 < k <= {n}, got {k}"
        )

    result = []
    # deque holds indices; values at those indices decrease front -> back.
    dq = collections.deque()
    append = dq.append
    pop = dq.pop
    popleft = dq.popleft

    for i, value in enumerate(nums):
        # Evict indices that fall out of the current window.
        left = i - k + 1
        while dq and dq[0] < left:
            popleft()
        # Drop dominated candidates from the back.
        while dq and nums[dq[-1]] <= value:
            pop()
        append(i)
        if left >= 0:
            result.append(nums[dq[0]])

    return result
