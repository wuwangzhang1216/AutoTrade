import json
import redis.asyncio as redis
from typing import Optional, Dict, List
from datetime import timedelta
import logging

from ..models import MarketSnapshot, OHLCV, MarketData

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis缓存管理"""

    def __init__(self, host: str, port: int, db: int):
        self.redis: Optional[redis.Redis] = None
        self.host = host
        self.port = port
        self.db = db

    async def connect(self):
        """连接Redis"""
        self.redis = await redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            decode_responses=True
        )
        logger.info(f"Connected to Redis at {self.host}:{self.port}")

    async def close(self):
        """关闭连接"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def set_market_snapshot(
        self,
        snapshot: MarketSnapshot,
        ttl: int = 60
    ):
        """缓存市场快照

        Args:
            snapshot: 市场快照
            ttl: 过期时间（秒）
        """
        try:
            key = "market:snapshot:latest"
            value = snapshot.model_dump_json()
            await self.redis.setex(key, ttl, value)
            logger.debug(f"Cached market snapshot with {len(snapshot.data)} symbols")
        except Exception as e:
            logger.error(f"Error caching market snapshot: {e}")

    async def get_market_snapshot(self) -> Optional[MarketSnapshot]:
        """获取最新市场快照"""
        try:
            key = "market:snapshot:latest"
            value = await self.redis.get(key)
            if value:
                return MarketSnapshot.model_validate_json(value)
            return None
        except Exception as e:
            logger.error(f"Error getting market snapshot: {e}")
            return None

    async def cache_ohlcv(self, symbol: str, ohlcv: OHLCV, ttl: int = 300):
        """缓存OHLCV数据

        Args:
            symbol: 交易对
            ohlcv: OHLCV数据
            ttl: 过期时间（秒）
        """
        try:
            key = f"ohlcv:{symbol}:latest"
            await self.redis.setex(
                key,
                ttl,
                ohlcv.model_dump_json()
            )
        except Exception as e:
            logger.error(f"Error caching OHLCV for {symbol}: {e}")

    async def get_ohlcv(self, symbol: str) -> Optional[OHLCV]:
        """获取缓存的OHLCV数据"""
        try:
            key = f"ohlcv:{symbol}:latest"
            value = await self.redis.get(key)
            if value:
                return OHLCV.model_validate_json(value)
            return None
        except Exception as e:
            logger.error(f"Error getting OHLCV for {symbol}: {e}")
            return None

    async def push_price_history(self, symbol: str, ohlcv: OHLCV, max_length: int = 1000):
        """推送价格历史到列表（用于技术指标计算）

        Args:
            symbol: 交易对
            ohlcv: OHLCV数据
            max_length: 最大保留长度
        """
        try:
            key = f"history:{symbol}"
            # 左侧推入（最新的在前面）
            await self.redis.lpush(key, ohlcv.model_dump_json())
            # 保持列表长度
            await self.redis.ltrim(key, 0, max_length - 1)
        except Exception as e:
            logger.error(f"Error pushing price history for {symbol}: {e}")

    async def get_price_history(
        self,
        symbol: str,
        limit: int = 100
    ) -> List[OHLCV]:
        """获取价格历史（用于指标计算）

        Args:
            symbol: 交易对
            limit: 获取数量

        Returns:
            OHLCV列表，按时间倒序（最新的在前）
        """
        try:
            key = f"history:{symbol}"
            data = await self.redis.lrange(key, 0, limit - 1)
            return [OHLCV.model_validate_json(d) for d in data]
        except Exception as e:
            logger.error(f"Error getting price history for {symbol}: {e}")
            return []

    async def cache_market_data(
        self,
        symbol: str,
        market_data: MarketData,
        ttl: int = 60
    ):
        """缓存完整市场数据"""
        try:
            key = f"market_data:{symbol}"
            await self.redis.setex(
                key,
                ttl,
                market_data.model_dump_json()
            )
        except Exception as e:
            logger.error(f"Error caching market data for {symbol}: {e}")

    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """获取缓存的市场数据"""
        try:
            key = f"market_data:{symbol}"
            value = await self.redis.get(key)
            if value:
                return MarketData.model_validate_json(value)
            return None
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None

    async def set_collection_status(self, status: str):
        """设置数据采集状态"""
        try:
            await self.redis.set("collection:status", status)
        except Exception as e:
            logger.error(f"Error setting collection status: {e}")

    async def get_collection_status(self) -> Optional[str]:
        """获取数据采集状态"""
        try:
            return await self.redis.get("collection:status")
        except Exception as e:
            logger.error(f"Error getting collection status: {e}")
            return None

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
