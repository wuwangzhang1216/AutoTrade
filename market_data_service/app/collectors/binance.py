import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime
import logging

from ..models import OHLCV, Ticker24h, OrderBook

logger = logging.getLogger(__name__)


class BinanceCollector:
    """Binance数据采集器"""

    BASE_URL = "https://api.binance.com/api/v3"

    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def fetch_ticker_24h(self, symbol: str) -> Ticker24h:
        """获取24小时行情数据"""
        url = f"{self.BASE_URL}/ticker/24hr"
        params = {"symbol": symbol}

        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch ticker for {symbol}: {response.status}")
                    raise Exception(f"API error: {response.status}")

                data = await response.json()

                return Ticker24h(
                    symbol=data['symbol'],
                    price_change=float(data['priceChange']),
                    price_change_percent=float(data['priceChangePercent']),
                    weighted_avg_price=float(data['weightedAvgPrice']),
                    last_price=float(data['lastPrice']),
                    last_qty=float(data['lastQty']),
                    bid_price=float(data['bidPrice']),
                    ask_price=float(data['askPrice']),
                    open_price=float(data['openPrice']),
                    high_price=float(data['highPrice']),
                    low_price=float(data['lowPrice']),
                    volume=float(data['volume']),
                    quote_volume=float(data['quoteVolume']),
                    open_time=datetime.fromtimestamp(int(data['openTime']) / 1000),
                    close_time=datetime.fromtimestamp(int(data['closeTime']) / 1000),
                    count=int(data['count'])
                )
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            raise

    async def fetch_klines(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[OHLCV]:
        """获取K线数据

        Args:
            symbol: 交易对，如 BTCUSDT
            interval: 时间间隔 (1m, 5m, 15m, 1h, 4h, 1d)
            limit: 返回数量，默认100，最大1000
        """
        url = f"{self.BASE_URL}/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }

        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch klines for {symbol}: {response.status}")
                    raise Exception(f"API error: {response.status}")

                data = await response.json()

                ohlcv_list = []
                for kline in data:
                    ohlcv_list.append(OHLCV(
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(int(kline[0]) / 1000),
                        open=float(kline[1]),
                        high=float(kline[2]),
                        low=float(kline[3]),
                        close=float(kline[4]),
                        volume=float(kline[5])
                    ))

                return ohlcv_list

        except Exception as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            raise

    async def fetch_order_book(self, symbol: str, limit: int = 20) -> OrderBook:
        """获取订单簿数据

        Args:
            symbol: 交易对
            limit: 深度档位 (5, 10, 20, 50, 100, 500, 1000, 5000)
        """
        url = f"{self.BASE_URL}/depth"
        params = {
            "symbol": symbol,
            "limit": limit
        }

        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch order book for {symbol}: {response.status}")
                    raise Exception(f"API error: {response.status}")

                data = await response.json()

                return OrderBook(
                    bids=[[float(price), float(qty)] for price, qty in data['bids']],
                    asks=[[float(price), float(qty)] for price, qty in data['asks']],
                    timestamp=datetime.now()
                )

        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            raise

    async def fetch_latest_ohlcv(self, symbol: str) -> OHLCV:
        """获取最新K线数据（1分钟）"""
        klines = await self.fetch_klines(symbol, interval="1m", limit=1)
        if not klines:
            raise ValueError(f"No kline data for {symbol}")
        return klines[0]

    async def collect_all_symbols(self) -> Dict[str, Dict]:
        """采集所有交易对的数据"""
        tasks = []
        for symbol in self.symbols:
            tasks.append(self._collect_symbol_data(symbol))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        market_data = {}
        for i, result in enumerate(results):
            symbol = self.symbols[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to collect data for {symbol}: {result}")
                continue
            market_data[symbol] = result

        return market_data

    async def _collect_symbol_data(self, symbol: str) -> Dict:
        """采集单个交易对的完整数据"""
        try:
            # 并发获取多个数据
            ticker_task = self.fetch_ticker_24h(symbol)
            klines_task = self.fetch_klines(symbol, interval="1m", limit=100)
            order_book_task = self.fetch_order_book(symbol, limit=20)

            ticker, klines, order_book = await asyncio.gather(
                ticker_task,
                klines_task,
                order_book_task
            )

            # 最新的OHLCV
            latest_ohlcv = klines[-1] if klines else None

            return {
                "ticker": ticker,
                "latest_ohlcv": latest_ohlcv,
                "historical_klines": klines,
                "order_book": order_book
            }

        except Exception as e:
            logger.error(f"Error collecting data for {symbol}: {e}")
            raise
