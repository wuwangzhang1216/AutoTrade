"""
CoinMarketCap API provider
Source: CoinMarketCap API (requires API key - free tier available)
"""
import requests
from typing import Optional, Dict, List
from utils.logger import logger, log_error
from utils.helpers import retry_on_failure, rate_limit
from config import settings
from data.cache_manager import FundamentalDataCache


class CoinMarketCapProvider:
    """
    Fetches cryptocurrency data from CoinMarketCap
    """

    BASE_URL = "https://pro-api.coinmarketcap.com/v1"

    def __init__(self):
        self.cache = FundamentalDataCache()
        self.api_key = settings.coinmarketcap_api_key if settings else None

        if not self.api_key:
            logger.warning("CoinMarketCap API key not configured - functionality limited")

        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key or '',
            'Accept': 'application/json'
        }

        logger.info("CoinMarketCap Provider initialized")

    @rate_limit(calls_per_minute=30)
    @retry_on_failure(max_attempts=3)
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get latest quote for a cryptocurrency

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC')

        Returns:
            Dict with quote data
        """
        if not self.api_key:
            logger.warning("CoinMarketCap API key not configured")
            return None

        # Remove /USDT suffix if present
        symbol = symbol.replace('/USDT', '').replace('USDT', '')

        # Check cache
        cached_data = self.cache.get_coinmarketcap_data(symbol)
        if cached_data:
            logger.debug(f"Using cached CoinMarketCap data for {symbol}")
            return cached_data

        try:
            url = f"{self.BASE_URL}/cryptocurrency/quotes/latest"
            params = {
                'symbol': symbol,
                'convert': 'USD'
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'data' not in data or symbol not in data['data']:
                log_error(f"Invalid CoinMarketCap response for {symbol}")
                return None

            coin_data = data['data'][symbol]
            quote = coin_data['quote']['USD']

            result = {
                'symbol': symbol,
                'name': coin_data['name'],
                'cmc_rank': coin_data.get('cmc_rank'),
                'price': quote.get('price'),
                'volume_24h': quote.get('volume_24h'),
                'volume_change_24h': quote.get('volume_change_24h'),
                'percent_change_1h': quote.get('percent_change_1h'),
                'percent_change_24h': quote.get('percent_change_24h'),
                'percent_change_7d': quote.get('percent_change_7d'),
                'percent_change_30d': quote.get('percent_change_30d'),
                'market_cap': quote.get('market_cap'),
                'market_cap_dominance': quote.get('market_cap_dominance'),
                'circulating_supply': coin_data.get('circulating_supply'),
                'total_supply': coin_data.get('total_supply'),
                'max_supply': coin_data.get('max_supply'),
            }

            # Cache the result
            self.cache.set_coinmarketcap_data(symbol, result)

            logger.info(f"Fetched CoinMarketCap quote for {symbol}")

            return result

        except requests.RequestException as e:
            log_error(f"Failed to fetch CoinMarketCap quote for {symbol}: {e}")
            return None

    @rate_limit(calls_per_minute=30)
    @retry_on_failure(max_attempts=3)
    def get_trending(self) -> Optional[List[Dict]]:
        """
        Get trending cryptocurrencies

        Returns:
            List of trending coins
        """
        if not self.api_key:
            return None

        try:
            url = f"{self.BASE_URL}/cryptocurrency/trending/latest"

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            trending = []
            for item in data.get('data', []):
                trending.append({
                    'symbol': item['symbol'],
                    'name': item['name'],
                    'cmc_rank': item.get('cmc_rank'),
                })

            logger.info(f"Fetched {len(trending)} trending coins from CoinMarketCap")

            return trending

        except requests.RequestException as e:
            log_error(f"Failed to fetch trending coins: {e}")
            return None

    @rate_limit(calls_per_minute=30)
    @retry_on_failure(max_attempts=3)
    def get_global_metrics(self) -> Optional[Dict]:
        """
        Get global market metrics

        Returns:
            Dict with global metrics
        """
        if not self.api_key:
            return None

        try:
            url = f"{self.BASE_URL}/global-metrics/quotes/latest"

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()['data']
            quote = data['quote']['USD']

            result = {
                'total_market_cap': quote.get('total_market_cap'),
                'total_volume_24h': quote.get('total_volume_24h'),
                'btc_dominance': data.get('btc_dominance'),
                'eth_dominance': data.get('eth_dominance'),
                'active_cryptocurrencies': data.get('active_cryptocurrencies'),
                'active_exchanges': data.get('active_exchanges'),
                'active_market_pairs': data.get('active_market_pairs'),
                'defi_volume_24h': data.get('defi_volume_24h'),
                'defi_market_cap': data.get('defi_market_cap'),
            }

            logger.info("Fetched global metrics from CoinMarketCap")

            return result

        except requests.RequestException as e:
            log_error(f"Failed to fetch global metrics: {e}")
            return None


__all__ = ["CoinMarketCapProvider"]
