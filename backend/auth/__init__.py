"""
Authentication module for AutoTrade AI API
"""
from .api_key import (
    APIKeyAuth,
    get_api_key_auth,
    verify_api_key,
    create_api_key,
    API_KEY_HEADER,
)

__all__ = [
    "APIKeyAuth",
    "get_api_key_auth",
    "verify_api_key",
    "create_api_key",
    "API_KEY_HEADER",
]
