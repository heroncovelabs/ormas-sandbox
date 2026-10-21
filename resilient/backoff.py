"""Shared retry-with-exponential-backoff loop used by the resilient clients.

Contract:
- The operation is attempted up to ``max_attempts`` times in total (the first
  call plus retries). The first successful result is returned immediately.
- Before the k-th retry (k = 1, 2, ...) the injected ``sleep`` is called with
  ``min(base_delay * 2 ** (k - 1), max_delay)`` seconds.
- ``sleep`` is called outside the operation's exception handler, so exceptions
  raised by ``sleep`` propagate unchanged.
- If every attempt raises, the last exception is re-raised.
"""

from typing import Callable, Optional, TypeVar

T = TypeVar("T")


def retry_with_backoff(
    operation: Callable[[], T],
    *,
    max_attempts: int,
    base_delay: float,
    max_delay: float,
    sleep: Callable[[float], None],
) -> T:
    last_exc: Optional[Exception] = None
    for attempt in range(max_attempts):
        if attempt > 0:
            delay = min(base_delay * 2 ** (attempt - 1), max_delay)
            sleep(delay)
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 - retry on any failure
            last_exc = exc
    assert last_exc is not None, "retry_with_backoff made no attempts"
    raise last_exc
