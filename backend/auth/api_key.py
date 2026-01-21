"""
API Key Authentication for AutoTrade AI API

Provides simple API key-based authentication for protecting endpoints.
Supports both header-based and query parameter authentication.
"""
import os
import secrets
import hashlib
from typing import Optional, List
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, APIKeyQuery
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from utils.logger import logger, log_error, log_warning


# API Key header name
API_KEY_HEADER = "X-API-Key"

# Security schemes
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


def get_valid_api_keys() -> List[str]:
    """
    Get list of valid API keys from environment.

    Supports multiple keys separated by comma for key rotation.
    Keys are hashed for comparison to avoid timing attacks.

    Returns:
        List of valid API key hashes
    """
    api_keys_str = os.getenv("API_KEYS", "")

    if not api_keys_str:
        # If no API keys configured, check for single key
        single_key = os.getenv("API_KEY", "")
        if single_key:
            return [hash_api_key(single_key)]
        return []

    # Split multiple keys and hash each
    keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
    return [hash_api_key(k) for k in keys]


def hash_api_key(key: str) -> str:
    """
    Hash an API key for secure comparison.

    Args:
        key: Raw API key

    Returns:
        SHA-256 hash of the key
    """
    return hashlib.sha256(key.encode()).hexdigest()


def create_api_key(length: int = 32) -> str:
    """
    Generate a new secure API key.

    Args:
        length: Length of the key in bytes (default 32 = 64 hex chars)

    Returns:
        New API key string
    """
    return secrets.token_hex(length)


def verify_api_key(api_key: str) -> bool:
    """
    Verify an API key against valid keys.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        api_key: API key to verify

    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False

    valid_keys = get_valid_api_keys()

    if not valid_keys:
        # No keys configured - allow all requests (development mode)
        log_warning(
            "No API keys configured. API authentication is DISABLED. "
            "Set API_KEY or API_KEYS environment variable for production."
        )
        return True

    key_hash = hash_api_key(api_key)

    # Use constant-time comparison
    return any(secrets.compare_digest(key_hash, valid_hash) for valid_hash in valid_keys)


class APIKeyAuth:
    """
    API Key authentication dependency for FastAPI.

    Usage:
        from auth import APIKeyAuth

        auth = APIKeyAuth()

        @app.get("/protected")
        async def protected_endpoint(api_key: str = Depends(auth)):
            return {"message": "Authenticated!"}

        # Or for optional auth:
        auth_optional = APIKeyAuth(auto_error=False)

        @app.get("/optional")
        async def optional_auth(api_key: str = Depends(auth_optional)):
            if api_key:
                return {"authenticated": True}
            return {"authenticated": False}
    """

    def __init__(self, auto_error: bool = True):
        """
        Initialize API Key auth.

        Args:
            auto_error: If True, raise HTTPException on auth failure.
                       If False, return None for unauthenticated requests.
        """
        self.auto_error = auto_error

    async def __call__(
        self,
        api_key_header_value: Optional[str] = Security(api_key_header),
        api_key_query_value: Optional[str] = Security(api_key_query),
    ) -> Optional[str]:
        """
        Validate API key from header or query parameter.

        Args:
            api_key_header_value: API key from X-API-Key header
            api_key_query_value: API key from ?api_key= query param

        Returns:
            Validated API key or None

        Raises:
            HTTPException: If auto_error=True and authentication fails
        """
        # Try header first, then query parameter
        api_key = api_key_header_value or api_key_query_value

        if not api_key:
            if self.auto_error:
                logger.warning("API request without authentication")
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Missing API key. Provide via X-API-Key header or api_key query parameter.",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
            return None

        if not verify_api_key(api_key):
            log_error(f"Invalid API key attempt: {api_key[:8]}...")
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail="Invalid API key",
                )
            return None

        return api_key


def get_api_key_auth(auto_error: bool = True) -> APIKeyAuth:
    """
    Factory function to create APIKeyAuth instance.

    Args:
        auto_error: Whether to raise exception on auth failure

    Returns:
        APIKeyAuth instance
    """
    return APIKeyAuth(auto_error=auto_error)


# Pre-configured auth instances for convenience
require_api_key = APIKeyAuth(auto_error=True)
optional_api_key = APIKeyAuth(auto_error=False)


__all__ = [
    "APIKeyAuth",
    "get_api_key_auth",
    "verify_api_key",
    "create_api_key",
    "require_api_key",
    "optional_api_key",
    "API_KEY_HEADER",
]
