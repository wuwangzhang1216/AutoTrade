from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # TimescaleDB配置
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
        return (
            f"postgresql://{self.TIMESCALE_USER}:{self.TIMESCALE_PASSWORD}"
            f"@{self.TIMESCALE_HOST}:{self.TIMESCALE_PORT}/{self.TIMESCALE_DB}"
        )


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
