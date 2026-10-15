"""Shared retry-with-exponential-backoff helper."""

from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


def retry_with_backoff(
    operation: Callable[[], T],
    *,
    max_attempts: int,
    base_delay: float,
    max_delay: float,
    sleep: Callable[[float], None],
) -> T:
    """Call ``operation`` up to ``max_attempts`` times and return the first success.

    Before the k-th retry (k = 1, 2, ...) this sleeps
    ``min(base_delay * 2 ** (k - 1), max_delay)`` seconds via ``sleep``.
    If every attempt raises an ``Exception``, the last exception is re-raised.
    """
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        if attempt > 0:
            # ``attempt`` is the retry number k (1-based) for this iteration.
            # Sleep lives outside the exception handler so sleep failures
            # propagate directly.
            sleep(min(base_delay * 2 ** (attempt - 1), max_delay))
        try:
            return operation()
        except Exception as exc:
            last_exc = exc
    assert last_exc is not None  # max_attempts >= 1 guarantees a captured error
    raise last_exc
