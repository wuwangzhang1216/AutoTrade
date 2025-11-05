"""
Configuration management for AutoTrade AI system
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # OpenRouter AI Configuration
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    openrouter_site_url: str = Field(default="http://localhost:3000", env="OPENROUTER_SITE_URL")
    openrouter_site_name: str = Field(default="AutoTrade AI", env="OPENROUTER_SITE_NAME")

    # AI Models
    ai_model_primary: str = Field(default="deepseek/deepseek-chat-v3.1", env="AI_MODEL_PRIMARY")
    ai_model_secondary: str = Field(default="qwen/qwen3-vl-235b-a22b-instruct", env="AI_MODEL_SECONDARY")

    # Fundamental Data API Keys (optional)
    # Get free API key from: https://www.coingecko.com/en/api
    coingecko_api_key: Optional[str] = Field(default=None, env="COINGECKO_API_KEY")

    # Trading Configuration
    initial_capital: float = Field(default=10000.0, env="INITIAL_CAPITAL")
    # SUPER AGGRESSIVE: 20x Leverage - EXTREME RISK!
    # WARNING: Price movement of ~4.5% can trigger liquidation (vs 9% at 10x)
    # MONITOR POSITIONS CLOSELY - This doubles liquidation risk
    leverage: int = Field(default=20, env="LEVERAGE")
    commission_rate: float = Field(default=0.001, env="COMMISSION_RATE")
    trading_interval_minutes: int = Field(default=15, env="TRADING_INTERVAL_MINUTES")

    # Database (absolute path to ensure consistency)
    database_url: str = Field(
        default=f"sqlite:///{str(BASE_DIR).replace(chr(92), '/')}/autotrade.db",
        env="DATABASE_URL"
    )

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_to_file: bool = Field(default=True, env="LOG_TO_FILE")

    # Cache Settings
    cache_expiry_minutes: int = Field(default=30, env="CACHE_EXPIRY_MINUTES")
    fundamental_data_cache_hours: int = Field(default=6, env="FUNDAMENTAL_DATA_CACHE_HOURS")

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class TradingPairsConfig:
    """Trading pairs configuration"""

    # Default trading pairs to monitor
    DEFAULT_PAIRS: List[str] = [
        "BTC/USDT",
        "ETH/USDT",
        "SOL/USDT",
        "BNB/USDT",
        "XRP/USDT",
        "ADA/USDT",
        "DOGE/USDT",
        "AVAX/USDT",
        "DOT/USDT",
        "POL/USDT",  # Changed from MATIC/USDT (Polygon migrated to POL)
    ]

    # Technical analysis timeframes
    TIMEFRAMES: List[str] = [
        "5m",   # 5 minutes
        "15m",  # 15 minutes
        "1h",   # 1 hour
        "4h",   # 4 hours
        "1d",   # 1 day
    ]

    # Primary timeframe for trading decisions
    PRIMARY_TIMEFRAME: str = "15m"

    # Maximum number of concurrent positions
    MAX_POSITIONS: int = 5

    # Position size (percentage of available capital per trade)
    # SUPER AGGRESSIVE CONFIGURATION - EXTREME RISK WARNING:
    # With 20x leverage and 15% position size:
    # - 5 positions × 15% = 75% capital utilization
    # - Each position controls 20x the margin (e.g., $1500 margin → $30,000 exposure)
    # - Liquidation at ~4.5% adverse price movement (half the buffer of 10x leverage)
    # - Total exposure can reach $150,000 on $10,000 capital (15x account size)
    #
    # Risk factors to monitor:
    # 1. Extreme volatility can trigger cascading liquidations
    # 2. Trading fees (0.1% per trade) eat into thin liquidation buffer
    # 3. Multiple correlated positions amplify systemic risk
    # 4. Requires constant monitoring during high volatility periods
    #
    # Formula: MAX_POSITIONS * POSITION_SIZE_PERCENT = 75% capital utilization
    # THIS IS A SUPER AGGRESSIVE SETUP - ONLY FOR EXPERIENCED TRADERS
    POSITION_SIZE_PERCENT: float = 15.0  # 15% per position with 20x leverage

    # Alternative conservative setting for risk-averse users:
    # MAX_POSITIONS: int = 4
    # POSITION_SIZE_PERCENT: float = 18.0  # 4 × 18% = 72% utilization


class TechnicalIndicatorsConfig:
    """Technical indicators configuration"""

    # Moving Averages
    MA_PERIODS: List[int] = [10, 20, 50, 100, 200]
    EMA_PERIODS: List[int] = [12, 26, 50, 200]

    # MACD
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9

    # RSI
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT: float = 70.0
    RSI_OVERSOLD: float = 30.0

    # Bollinger Bands
    BB_PERIOD: int = 20
    BB_STD: int = 2

    # ATR (Average True Range)
    ATR_PERIOD: int = 14


class FundamentalDataConfig:
    """Fundamental data sources configuration"""

    # Data refresh intervals (in minutes)
    FEAR_GREED_INTERVAL: int = 60        # 1 hour
    COINGECKO_INTERVAL: int = 30         # 30 minutes

    # API rate limits (requests per minute)
    COINGECKO_RATE_LIMIT: int = 50


class AIDecisionConfig:
    """AI decision engine configuration"""

    # Model temperature (creativity vs consistency)
    TEMPERATURE: float = 0.7

    # Maximum tokens for AI response
    MAX_TOKENS: int = 1000

    # Timeout for individual AI API requests (seconds)
    # Increased to 60s to handle slow API responses
    API_REQUEST_TIMEOUT: int = 60

    # Total timeout for dual model decision (seconds)
    # Should be > API_REQUEST_TIMEOUT to allow both models to complete
    DECISION_TIMEOUT: int = 90

    # Decision voting strategy
    VOTING_STRATEGY: str = "majority"  # Options: "majority", "unanimous", "weighted"

    # Model weights (if using weighted strategy)
    MODEL_WEIGHTS: dict = {
        "deepseek/deepseek-chat-v3.1": 0.5,
        "qwen/qwen3-vl-235b-a22b-instruct": 0.5,
    }

    # Minimum confidence threshold to execute trade
    MIN_CONFIDENCE: float = 0.6  # 60%


class DirectoryConfig:
    """Directory structure"""

    BASE_DIR: Path = BASE_DIR
    LOGS_DIR: Path = BASE_DIR / "logs"
    CACHE_DIR: Path = BASE_DIR / "cache"
    DATA_DIR: Path = BASE_DIR / "data"
    BACKUPS_DIR: Path = BASE_DIR / "backups"

    @classmethod
    def create_directories(cls):
        """Create all necessary directories"""
        for dir_path in [cls.LOGS_DIR, cls.CACHE_DIR, cls.DATA_DIR, cls.BACKUPS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


# Singleton settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"Warning: Could not load settings from .env file: {e}")
    print("Please create a .env file based on .env.example")
    settings = None


# Export all configurations
__all__ = [
    "settings",
    "Settings",
    "TradingPairsConfig",
    "TechnicalIndicatorsConfig",
    "FundamentalDataConfig",
    "AIDecisionConfig",
    "DirectoryConfig",
    "BASE_DIR",
]
