"""Shared retry-with-exponential-backoff helper.

This is the single implementation used by all clients that retry operations.
"""
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
    """Call ``operation`` up to ``max_attempts`` times and return its first success.

    The first call is attempted immediately. Before the k-th retry (k = 1, 2, ...)
    the helper calls ``sleep(min(base_delay * 2 ** (k - 1), max_delay))``.

    If every attempt raises ``Exception``, the last exception is re-raised.
    """
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        if attempt > 0:
            sleep(min(base_delay * 2 ** (attempt - 1), max_delay))
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 — retry on any operation failure
            last_exc = exc
    assert last_exc is not None
    raise last_exc
