"""Shared retry-with-exponential-backoff loop used by the resilient clients."""
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
    """Call ``operation`` up to ``max_attempts`` times and return its result.

    The first call is immediate. Before the k-th retry (k = 1, 2, ...) this
    sleeps ``min(base_delay * 2**(k-1), max_delay)`` seconds via ``sleep``.

    Exceptions of type ``Exception`` trigger a retry. If every attempt fails,
    the last exception is re-raised. Exceptions raised by ``sleep`` propagate.
    """
    last_exc: BaseException | None = None
    for attempt in range(max_attempts):
        if attempt > 0:
            sleep(min(base_delay * 2 ** (attempt - 1), max_delay))
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 — retry on any operation failure
            last_exc = exc
    assert last_exc is not None
    raise last_exc
