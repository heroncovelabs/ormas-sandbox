"""Single shared retry-with-exponential-backoff implementation."""
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
    """Call ``operation`` up to ``max_attempts`` times; return its result.

    Before the k-th retry the client sleeps
    ``min(base_delay * 2 ** (k - 1), max_delay)`` seconds.  Re-raises the last
    exception if every attempt fails.
    """
    last_exc: BaseException | None = None
    for attempt in range(max_attempts):
        if attempt > 0:
            sleep(min(base_delay * 2 ** (attempt - 1), max_delay))
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 — retry on any operation failure
            last_exc = exc
    if last_exc is None:
        raise ValueError("max_attempts must be at least 1")
    raise last_exc
