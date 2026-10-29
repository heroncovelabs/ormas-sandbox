"""Shared retry-with-exponential-backoff loop used by all resilient clients.

Contract:

* The operation is attempted up to ``max_attempts`` times in total: the first
  call plus up to ``max_attempts - 1`` retries.
* The result of the first successful call is returned immediately.
* Before the k-th retry (k = 1, 2, ...) the injected ``sleep`` is called with
  ``min(base_delay * 2 ** (k - 1), max_delay)`` seconds, so delays grow
  exponentially and never exceed ``max_delay``.
* Only ``Exception`` raised by the operation triggers a retry. ``sleep`` runs
  outside the exception handler, so it is never called while an operation
  exception is being handled.
* If every attempt fails, the last operation exception is re-raised.
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
    """Call ``operation`` with capped exponential backoff between attempts.

    Args:
        operation: Zero-argument callable to attempt.
        max_attempts: Total number of attempts, including the first call.
        base_delay: Delay in seconds before the first retry; doubles each retry.
        max_delay: Upper bound in seconds for any single delay.
        sleep: Callable used to wait between attempts (injectable for tests).

    Returns:
        The return value of the first successful ``operation()`` call.

    Raises:
        The last exception raised by ``operation`` once all attempts fail.
    """
    last_exc: Exception | None = None
    for retry_index in range(max_attempts):
        if retry_index > 0:
            sleep(min(base_delay * 2 ** (retry_index - 1), max_delay))
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 — retry on any operation failure
            last_exc = exc
    assert last_exc is not None
    raise last_exc
