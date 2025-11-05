"""
Utility helper functions for AutoTrade AI system
"""
import time
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
from utils.logger import logger


def retry_on_failure(max_attempts: int = 3, wait_min: int = 1, wait_max: int = 10):
    """
    Decorator to retry function on failure with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        wait_min: Minimum wait time between retries (seconds)
        wait_max: Maximum wait time between retries (seconds)
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=wait_min, max=wait_max),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError, TimeoutError)),
        reraise=True,
    )


def rate_limit(calls_per_minute: int):
    """
    Decorator to rate limit function calls

    Args:
        calls_per_minute: Maximum number of calls allowed per minute
    """
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait_time = min_interval - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
            last_called[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change between two values

    Args:
        old_value: Original value
        new_value: New value

    Returns:
        Percentage change
    """
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / abs(old_value)) * 100


def format_currency(amount: float, decimals: int = 2) -> str:
    """
    Format currency amount with proper separators

    Args:
        amount: Amount to format
        decimals: Number of decimal places

    Returns:
        Formatted string
    """
    return f"${amount:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2, show_sign: bool = True) -> str:
    """
    Format percentage value

    Args:
        value: Percentage value
        decimals: Number of decimal places
        show_sign: Whether to show +/- sign

    Returns:
        Formatted string
    """
    sign = "+" if value > 0 and show_sign else ""
    return f"{sign}{value:.{decimals}f}%"


def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    Convert Unix timestamp to datetime

    Args:
        timestamp: Unix timestamp in milliseconds

    Returns:
        datetime object
    """
    return datetime.fromtimestamp(timestamp / 1000)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    Convert datetime to Unix timestamp

    Args:
        dt: datetime object

    Returns:
        Unix timestamp in milliseconds
    """
    return int(dt.timestamp() * 1000)


def time_ago(dt: datetime) -> str:
    """
    Convert datetime to human-readable 'time ago' format

    Args:
        dt: datetime object

    Returns:
        Human-readable string (e.g., "2 hours ago")
    """
    now = datetime.now()
    diff = now - dt

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif diff < timedelta(days=30):
        weeks = int(diff.days / 7)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif diff < timedelta(days=365):
        months = int(diff.days / 30)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(diff.days / 365)
        return f"{years} year{'s' if years != 1 else ''} ago"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero

    Args:
        numerator: Top number
        denominator: Bottom number
        default: Default value if division fails

    Returns:
        Division result or default
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Clamp value between min and max

    Args:
        value: Value to clamp
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Clamped value
    """
    return max(min_value, min(value, max_value))


def parse_timeframe_to_minutes(timeframe: str) -> int:
    """
    Parse timeframe string to minutes

    Args:
        timeframe: Timeframe string (e.g., "5m", "1h", "1d")

    Returns:
        Number of minutes
    """
    unit = timeframe[-1]
    value = int(timeframe[:-1])

    if unit == "m":
        return value
    elif unit == "h":
        return value * 60
    elif unit == "d":
        return value * 1440
    elif unit == "w":
        return value * 10080
    else:
        raise ValueError(f"Unknown timeframe unit: {unit}")


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length

    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


class Timer:
    """Context manager for timing code execution"""

    def __init__(self, name: str = "Operation", log: bool = True):
        self.name = name
        self.log = log
        self.start_time = None
        self.end_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
        if self.log:
            logger.debug(f"{self.name} took {self.elapsed:.2f} seconds")


__all__ = [
    "retry_on_failure",
    "rate_limit",
    "calculate_percentage_change",
    "format_currency",
    "format_percentage",
    "timestamp_to_datetime",
    "datetime_to_timestamp",
    "time_ago",
    "safe_divide",
    "clamp",
    "parse_timeframe_to_minutes",
    "truncate_string",
    "Timer",
]
