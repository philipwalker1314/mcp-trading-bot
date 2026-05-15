import asyncio
from collections.abc import Callable
from functools import wraps

from app.logger import get_logger

logger = get_logger("retries")


def async_retry(
    retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
):
    """
    Async retry decorator.
    """

    def decorator(function: Callable):

        @wraps(function)
        async def wrapper(*args, **kwargs):

            last_exception = None

            for attempt in range(1, retries + 1):
                try:
                    return await function(*args, **kwargs)

                except exceptions as error:
                    last_exception = error

                    logger.warning(
                        "retry_attempt_failed",
                        function=function.__name__,
                        attempt=attempt,
                        retries=retries,
                        error=str(error),
                    )

                    if attempt < retries:
                        await asyncio.sleep(delay)

            logger.error(
                "retry_exhausted",
                function=function.__name__,
                error=str(last_exception),
            )

            raise last_exception

        return wrapper

    return decorator
