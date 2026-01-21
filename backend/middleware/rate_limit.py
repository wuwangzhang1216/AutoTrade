"""
Rate Limiting Middleware for AutoTrade AI API

Prevents API abuse by limiting request rates per client.
Uses slowapi which is built on top of limits library.
"""
import os
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from utils.logger import logger, log_warning

# Try to import slowapi, provide fallback if not installed
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    logger.warning(
        "slowapi not installed. Rate limiting is DISABLED. "
        "Install with: pip install slowapi"
    )
    # Provide dummy implementations
    RateLimitExceeded = Exception

    class Limiter:
        def __init__(self, *args, **kwargs):
            pass

        def limit(self, limit_string: str):
            def decorator(func):
                return func
            return decorator

        def shared_limit(self, limit_string: str, scope: str):
            def decorator(func):
                return func
            return decorator

    def get_remote_address(request: Request) -> str:
        return request.client.host if request.client else "unknown"


def get_real_client_ip(request: Request) -> str:
    """
    Get the real client IP address, considering proxies.

    Checks X-Forwarded-For and X-Real-IP headers for proxy scenarios.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address string
    """
    # Check for proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, get the first (original client)
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return "unknown"


def get_rate_limit_key(request: Request) -> str:
    """
    Generate a rate limit key based on client IP.

    Can be extended to use API key or user ID for authenticated requests.

    Args:
        request: FastAPI request object

    Returns:
        Rate limit key string
    """
    return get_real_client_ip(request)


# Default rate limits from environment or use defaults
DEFAULT_RATE_LIMIT = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
STRICT_RATE_LIMIT = os.getenv("RATE_LIMIT_STRICT", "30/minute")
RELAXED_RATE_LIMIT = os.getenv("RATE_LIMIT_RELAXED", "200/minute")

# Create limiter instance
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[DEFAULT_RATE_LIMIT],
    storage_uri=os.getenv("RATE_LIMIT_STORAGE", "memory://"),
    strategy="fixed-window",
)


def get_limiter() -> Limiter:
    """Get the global limiter instance."""
    return limiter


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.

    Provides informative error response with retry information.

    Args:
        request: FastAPI request object
        exc: RateLimitExceeded exception

    Returns:
        JSON response with error details
    """
    client_ip = get_real_client_ip(request)
    log_warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")

    # Get retry-after from exception if available
    retry_after = getattr(exc, "retry_after", 60)

    return JSONResponse(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please slow down.",
            "retry_after": retry_after,
            "detail": str(exc.detail) if hasattr(exc, "detail") else "Rate limit exceeded",
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(getattr(exc, "limit", DEFAULT_RATE_LIMIT)),
        },
    )


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Setup rate limiting for a FastAPI application.

    Args:
        app: FastAPI application instance
    """
    if not SLOWAPI_AVAILABLE:
        logger.warning("Rate limiting not set up - slowapi not available")
        return

    # Add limiter to app state
    app.state.limiter = limiter

    # Add exception handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    logger.info(f"Rate limiting enabled: default={DEFAULT_RATE_LIMIT}")


# Convenience decorators for different rate limit tiers
def default_limit():
    """Apply default rate limit."""
    return limiter.limit(DEFAULT_RATE_LIMIT)


def strict_limit():
    """Apply strict rate limit for sensitive endpoints."""
    return limiter.limit(STRICT_RATE_LIMIT)


def relaxed_limit():
    """Apply relaxed rate limit for public endpoints."""
    return limiter.limit(RELAXED_RATE_LIMIT)


__all__ = [
    "limiter",
    "get_limiter",
    "RateLimitExceeded",
    "rate_limit_exceeded_handler",
    "setup_rate_limiting",
    "default_limit",
    "strict_limit",
    "relaxed_limit",
    "get_real_client_ip",
    "SLOWAPI_AVAILABLE",
]
