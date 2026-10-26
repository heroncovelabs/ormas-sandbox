"""HTTP client that retries via the shared backoff helper."""
from __future__ import annotations

import time
from typing import Callable, TypeVar

from resilient.backoff import retry_with_backoff

T = TypeVar("T")


class HttpClient:
    """Calls an operation, retrying with exponential backoff on failure."""

    def __init__(
        self,
        *,
        max_attempts: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 2.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._sleep = sleep

    def request_with_retry(self, operation: Callable[[], T]) -> T:
        """Call ``operation`` up to ``max_attempts`` times; return its result.

        Re-raises the last exception if every attempt fails.
        """
        return retry_with_backoff(
            operation,
            max_attempts=self.max_attempts,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            sleep=self._sleep,
        )
