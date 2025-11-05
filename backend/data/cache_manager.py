"""
Cache manager for storing and retrieving data
Reduces API calls and improves performance
"""
import json
import pickle
from pathlib import Path
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
from diskcache import Cache
from utils.logger import logger
from config import DirectoryConfig


class CacheManager:
    """
    Manages caching of API responses and computed data
    """

    def __init__(self, cache_dir: Optional[Path] = None, default_ttl: int = 1800):
        """
        Initialize cache manager

        Args:
            cache_dir: Directory for cache storage
            default_ttl: Default time-to-live in seconds (default: 30 minutes)
        """
        if cache_dir is None:
            DirectoryConfig.create_directories()
            cache_dir = DirectoryConfig.CACHE_DIR

        self.cache_dir = cache_dir
        self.default_ttl = default_ttl

        # Create disk cache
        self.cache = Cache(str(cache_dir))

        logger.info(f"Cache Manager initialized at {cache_dir}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        try:
            value = self.cache.get(key)
            if value is not None:
                logger.debug(f"Cache HIT: {key}")
            else:
                logger.debug(f"Cache MISS: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = default)
        """
        try:
            if ttl is None:
                ttl = self.default_ttl

            self.cache.set(key, value, expire=ttl)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")

        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")

    def delete(self, key: str):
        """Delete key from cache"""
        try:
            self.cache.delete(key)
            logger.debug(f"Cache DELETE: {key}")
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")

    def clear(self):
        """Clear all cache"""
        try:
            self.cache.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        return key in self.cache

    def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            return {
                'size': len(self.cache),
                'volume': self.cache.volume(),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}


# Global cache instance
_global_cache = None


def get_cache() -> CacheManager:
    """
    Get global cache instance (singleton)

    Returns:
        CacheManager instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache


def cached(ttl: int = 1800, key_prefix: str = ""):
    """
    Decorator to cache function results

    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache key

    Example:
        @cached(ttl=3600, key_prefix="price")
        def get_price(symbol):
            return fetch_price_from_api(symbol)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()

            # Create cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]

            # Add args to key
            if args:
                key_parts.extend([str(arg) for arg in args])

            # Add kwargs to key
            if kwargs:
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])

            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Compute and cache
            result = func(*args, **kwargs)
            if result is not None:
                cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


class FundamentalDataCache:
    """
    Specialized cache for fundamental data
    Handles different expiry times for different data sources
    """

    def __init__(self):
        self.cache = get_cache()

        # Cache TTL for different data sources (in seconds)
        self.ttl_config = {
            'fear_greed': 3600,        # 1 hour
            'coingecko': 1800,         # 30 minutes
            'coinmarketcap': 1800,     # 30 minutes
            'cryptopanic': 900,        # 15 minutes
            'lunarcrush': 3600,        # 1 hour
        }

    def get_fear_greed(self) -> Optional[dict]:
        """Get cached Fear & Greed index"""
        return self.cache.get("fundamental:fear_greed")

    def set_fear_greed(self, data: dict):
        """Cache Fear & Greed index"""
        self.cache.set("fundamental:fear_greed", data, ttl=self.ttl_config['fear_greed'])

    def get_coingecko_data(self, coin_id: str) -> Optional[dict]:
        """Get cached CoinGecko data"""
        return self.cache.get(f"fundamental:coingecko:{coin_id}")

    def set_coingecko_data(self, coin_id: str, data: dict):
        """Cache CoinGecko data"""
        self.cache.set(f"fundamental:coingecko:{coin_id}", data, ttl=self.ttl_config['coingecko'])

    def get_coinmarketcap_data(self, symbol: str) -> Optional[dict]:
        """Get cached CoinMarketCap data"""
        return self.cache.get(f"fundamental:coinmarketcap:{symbol}")

    def set_coinmarketcap_data(self, symbol: str, data: dict):
        """Cache CoinMarketCap data"""
        self.cache.set(f"fundamental:coinmarketcap:{symbol}", data, ttl=self.ttl_config['coinmarketcap'])

    def get_cryptopanic_news(self, currencies: str = "BTC,ETH") -> Optional[list]:
        """Get cached CryptoPanic news"""
        return self.cache.get(f"fundamental:cryptopanic:{currencies}")

    def set_cryptopanic_news(self, currencies: str, data: list):
        """Cache CryptoPanic news"""
        self.cache.set(f"fundamental:cryptopanic:{currencies}", data, ttl=self.ttl_config['cryptopanic'])

    def get_lunarcrush_data(self, symbol: str) -> Optional[dict]:
        """Get cached LunarCrush data"""
        return self.cache.get(f"fundamental:lunarcrush:{symbol}")

    def set_lunarcrush_data(self, symbol: str, data: dict):
        """Cache LunarCrush data"""
        self.cache.set(f"fundamental:lunarcrush:{symbol}", data, ttl=self.ttl_config['lunarcrush'])


__all__ = [
    "CacheManager",
    "FundamentalDataCache",
    "get_cache",
    "cached",
]
