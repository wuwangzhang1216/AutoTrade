"""
CryptoPanic API provider
Source: CryptoPanic API (requires API key - free tier available)
"""
import requests
from typing import Optional, List, Dict
from datetime import datetime
from utils.logger import logger, log_error
from utils.helpers import retry_on_failure, rate_limit
from config import settings
from data.cache_manager import FundamentalDataCache


class CryptoPanicProvider:
    """
    Fetches cryptocurrency news and sentiment from CryptoPanic
    """

    BASE_URL = "https://cryptopanic.com/api/v1"

    def __init__(self):
        self.cache = FundamentalDataCache()
        self.api_key = settings.cryptopanic_api_key if settings else None

        if not self.api_key:
            logger.warning("CryptoPanic API key not configured - functionality limited")

        logger.info("CryptoPanic Provider initialized")

    @rate_limit(calls_per_minute=60)
    @retry_on_failure(max_attempts=3)
    def get_news(
        self,
        currencies: str = "BTC,ETH",
        filter_type: str = "hot",
        limit: int = 20
    ) -> Optional[List[Dict]]:
        """
        Get cryptocurrency news

        Args:
            currencies: Comma-separated list of currencies
            filter_type: 'rising', 'hot', 'bullish', 'bearish', 'important', 'saved', 'lol'
            limit: Number of news items (max 20 without premium)

        Returns:
            List of news items
        """
        if not self.api_key:
            logger.warning("CryptoPanic API key not configured")
            return None

        # Check cache
        cache_key = f"{currencies}:{filter_type}"
        cached_data = self.cache.get_cryptopanic_news(cache_key)
        if cached_data:
            logger.debug(f"Using cached CryptoPanic news for {currencies}")
            return cached_data

        try:
            url = f"{self.BASE_URL}/posts/"
            params = {
                'auth_token': self.api_key,
                'currencies': currencies,
                'filter': filter_type,
                'public': 'true'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'results' not in data:
                log_error("Invalid CryptoPanic API response")
                return None

            news_items = []
            for item in data['results'][:limit]:
                news_items.append({
                    'title': item['title'],
                    'published_at': datetime.fromisoformat(item['published_at'].replace('Z', '+00:00')),
                    'url': item['url'],
                    'source': item['source']['title'],
                    'currencies': [c['code'] for c in item.get('currencies', [])],
                    'kind': item.get('kind'),  # news, media, tweet
                    'votes': {
                        'positive': item.get('votes', {}).get('positive', 0),
                        'negative': item.get('votes', {}).get('negative', 0),
                        'important': item.get('votes', {}).get('important', 0),
                        'liked': item.get('votes', {}).get('liked', 0),
                        'disliked': item.get('votes', {}).get('disliked', 0),
                        'lol': item.get('votes', {}).get('lol', 0),
                        'toxic': item.get('votes', {}).get('toxic', 0),
                    }
                })

            # Cache the result
            self.cache.set_cryptopanic_news(cache_key, news_items)

            logger.info(f"Fetched {len(news_items)} news items from CryptoPanic")

            return news_items

        except requests.RequestException as e:
            log_error(f"Failed to fetch CryptoPanic news: {e}")
            return None

    def analyze_sentiment(self, news_items: List[Dict]) -> Dict:
        """
        Analyze sentiment from news items

        Args:
            news_items: List of news items from get_news()

        Returns:
            Sentiment analysis
        """
        if not news_items:
            return {
                'sentiment_score': 0,
                'sentiment': 'Neutral',
                'bullish_count': 0,
                'bearish_count': 0,
                'important_count': 0
            }

        total_positive = 0
        total_negative = 0
        important_count = 0

        for item in news_items:
            votes = item.get('votes', {})
            total_positive += votes.get('positive', 0) + votes.get('liked', 0)
            total_negative += votes.get('negative', 0) + votes.get('disliked', 0)
            important_count += votes.get('important', 0)

        # Calculate sentiment score (-100 to 100)
        total_votes = total_positive + total_negative
        if total_votes > 0:
            sentiment_score = ((total_positive - total_negative) / total_votes) * 100
        else:
            sentiment_score = 0

        # Classify sentiment
        if sentiment_score > 20:
            sentiment = 'Bullish'
        elif sentiment_score < -20:
            sentiment = 'Bearish'
        else:
            sentiment = 'Neutral'

        return {
            'sentiment_score': round(sentiment_score, 2),
            'sentiment': sentiment,
            'bullish_count': total_positive,
            'bearish_count': total_negative,
            'important_count': important_count,
            'total_news': len(news_items)
        }


__all__ = ["CryptoPanicProvider"]
