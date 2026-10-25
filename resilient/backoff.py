"""Shared retry logic with capped exponential backoff."""
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
    """Return the first success, or re-raise the last operation failure."""
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
