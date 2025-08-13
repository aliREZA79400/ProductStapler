import functools
from typing import Callable, Any
import time


def async_time():
    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs) -> Any:
            print(f"Stratin {func} with args {args} {kwargs}")
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                end = time.time()
                total = end - start
                print(f"finsished {func} in {total:.4f} seconds")

        return wrapped

    return wrapper
