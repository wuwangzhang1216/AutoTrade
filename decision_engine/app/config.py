from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # OpenRouter API
    OPENROUTER_API_KEY: str

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # PostgreSQL配置
    TIMESCALE_HOST: str = "localhost"
    TIMESCALE_PORT: int = 5432
    TIMESCALE_DB: str = "trading_platform"
    TIMESCALE_USER: str = "admin"
    TIMESCALE_PASSWORD: str = "password"

    # Agent配置
    INITIAL_BALANCE: float = 10000.0
    MAX_POSITION_SIZE: float = 0.3
    RISK_PER_TRADE: float = 0.02

    # 服务配置
    DECISION_ENGINE_PORT: int = 8002
    MARKET_DATA_HOST: str = "market_data_service"
    MARKET_DATA_PORT: int = 8001
    TRADING_SERVICE_HOST: str = "trading_service"
    TRADING_SERVICE_PORT: int = 8003

    # 决策间隔（秒）
    DECISION_INTERVAL: int = 300  # 5 minutes

    class Config:
        env_file = "../.env"

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
