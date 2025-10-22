from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ..models import MarketData
from ..storage.redis_cache import RedisCache
from ..storage.timescale_db import TimescaleDB

logger = logging.getLogger(__name__)

router = APIRouter()

# These will be injected from main.py
redis_cache: Optional[RedisCache] = None
timescale_db: Optional[TimescaleDB] = None


def init_dependencies(cache: RedisCache, db: TimescaleDB):
    """Initialize dependencies for the router"""
    global redis_cache, timescale_db
    redis_cache = cache
    timescale_db = db


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "market_data", "timestamp": datetime.utcnow().isoformat()}


@router.get("/api/market/latest")
async def get_latest_market_snapshot():
    """
    Get latest market data snapshot for all symbols - REAL DATA
    """
    try:
        if redis_cache:
            snapshot = await redis_cache.get_market_snapshot()
            if snapshot:
                # Convert Pydantic model to dict
                snapshot_dict = snapshot.model_dump(mode='json') if hasattr(snapshot, 'model_dump') else snapshot.dict()
                logger.info(f"Returning market snapshot with {len(snapshot_dict.get('data', {}))} symbols")
                return snapshot_dict

        logger.warning("No market snapshot available in cache")
        raise HTTPException(
            status_code=404,
            detail="No market snapshot available. Service may still be initializing."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/market/{symbol}")
async def get_market_data(symbol: str):
    """
    Get current market data for a symbol - returns REAL data from cache
    """
    try:
        symbol = symbol.upper()

        # Map simple symbols to USDT pairs
        symbol_mapping = {
            'BTC': 'BTCUSDT',
            'ETH': 'ETHUSDT',
            'SOL': 'SOLUSDT',
            'BNB': 'BNBUSDT',
            'DOGE': 'DOGEUSDT',
            'XRP': 'XRPUSDT'
        }

        # Try both the provided symbol and the mapped version
        symbols_to_try = [symbol]
        if symbol in symbol_mapping:
            symbols_to_try.insert(0, symbol_mapping[symbol])

        # Get real data from Redis cache
        if redis_cache:
            for sym in symbols_to_try:
                try:
                    cached_data = await redis_cache.get_market_data(sym)
                    if cached_data:
                        logger.info(f"Found cached data for {sym} (requested as {symbol})")
                        # cached_data is a MarketData object with real market data
                        if hasattr(cached_data, 'ohlcv') and cached_data.ohlcv:
                            ohlcv = cached_data.ohlcv
                            logger.info(f"Returning market data: price={ohlcv.close}, volume={ohlcv.volume}")

                            # 优先使用ticker中的准确的24小时价格变化百分比
                            change_24h = 0.0
                            if hasattr(cached_data, 'ticker') and cached_data.ticker:
                                # 使用Binance提供的准确数据
                                change_24h = float(cached_data.ticker.price_change_percent)
                                logger.info(f"Using real 24h change from ticker: {change_24h}%")
                            else:
                                # 备用方案：尝试从历史价格计算
                                logger.warning(f"No ticker data for {sym}, calculating from history")
                                try:
                                    key_24h = f"price_24h_ago:{sym}"
                                    price_24h_ago_str = await redis_cache.redis.get(key_24h)

                                    if price_24h_ago_str:
                                        price_24h_ago = float(price_24h_ago_str)
                                        current_price = float(ohlcv.close)
                                        change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
                                    else:
                                        # 存储当前价格作为24小时前的参考
                                        await redis_cache.redis.setex(key_24h, 86400, str(ohlcv.close))
                                        change_24h = 0.0
                                except Exception as e:
                                    logger.debug(f"Error calculating 24h change: {e}")
                                    change_24h = 0.0

                            return {
                                "symbol": symbol,  # Return requested symbol, not full pair
                                "price": float(ohlcv.close),
                                "volume_24h": float(ohlcv.volume),
                                "change_24h": change_24h,
                                "timestamp": cached_data.timestamp.isoformat()
                            }
                        elif hasattr(cached_data, 'price'):
                            # Alternative format
                            return {
                                "symbol": symbol,
                                "price": float(cached_data.price),
                                "volume_24h": float(getattr(cached_data, 'volume', 0)),
                                "change_24h": float(getattr(cached_data, 'price_change_percent', 0)),
                                "timestamp": datetime.utcnow().isoformat()
                            }
                except Exception as e:
                    logger.debug(f"Symbol {sym} not in cache, trying next...")
                    continue

            logger.warning(f"No cached data found for {symbol} or mapped symbols")

        # If no cached data, return error - don't return fake data
        logger.error(f"No real data available for {symbol}")
        raise HTTPException(
            status_code=404,
            detail=f"No market data available for {symbol}. Service may still be initializing."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/indicators/{symbol}")
async def get_technical_indicators(symbol: str):
    """
    Get technical indicators for a symbol
    """
    try:
        symbol = symbol.upper()

        # Try to get from Redis cache
        if redis_cache:
            cached_indicators = await redis_cache.get(f"indicators:{symbol}")
            if cached_indicators:
                return cached_indicators

        # Return demo indicators if no real data
        return {
            "symbol": symbol,
            "rsi": 55.5,
            "macd": {
                "macd": 120.5,
                "signal": 115.3,
                "histogram": 5.2
            },
            "bollinger_bands": {
                "upper": 52000.0,
                "middle": 50000.0,
                "lower": 48000.0
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching indicators for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    interval: str = "1h",
    limit: int = 100
):
    """
    Get historical OHLCV data for a symbol
    """
    try:
        symbol = symbol.upper()

        if timescale_db:
            # Calculate time range based on interval and limit
            end_time = datetime.utcnow()

            # Map interval to timedelta
            interval_map = {
                "1m": timedelta(minutes=1),
                "5m": timedelta(minutes=5),
                "15m": timedelta(minutes=15),
                "1h": timedelta(hours=1),
                "4h": timedelta(hours=4),
                "1d": timedelta(days=1),
            }

            delta = interval_map.get(interval, timedelta(hours=1))
            start_time = end_time - (delta * limit)

            ohlcv_data = await timescale_db.get_ohlcv(
                symbol=symbol,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )

            if ohlcv_data:
                return [
                    {
                        "timestamp": candle.timestamp.isoformat(),
                        "open": float(candle.open),
                        "high": float(candle.high),
                        "low": float(candle.low),
                        "close": float(candle.close),
                        "volume": float(candle.volume)
                    }
                    for candle in ohlcv_data
                ]

        # Return empty array if no data
        return []

    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/symbols")
async def get_available_symbols():
    """
    Get list of available trading symbols
    """
    return {
        "symbols": ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"],
        "count": 6
    }
