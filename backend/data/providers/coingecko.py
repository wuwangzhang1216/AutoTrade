"""
CoinGecko API provider
Source: CoinGecko API (free tier available)
"""
import requests
from typing import Optional, Dict, List
from utils.logger import logger, log_error
from utils.helpers import retry_on_failure, rate_limit
from config import settings
from data.cache_manager import FundamentalDataCache


class CoinGeckoProvider:
    """
    Fetches cryptocurrency data from CoinGecko
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    # Symbol to CoinGecko ID mapping
    SYMBOL_TO_ID = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
        'BNB': 'binancecoin',
        'XRP': 'ripple',
        'ADA': 'cardano',
        'DOGE': 'dogecoin',
        'AVAX': 'avalanche-2',
        'DOT': 'polkadot',
        'MATIC': 'matic-network',
    }

    def __init__(self):
        self.cache = FundamentalDataCache()
        self.api_key = settings.coingecko_api_key if settings else None

        self.headers = {}
        if self.api_key:
            self.headers['x-cg-demo-api-key'] = self.api_key

        logger.info("CoinGecko Provider initialized")

    def get_coin_id(self, symbol: str) -> str:
        """Convert symbol to CoinGecko coin ID"""
        # Remove /USDT suffix if present
        symbol = symbol.replace('/USDT', '').replace('USDT', '')
        return self.SYMBOL_TO_ID.get(symbol, symbol.lower())

    @rate_limit(calls_per_minute=50)
    @retry_on_failure(max_attempts=3)
    def get_coin_data(self, symbol: str) -> Optional[Dict]:
        """
        Get comprehensive coin data

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC')

        Returns:
            Dict with coin data
        """
        coin_id = self.get_coin_id(symbol)

        # Check cache
        cached_data = self.cache.get_coingecko_data(coin_id)
        if cached_data:
            logger.debug(f"Using cached CoinGecko data for {coin_id}")
            return cached_data

        try:
            url = f"{self.BASE_URL}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'community_data': 'true',
                'developer_data': 'true',
                'sparkline': 'false'
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract relevant data
            result = {
                'id': coin_id,
                'symbol': data['symbol'].upper(),
                'name': data['name'],
                'market_cap_rank': data.get('market_cap_rank'),
                'price_change_24h': data['market_data'].get('price_change_percentage_24h'),
                'price_change_7d': data['market_data'].get('price_change_percentage_7d'),
                'price_change_30d': data['market_data'].get('price_change_percentage_30d'),
                'market_cap': data['market_data'].get('market_cap', {}).get('usd'),
                'total_volume': data['market_data'].get('total_volume', {}).get('usd'),
                'circulating_supply': data['market_data'].get('circulating_supply'),
                'total_supply': data['market_data'].get('total_supply'),
                'ath': data['market_data'].get('ath', {}).get('usd'),
                'ath_change_percentage': data['market_data'].get('ath_change_percentage', {}).get('usd'),
                'atl': data['market_data'].get('atl', {}).get('usd'),
                'atl_change_percentage': data['market_data'].get('atl_change_percentage', {}).get('usd'),
                'sentiment_votes_up_percentage': data.get('sentiment_votes_up_percentage'),
                'sentiment_votes_down_percentage': data.get('sentiment_votes_down_percentage'),
            }

            # Cache the result
            self.cache.set_coingecko_data(coin_id, result)

            logger.info(f"Fetched CoinGecko data for {coin_id}")

            return result

        except requests.RequestException as e:
            log_error(f"Failed to fetch CoinGecko data for {coin_id}: {e}")
            return None

    @rate_limit(calls_per_minute=50)
    @retry_on_failure(max_attempts=3)
    def get_trending_coins(self) -> Optional[List[Dict]]:
        """
        Get trending coins

        Returns:
            List of trending coins
        """
        try:
            url = f"{self.BASE_URL}/search/trending"

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            trending = []
            for item in data.get('coins', []):
                coin = item['item']
                trending.append({
                    'id': coin['id'],
                    'symbol': coin['symbol'],
                    'name': coin['name'],
                    'market_cap_rank': coin.get('market_cap_rank'),
                    'score': coin.get('score', 0)
                })

            logger.info(f"Fetched {len(trending)} trending coins")

            return trending

        except requests.RequestException as e:
            log_error(f"Failed to fetch trending coins: {e}")
            return None

    @rate_limit(calls_per_minute=50)
    @retry_on_failure(max_attempts=3)
    def get_global_data(self) -> Optional[Dict]:
        """
        Get global cryptocurrency market data

        Returns:
            Dict with global market data
        """
        try:
            url = f"{self.BASE_URL}/global"

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()['data']

            result = {
                'total_market_cap': data.get('total_market_cap', {}).get('usd'),
                'total_volume': data.get('total_volume', {}).get('usd'),
                'market_cap_percentage': data.get('market_cap_percentage', {}),
                'market_cap_change_24h': data.get('market_cap_change_percentage_24h_usd'),
                'active_cryptocurrencies': data.get('active_cryptocurrencies'),
                'markets': data.get('markets'),
                'btc_dominance': data.get('market_cap_percentage', {}).get('btc'),
                'eth_dominance': data.get('market_cap_percentage', {}).get('eth'),
            }

            logger.info("Fetched global market data from CoinGecko")

            return result

        except requests.RequestException as e:
            log_error(f"Failed to fetch global market data: {e}")
            return None


__all__ = ["CoinGeckoProvider"]
