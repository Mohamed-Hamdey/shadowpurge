import asyncio
import time
from functools import wraps
from typing import Callable, Any, Optional, Type, Tuple
import logging

from shadowpurge.core.exceptions import NetworkError, RateLimitError

logger = logging.getLogger(__name__)


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (NetworkError,),
    on_retry: Optional[Callable] = None,
):
    """
    Retry decorator with exponential backoff for async functions.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Exception types to retry on
        on_retry: Optional callback called before each retry
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if on_retry:
                            try:
                                on_retry(attempt, e, current_delay)
                            except Exception:
                                pass
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} after {current_delay:.1f}s "
                            f"due to: {e}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} retries exhausted: {e}")
                        raise
                except Exception:
                    raise

            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def sync_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Synchronous retry decorator with exponential backoff.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} after {current_delay:.1f}s "
                            f"due to: {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} retries exhausted: {e}")
                        raise
            if last_exception:
                raise last_exception

        return wrapper

    return decorator
