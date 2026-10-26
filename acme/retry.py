import time


def _backoff_delay(attempt, base_delay, max_delay):
    """Exponential backoff for a zero-based attempt index, capped at max_delay."""
    delay = base_delay * (2 ** attempt)
    if max_delay is not None:
        delay = min(delay, max_delay)
    return delay


def retry_call(fn, *, max_attempts, base_delay, max_delay, sleep=time.sleep):
    """Call ``fn`` up to ``max_attempts`` times, sleeping between attempts.

    Raises the last exception when every attempt fails.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    last = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            if attempt == max_attempts - 1:
                break
            sleep(_backoff_delay(attempt, base_delay, max_delay))
    raise last
