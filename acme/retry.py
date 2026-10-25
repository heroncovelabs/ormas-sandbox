import time


def retry_call(fn, *, max_attempts, base_delay, max_delay, sleep=time.sleep):
    last = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            if attempt == max_attempts - 1:
                break
            delay = min(max_delay, base_delay * (2 ** attempt))
            sleep(delay)
    raise last
