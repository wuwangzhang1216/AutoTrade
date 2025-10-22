"""
Unified configuration for all services
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # General
    SERVICE_NAME: str = "unified_trading_platform"
    PORT: int = int(os.getenv("PORT", "8080"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    TIMESCALE_HOST: str = os.getenv("TIMESCALE_HOST", "localhost")
    TIMESCALE_PORT: int = int(os.getenv("TIMESCALE_PORT", "5432"))
    TIMESCALE_DB: str = os.getenv("TIMESCALE_DB", "trading_platform")
    TIMESCALE_USER: str = os.getenv("TIMESCALE_USER", "admin")
    TIMESCALE_PASSWORD: str = os.getenv("TIMESCALE_PASSWORD", "password")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Market Data Settings
    DATA_COLLECTION_INTERVAL: int = int(os.getenv("DATA_COLLECTION_INTERVAL", "5"))
    SYMBOLS: str = os.getenv("SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,DOGEUSDT,XRPUSDT")

    # Decision Engine Settings
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    INITIAL_BALANCE: float = float(os.getenv("INITIAL_BALANCE", "10000.0"))
    MAX_POSITION_SIZE: float = float(os.getenv("MAX_POSITION_SIZE", "0.3"))
    RISK_PER_TRADE: float = float(os.getenv("RISK_PER_TRADE", "0.02"))
    DECISION_INTERVAL: int = int(os.getenv("DECISION_INTERVAL", "60"))

    # Trading Service Settings
    COMMISSION_RATE: float = float(os.getenv("COMMISSION_RATE", "0.001"))
    SLIPPAGE_RATE: float = float(os.getenv("SLIPPAGE_RATE", "0.0005"))

    @property
    def database_url(self) -> str:
        """Get database URL (Heroku or local)"""
        if self.DATABASE_URL:
            # Heroku provides DATABASE_URL, but we need to convert postgres:// to postgresql://
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        return f"postgresql://{self.TIMESCALE_USER}:{self.TIMESCALE_PASSWORD}@{self.TIMESCALE_HOST}:{self.TIMESCALE_PORT}/{self.TIMESCALE_DB}"

    @property
    def redis_url(self) -> str:
        """Get Redis URL (Heroku or local)"""
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def symbols_list(self) -> List[str]:
        """Parse symbols from comma-separated string"""
        return [s.strip() for s in self.SYMBOLS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    """Get settings instance"""
    return Settings()
