from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # PostgreSQL配置
    TIMESCALE_HOST: str = "localhost"
    TIMESCALE_PORT: int = 5432
    TIMESCALE_DB: str = "trading_platform"
    TIMESCALE_USER: str = "admin"
    TIMESCALE_PASSWORD: str = "password"

    # 服务端口
    TRADING_SERVICE_PORT: int = 8003
    DECISION_ENGINE_PORT: int = 8002

    # 交易配置
    COMMISSION_RATE: float = 0.001  # 0.1% 手续费
    SLIPPAGE_RATE: float = 0.0005   # 0.05% 滑点

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
