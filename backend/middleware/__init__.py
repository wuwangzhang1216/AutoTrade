"""
Middleware module for AutoTrade AI API
"""
from .rate_limit import (
    limiter,
    get_limiter,
    RateLimitExceeded,
    rate_limit_exceeded_handler,
    setup_rate_limiting,
)

__all__ = [
    "limiter",
    "get_limiter",
    "RateLimitExceeded",
    "rate_limit_exceeded_handler",
    "setup_rate_limiting",
]
