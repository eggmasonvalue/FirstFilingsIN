import logging
import re
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception, before_sleep_log
from . import config

logger = logging.getLogger(__name__)

# Status codes to retry
RETRY_STATUS_CODES = {408, 429, 502, 503, 504}

def should_retry_exception(exception: Exception) -> bool:
    """
    Predicate to determine if an exception should trigger a retry.

    Retries on:
    - TimeoutError (client-side timeout)
    - ConnectionError IF the status code is in RETRY_STATUS_CODES (408, 429, 502, 503, 504)
    """
    if isinstance(exception, TimeoutError):
        return True

    if isinstance(exception, ConnectionError):
        msg = str(exception)
        # Check for status codes in the message
        # NSE format: "{url} {status_code}: {reason}"
        # BSE format: "{status_code}: {reason}"
        # Requests format often includes status code.

        # Regex to find a 3-digit number that looks like a status code
        # We look for our specific retry codes.
        for code in RETRY_STATUS_CODES:
            # Check for the code as a distinct word in the message
            if re.search(rf"\b{code}\b", msg):
                return True

        return False

    return False

def get_retry_decorator():
    """
    Returns a configured tenacity retry decorator.
    """
    return retry(
        stop=stop_after_attempt(config.TOTAL_RETRIES),
        wait=wait_random_exponential(multiplier=config.RETRY_MULTIPLIER, min=config.RETRY_MIN_DELAY, max=config.RETRY_MAX_DELAY),
        retry=retry_if_exception(should_retry_exception),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )

# Export a ready-to-use decorator
retry_exchange = get_retry_decorator()
