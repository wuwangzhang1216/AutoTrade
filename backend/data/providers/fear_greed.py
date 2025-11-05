"""
Fear & Greed Index provider
Source: Alternative.me API (free, no authentication required)
"""
import requests
from typing import Optional, Dict
from datetime import datetime
from utils.logger import logger, log_error
from utils.helpers import retry_on_failure
from data.cache_manager import FundamentalDataCache


class FearGreedProvider:
    """
    Fetches Crypto Fear & Greed Index
    """

    API_URL = "https://api.alternative.me/fng/"

    def __init__(self):
        self.cache = FundamentalDataCache()
        logger.info("Fear & Greed Provider initialized")

    @retry_on_failure(max_attempts=3)
    def get_current_index(self) -> Optional[Dict]:
        """
        Get current Fear & Greed Index

        Returns:
            Dict with index data or None
            {
                'value': 50,
                'value_classification': 'Neutral',
                'timestamp': datetime,
                'time_until_update': seconds
            }
        """
        # Check cache first
        cached_data = self.cache.get_fear_greed()
        if cached_data:
            logger.debug("Using cached Fear & Greed index")
            return cached_data

        try:
            response = requests.get(
                self.API_URL,
                params={'limit': 1},
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            if 'data' not in data or not data['data']:
                log_error("Invalid Fear & Greed API response")
                return None

            index_data = data['data'][0]

            result = {
                'value': int(index_data['value']),
                'value_classification': index_data['value_classification'],
                'timestamp': datetime.fromtimestamp(int(index_data['timestamp'])),
                'time_until_update': index_data.get('time_until_update', None)
            }

            # Cache the result
            self.cache.set_fear_greed(result)

            logger.info(f"Fear & Greed Index: {result['value']} ({result['value_classification']})")

            return result

        except requests.RequestException as e:
            log_error(f"Failed to fetch Fear & Greed Index: {e}")
            return None

    @retry_on_failure(max_attempts=3)
    def get_historical(self, limit: int = 30) -> Optional[list]:
        """
        Get historical Fear & Greed Index

        Args:
            limit: Number of historical data points (max 365)

        Returns:
            List of historical index data
        """
        try:
            response = requests.get(
                self.API_URL,
                params={'limit': min(limit, 365)},
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            if 'data' not in data:
                return None

            historical = []
            for item in data['data']:
                historical.append({
                    'value': int(item['value']),
                    'value_classification': item['value_classification'],
                    'timestamp': datetime.fromtimestamp(int(item['timestamp']))
                })

            logger.info(f"Fetched {len(historical)} historical Fear & Greed data points")

            return historical

        except requests.RequestException as e:
            log_error(f"Failed to fetch historical Fear & Greed Index: {e}")
            return None

    def interpret_index(self, value: int) -> Dict[str, str]:
        """
        Interpret Fear & Greed Index value

        Args:
            value: Index value (0-100)

        Returns:
            Dict with interpretation
        """
        if value <= 25:
            sentiment = "Extreme Fear"
            market_condition = "Potential buying opportunity"
            recommendation = "Market may be oversold"
        elif value <= 45:
            sentiment = "Fear"
            market_condition = "Cautious market"
            recommendation = "Consider accumulation"
        elif value <= 55:
            sentiment = "Neutral"
            market_condition = "Balanced market"
            recommendation = "Wait for clearer signals"
        elif value <= 75:
            sentiment = "Greed"
            market_condition = "Optimistic market"
            recommendation = "Consider taking profits"
        else:
            sentiment = "Extreme Greed"
            market_condition = "Potential selling opportunity"
            recommendation = "Market may be overbought"

        return {
            'sentiment': sentiment,
            'market_condition': market_condition,
            'recommendation': recommendation
        }


__all__ = ["FearGreedProvider"]
