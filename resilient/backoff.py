"""The single shared retry-with-exponential-backoff loop.

Both :class:`~resilient.http_client.HttpClient` and
:class:`~resilient.db_client.DbClient` delegate here, so there is exactly one
implementation and the clients behave identically.
"""
from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


def backoff_delay(retry_index: int, *, base_delay: float, max_delay: float) -> float:
    """Delay slept before the k-th retry (``retry_index`` = k = 1, 2, ...).

    Exponential backoff ``base_delay * 2**(k-1)``, capped at ``max_delay``.
    """
    return min(base_delay * 2 ** (retry_index - 1), max_delay)


def retry_with_backoff(
    operation: Callable[[], T],
    *,
    max_attempts: int,
    base_delay: float,
    max_delay: float,
    sleep: Callable[[float], None],
) -> T:
    """Call ``operation`` up to ``max_attempts`` times; return its first result.

    The first call plus retries together make up ``max_attempts`` attempts.
    Before the k-th retry (k = 1, 2, ...) sleeps
    ``min(base_delay * 2**(k-1), max_delay)`` seconds via ``sleep``. If every
    attempt fails, the last exception is re-raised.
    """
    last_exc: BaseException | None = None
    for attempt in range(max_attempts):
        if attempt > 0:
            sleep(backoff_delay(attempt, base_delay=base_delay, max_delay=max_delay))
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 — retry on any operation failure
            last_exc = exc
    assert last_exc is not None
    raise last_exc
