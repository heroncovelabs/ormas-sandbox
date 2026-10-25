import time


def retry_call(fn, *, max_attempts, base_delay, max_delay, sleep=time.sleep):
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
            delay = min(base_delay * (2 ** attempt), max_delay)
            if delay > 0:
                sleep(delay)
    raise last
