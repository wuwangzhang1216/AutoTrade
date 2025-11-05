"""
LunarCrush API provider
Source: LunarCrush API (requires API key - free trial available)
"""
import requests
from typing import Optional, Dict
from utils.logger import logger, log_error
from utils.helpers import retry_on_failure, rate_limit
from config import settings
from data.cache_manager import FundamentalDataCache


class LunarCrushProvider:
    """
    Fetches social media analytics from LunarCrush
    """

    BASE_URL = "https://lunarcrush.com/api4/public"

    # Symbol mapping
    SYMBOL_MAP = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
        'BNB': 'binance-coin',
        'XRP': 'xrp',
        'ADA': 'cardano',
        'DOGE': 'dogecoin',
        'AVAX': 'avalanche',
        'DOT': 'polkadot',
        'MATIC': 'polygon',
    }

    def __init__(self):
        self.cache = FundamentalDataCache()
        self.api_key = settings.lunarcrush_api_key if settings else None

        if not self.api_key:
            logger.warning("LunarCrush API key not configured - functionality limited")

        self.headers = {
            'Authorization': f'Bearer {self.api_key}' if self.api_key else ''
        }

        logger.info("LunarCrush Provider initialized")

    def get_coin_slug(self, symbol: str) -> str:
        """Convert symbol to LunarCrush coin slug"""
        symbol = symbol.replace('/USDT', '').replace('USDT', '')
        return self.SYMBOL_MAP.get(symbol, symbol.lower())

    @rate_limit(calls_per_minute=20)
    @retry_on_failure(max_attempts=3)
    def get_coin_metrics(self, symbol: str) -> Optional[Dict]:
        """
        Get social metrics for a coin

        Args:
            symbol: Cryptocurrency symbol

        Returns:
            Dict with social metrics
        """
        if not self.api_key:
            logger.warning("LunarCrush API key not configured")
            return None

        coin_slug = self.get_coin_slug(symbol)

        # Check cache
        cached_data = self.cache.get_lunarcrush_data(coin_slug)
        if cached_data:
            logger.debug(f"Using cached LunarCrush data for {coin_slug}")
            return cached_data

        try:
            # Note: LunarCrush API v4 uses different endpoints
            # Using public endpoint (may have limitations)
            url = f"{self.BASE_URL}/coins/{coin_slug}/v1"

            response = requests.get(url, headers=self.headers, timeout=10)

            # If unauthorized, try without auth (public data)
            if response.status_code == 401:
                response = requests.get(url, timeout=10)

            response.raise_for_status()
            data = response.json()

            if 'data' not in data:
                log_error(f"Invalid LunarCrush response for {coin_slug}")
                return None

            coin_data = data['data']

            result = {
                'symbol': symbol,
                'name': coin_data.get('name'),
                'galaxy_score': coin_data.get('galaxy_score'),  # Overall score
                'alt_rank': coin_data.get('alt_rank'),  # Alternative rank
                'social_volume': coin_data.get('social_volume'),  # Social mentions
                'social_volume_24h_change': coin_data.get('social_volume_24h_change'),
                'social_score': coin_data.get('social_score'),
                'sentiment': coin_data.get('sentiment'),  # Overall sentiment
                'tweets_24h': coin_data.get('tweets_24h'),
                'reddit_posts_24h': coin_data.get('reddit_posts_24h'),
                'news_24h': coin_data.get('news_24h'),
                'social_dominance': coin_data.get('social_dominance'),
                'market_dominance': coin_data.get('market_dominance'),
            }

            # Cache the result
            self.cache.set_lunarcrush_data(coin_slug, result)

            logger.info(f"Fetched LunarCrush metrics for {coin_slug}")

            return result

        except requests.RequestException as e:
            log_error(f"Failed to fetch LunarCrush data for {coin_slug}: {e}")
            return None

    @rate_limit(calls_per_minute=20)
    @retry_on_failure(max_attempts=3)
    def get_trending_coins(self) -> Optional[list]:
        """
        Get trending coins based on social activity

        Returns:
            List of trending coins
        """
        if not self.api_key:
            logger.warning("LunarCrush API key not configured")
            return None

        try:
            url = f"{self.BASE_URL}/coins/list/v1"
            params = {
                'sort': 'social_volume',
                'limit': 10
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=10)

            # Try without auth if unauthorized
            if response.status_code == 401:
                response = requests.get(url, params=params, timeout=10)

            response.raise_for_status()
            data = response.json()

            trending = []
            for coin in data.get('data', []):
                trending.append({
                    'symbol': coin.get('symbol'),
                    'name': coin.get('name'),
                    'social_volume': coin.get('social_volume'),
                    'galaxy_score': coin.get('galaxy_score'),
                })

            logger.info(f"Fetched {len(trending)} trending coins from LunarCrush")

            return trending

        except requests.RequestException as e:
            log_error(f"Failed to fetch trending coins: {e}")
            return None


__all__ = ["LunarCrushProvider"]
