"""Shared retry-with-exponential-backoff implementation."""
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
    """Run ``operation`` with capped exponential backoff between attempts.

    Return the first successful result, or re-raise the last exception after
    every attempt has failed.
    """
    last_exc: BaseException | None = None
    for attempt in range(max_attempts):
        if attempt > 0:
            delay = min(base_delay * 2 ** (attempt - 1), max_delay)
            sleep(delay)
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 — retry on any operation failure
            last_exc = exc

    assert last_exc is not None
    raise last_exc
