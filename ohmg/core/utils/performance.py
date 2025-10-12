from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def time_this_function(func):
    def wrapper_function(*args, **kwargs):
        start = datetime.now()
        result = func(*args, **kwargs)
        logger.debug(
            f"{func.__module__} {func.__qualname__} elapsed time: {datetime.now() - start}"
        )
        return result

    return wrapper_function
