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
    """Call ``operation`` up to ``max_attempts`` times with capped exponential backoff.

    The first call is made immediately. Before the k-th retry (k = 1, 2, ...)
    the helper sleeps ``min(base_delay * 2**(k-1), max_delay)`` seconds. The
    result of the first successful call is returned. If every attempt raises
    an ``Exception``, the last exception is re-raised.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 - retry on any Exception subclass
            last_exc = exc
        if attempt < max_attempts:
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            sleep(delay)

    assert last_exc is not None
    raise last_exc
