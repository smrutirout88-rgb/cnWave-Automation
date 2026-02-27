import time
import random
import functools


def retry(max_attempts=5, base_delay=2):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            delay = base_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):

                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    if attempt == max_attempts:
                        raise

                    sleep_time = delay + random.uniform(0, 1)

                    # Optional: log if logger available
                    if args and hasattr(args[0], "logger"):
                        args[0].logger.warning(
                            f"Retry {attempt}/{max_attempts} "
                            f"after error: {str(e)}. "
                            f"Sleeping {sleep_time:.2f}s"
                        )

                    time.sleep(sleep_time)
                    delay *= 2

            raise last_exception

        return wrapper

    return decorator

