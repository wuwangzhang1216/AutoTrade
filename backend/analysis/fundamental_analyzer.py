"""
Fundamental analyzer combining all data sources
"""
from typing import Dict, List, Optional
from datetime import datetime
from utils.logger import logger, log_error
from data.providers import (
    FearGreedProvider,
    # CoinGeckoProvider,  # REMOVED: CoinGecko no longer used
)


class FundamentalAnalyzer:
    """
    Aggregates and analyzes fundamental data from multiple sources
    """

    def __init__(self):
        """Initialize all fundamental data providers"""
        self.fear_greed = FearGreedProvider()
        # self.coingecko = CoinGeckoProvider()  # REMOVED: CoinGecko no longer used

        logger.info("Fundamental Analyzer initialized with Fear & Greed Index")

    def get_market_sentiment(self) -> Dict:
        """
        Get overall market sentiment

        Returns:
            Dict with market sentiment data
        """
        sentiment_data = {}

        # Fear & Greed Index
        fg_data = self.fear_greed.get_current_index()
        if fg_data:
            sentiment_data['fear_greed'] = {
                'value': fg_data['value'],
                'classification': fg_data['value_classification'],
                'interpretation': self.fear_greed.interpret_index(fg_data['value'])
            }

        # REMOVED: CoinGecko global market data no longer used
        # global_data = self.coingecko.get_global_data()
        # if global_data:
        #     sentiment_data['global_market'] = {
        #         'total_market_cap': global_data.get('total_market_cap'),
        #         'total_volume': global_data.get('total_volume'),
        #         'btc_dominance': global_data.get('btc_dominance'),
        #         'eth_dominance': global_data.get('eth_dominance'),
        #         'market_cap_change_24h': global_data.get('market_cap_change_24h'),
        #     }

        # REMOVED: CoinGecko trending coins no longer used
        # trending = self.coingecko.get_trending_coins()
        # if trending:
        #     sentiment_data['trending_coins'] = [
        #         {'symbol': coin['symbol'], 'name': coin['name']}
        #         for coin in trending[:5]
        #     ]

        return sentiment_data

    def get_coin_fundamentals(self, symbol: str) -> Dict:
        """
        Get comprehensive fundamental data for a coin

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC')

        Returns:
            Dict with fundamental data
        """
        fundamentals = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'sources': {}
        }

        # REMOVED: CoinGecko data no longer used
        # cg_data = self.coingecko.get_coin_data(symbol)
        # if cg_data:
        #     fundamentals['sources']['coingecko'] = {
        #         'market_cap_rank': cg_data.get('market_cap_rank'),
        #         'price_change_24h': cg_data.get('price_change_24h'),
        #         'price_change_7d': cg_data.get('price_change_7d'),
        #         'price_change_30d': cg_data.get('price_change_30d'),
        #         'market_cap': cg_data.get('market_cap'),
        #         'volume_24h': cg_data.get('total_volume'),
        #         'ath_change': cg_data.get('ath_change_percentage'),
        #         'sentiment_up': cg_data.get('sentiment_votes_up_percentage'),
        #         'sentiment_down': cg_data.get('sentiment_votes_down_percentage'),
        #     }

        return fundamentals

    def get_news_sentiment(self, currencies: str = "BTC,ETH") -> Dict:
        """
        Get news sentiment analysis

        Note: News sentiment feature removed to simplify dependencies.
        Returns empty dict for compatibility.

        Args:
            currencies: Comma-separated list of currencies

        Returns:
            Dict with news sentiment (empty for now)
        """
        return {}

    def get_comprehensive_analysis(self, symbol: str) -> Dict:
        """
        Get comprehensive fundamental analysis for a coin

        Args:
            symbol: Cryptocurrency symbol

        Returns:
            Dict with complete fundamental analysis
        """
        logger.info(f"Performing comprehensive fundamental analysis for {symbol}")

        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'market_sentiment': self.get_market_sentiment(),
            'coin_fundamentals': self.get_coin_fundamentals(symbol),
            'news_sentiment': self.get_news_sentiment(symbol),
        }

        # Calculate overall fundamental score (0-100)
        score = self._calculate_fundamental_score(analysis)
        analysis['fundamental_score'] = score
        analysis['recommendation'] = self._get_recommendation(score)

        logger.info(f"Fundamental score for {symbol}: {score}/100 ({analysis['recommendation']})")

        return analysis

    def _calculate_fundamental_score(self, analysis: Dict) -> float:
        """
        Calculate overall fundamental score

        Simplified version using only Fear & Greed Index.

        Args:
            analysis: Analysis data

        Returns:
            Score from 0-100
        """
        scores = []
        weights = []

        # Fear & Greed Index (weight: 1.0 - only data source now)
        fg_data = analysis.get('market_sentiment', {}).get('fear_greed')
        if fg_data:
            scores.append(fg_data['value'])
            weights.append(1.0)

        # REMOVED: CoinGecko data no longer used
        # # Price momentum from CoinGecko (weight: 0.3)
        # cg_data = analysis.get('coin_fundamentals', {}).get('sources', {}).get('coingecko', {})
        # if cg_data and cg_data.get('price_change_7d') is not None:
        #     # Convert percentage change to score
        #     price_change = cg_data['price_change_7d']
        #     # Normalize: -50% = 0, 0% = 50, +50% = 100
        #     price_score = min(max((price_change + 50) / 1.0, 0), 100)
        #     scores.append(price_score)
        #     weights.append(0.3)

        # # CoinGecko sentiment votes (weight: 0.2)
        # if cg_data and cg_data.get('sentiment_up') is not None:
        #     sentiment_score = cg_data['sentiment_up']  # Already 0-100
        #     scores.append(sentiment_score)
        #     weights.append(0.2)

        # Calculate weighted average
        if scores:
            total_weight = sum(weights)
            weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
            return round(weighted_score, 2)
        else:
            return 50.0  # Neutral if no data

    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on fundamental score"""
        if score >= 75:
            return "STRONG_BUY"
        elif score >= 60:
            return "BUY"
        elif score >= 40:
            return "HOLD"
        elif score >= 25:
            return "SELL"
        else:
            return "STRONG_SELL"


__all__ = ["FundamentalAnalyzer"]
