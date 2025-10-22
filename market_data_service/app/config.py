from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional
import os


class Settings(BaseSettings):
    """应用配置"""

    # Heroku URLs (优先使用)
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None

    # Redis配置 (本地开发使用)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # TimescaleDB配置 (本地开发使用)
    TIMESCALE_HOST: str = "localhost"
    TIMESCALE_PORT: int = 5432
    TIMESCALE_DB: str = "trading_platform"
    TIMESCALE_USER: str = "admin"
    TIMESCALE_PASSWORD: str = "password"

    # 数据采集配置
    DATA_COLLECTION_INTERVAL: int = 5  # 秒
    SYMBOLS: str = "BTCUSDT,ETHUSDT,SOLUSDT"

    # 服务端口
    MARKET_DATA_PORT: int = 8001

    class Config:
        env_file = "../.env"

    @property
    def symbols_list(self) -> List[str]:
        """获取交易对列表"""
        return [s.strip() for s in self.SYMBOLS.split(",")]

    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        # 优先使用Heroku的DATABASE_URL
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # 否则使用本地配置
        return (
            f"postgresql://{self.TIMESCALE_USER}:{self.TIMESCALE_PASSWORD}"
            f"@{self.TIMESCALE_HOST}:{self.TIMESCALE_PORT}/{self.TIMESCALE_DB}"
        )

    @property
    def redis_url(self) -> str:
        """获取Redis连接URL"""
        # 优先使用Heroku的REDIS_URL
        if self.REDIS_URL:
            return self.REDIS_URL
        # 否则使用本地配置
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
