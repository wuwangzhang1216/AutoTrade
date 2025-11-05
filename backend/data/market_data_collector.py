"""
Market data collector using CCXT
Fetches real-time prices and historical OHLCV data
"""
import ccxt
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from utils.logger import logger, log_error, log_success
from utils.helpers import retry_on_failure, Timer
from config import TradingPairsConfig


class MarketDataCollector:
    """
    Collects market data from cryptocurrency exchanges
    """

    def __init__(self, exchange_id: str = "kraken"):
        """
        Initialize market data collector

        Args:
            exchange_id: Exchange to use (default: kraken)
        """
        self.exchange_id = exchange_id

        try:
            # Initialize exchange (public API, no authentication needed)
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',  # Use futures for leverage trading
                }
            })

            log_success(f"Market Data Collector initialized with {exchange_id}")
            logger.info(f"Exchange: {self.exchange.name}")

        except Exception as e:
            log_error(f"Failed to initialize exchange: {e}")
            raise

    @retry_on_failure(max_attempts=3)
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Get current ticker data for a symbol

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")

        Returns:
            Ticker data dict or None if failed
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['baseVolume'],
                'quote_volume': ticker['quoteVolume'],
                'change_24h': ticker.get('percentage', 0),
                'timestamp': ticker['timestamp'],
            }
        except Exception as e:
            log_error(f"Failed to fetch ticker for {symbol}: {e}")
            return None

    @retry_on_failure(max_attempts=3)
    def get_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol (quick version)

        Args:
            symbol: Trading pair

        Returns:
            Current price or None
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            log_error(f"Failed to fetch price for {symbol}: {e}")
            return None

    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get prices for multiple symbols

        Args:
            symbols: List of trading pairs

        Returns:
            Dict of symbol -> price
        """
        prices = {}

        for symbol in symbols:
            price = self.get_price(symbol)
            if price is not None:
                prices[symbol] = price

        return prices

    @retry_on_failure(max_attempts=3)
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "15m",
        limit: int = 100,
        since: Optional[int] = None
    ) -> Optional[pd.DataFrame]:
        """
        Get OHLCV (candlestick) data

        Args:
            symbol: Trading pair
            timeframe: Timeframe (e.g., "5m", "15m", "1h", "4h", "1d")
            limit: Number of candles to fetch
            since: Start time in milliseconds (optional)

        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)

            if not ohlcv:
                logger.warning(f"No OHLCV data for {symbol}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            df['timeframe'] = timeframe

            return df

        except Exception as e:
            log_error(f"Failed to fetch OHLCV for {symbol}: {e}")
            return None

    def get_ohlcv_multi_timeframe(
        self,
        symbol: str,
        timeframes: List[str] = None,
        limit: int = 100
    ) -> Dict[str, pd.DataFrame]:
        """
        Get OHLCV data for multiple timeframes

        Args:
            symbol: Trading pair
            timeframes: List of timeframes
            limit: Number of candles per timeframe

        Returns:
            Dict of timeframe -> DataFrame
        """
        if timeframes is None:
            timeframes = TradingPairsConfig.TIMEFRAMES

        data = {}

        for tf in timeframes:
            df = self.get_ohlcv(symbol, timeframe=tf, limit=limit)
            if df is not None:
                data[tf] = df

        return data

    def get_market_overview(self, symbols: List[str] = None) -> pd.DataFrame:
        """
        Get market overview for multiple symbols

        Args:
            symbols: List of trading pairs (defaults to configured pairs)

        Returns:
            DataFrame with market overview
        """
        if symbols is None:
            symbols = TradingPairsConfig.DEFAULT_PAIRS

        overview_data = []

        with Timer(f"Fetching market overview for {len(symbols)} symbols", log=True):
            for symbol in symbols:
                ticker = self.get_ticker(symbol)
                if ticker:
                    overview_data.append(ticker)

        if not overview_data:
            logger.warning("No market overview data collected")
            return pd.DataFrame()

        df = pd.DataFrame(overview_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        return df

    @retry_on_failure(max_attempts=3)
    def get_orderbook(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """
        Get order book (depth) data

        Args:
            symbol: Trading pair
            limit: Number of bid/ask levels

        Returns:
            Order book data or None
        """
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit=limit)

            return {
                'symbol': symbol,
                'bids': orderbook['bids'],  # List of [price, amount]
                'asks': orderbook['asks'],
                'timestamp': orderbook['timestamp'],
                'bid_volume': sum(bid[1] for bid in orderbook['bids']),
                'ask_volume': sum(ask[1] for ask in orderbook['asks']),
            }

        except Exception as e:
            log_error(f"Failed to fetch orderbook for {symbol}: {e}")
            return None

    @retry_on_failure(max_attempts=3)
    def get_funding_rate(self, symbol: str) -> Optional[float]:
        """
        Get current funding rate for perpetual futures

        Args:
            symbol: Trading pair

        Returns:
            Funding rate or None
        """
        try:
            # Note: Not all exchanges support this
            funding = self.exchange.fetch_funding_rate(symbol)
            return funding.get('fundingRate', None)

        except Exception as e:
            logger.debug(f"Funding rate not available for {symbol}: {e}")
            return None

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str = "1h",
        days: int = 30
    ) -> Optional[pd.DataFrame]:
        """
        Get historical data for backtesting

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            days: Number of days of history

        Returns:
            DataFrame with historical data
        """
        try:
            # Calculate since timestamp
            since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

            all_data = []
            current_since = since

            # Fetch in batches (exchanges limit to ~1000 candles per request)
            while True:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=1000)

                if not ohlcv:
                    break

                all_data.extend(ohlcv)

                # Update since to last timestamp
                if len(ohlcv) < 1000:
                    break

                current_since = ohlcv[-1][0] + 1

            if not all_data:
                logger.warning(f"No historical data for {symbol}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(
                all_data,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            df['timeframe'] = timeframe

            # Remove duplicates
            df = df.drop_duplicates(subset=['timestamp']).reset_index(drop=True)

            log_success(f"Loaded {len(df)} candles for {symbol} ({timeframe})")

            return df

        except Exception as e:
            log_error(f"Failed to fetch historical data for {symbol}: {e}")
            return None

    def test_connection(self) -> bool:
        """
        Test exchange connection

        Returns:
            True if connection successful
        """
        try:
            # Try to fetch BTC/USDT price
            price = self.get_price("BTC/USDT")

            if price:
                log_success(f"Exchange connection test successful! BTC/USDT: ${price:,.2f}")
                return True
            else:
                log_error("Exchange connection test failed")
                return False

        except Exception as e:
            log_error(f"Exchange connection error: {e}")
            return False


# Convenience function
def create_collector(exchange_id: str = "kraken") -> MarketDataCollector:
    """
    Factory function to create market data collector

    Args:
        exchange_id: Exchange ID

    Returns:
        MarketDataCollector instance
    """
    return MarketDataCollector(exchange_id)


__all__ = ["MarketDataCollector", "create_collector"]
