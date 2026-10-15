import time


def retry_call(fn, *, max_attempts, base_delay, max_delay, sleep=time.sleep):
    last = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            if attempt + 1 < max_attempts:
                delay = min(base_delay * (2 ** attempt), max_delay)
                sleep(delay)
    raise last
