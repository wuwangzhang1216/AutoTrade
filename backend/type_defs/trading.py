"""
Type definitions for trading-related data structures

These TypedDict definitions provide type safety and IDE autocompletion
for the various data structures used throughout the trading system.
"""
from typing import TypedDict, Optional, Dict, List, Any
from datetime import datetime


class TechnicalSummary(TypedDict, total=False):
    """Technical analysis summary returned by TechnicalAnalyzer"""
    symbol: str
    current_price: float
    sma_20: float
    sma_50: float
    ema_12: float
    ema_26: float
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    atr: float
    volume: float
    trend: str  # 'bullish', 'bearish', 'neutral'
    signal: str  # 'buy', 'sell', 'hold'
    strength: float  # 0.0 - 1.0


class FundamentalAnalysis(TypedDict, total=False):
    """Fundamental analysis data from external sources"""
    market_cap: float
    volume_24h: float
    circulating_supply: float
    total_supply: float
    ath: float  # All-time high
    ath_change_percentage: float
    atl: float  # All-time low
    atl_change_percentage: float
    price_change_24h: float
    price_change_7d: float
    sentiment_score: float  # -1.0 to 1.0
    news_count: int
    social_volume: int


class MarketSentiment(TypedDict, total=False):
    """Market sentiment indicators"""
    fear_greed_index: int  # 0-100
    fear_greed_label: str  # 'Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed'
    bitcoin_dominance: float
    total_market_cap: float
    market_trend: str  # 'bullish', 'bearish', 'neutral'


class AnalysisResult(TypedDict):
    """Complete analysis result for a trading symbol"""
    symbol: str
    current_price: float
    technical_summary: TechnicalSummary
    fundamental_analysis: FundamentalAnalysis
    market_sentiment: MarketSentiment


class PerformanceStats(TypedDict):
    """Trading performance statistics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float  # Percentage


class AccountContext(TypedDict, total=False):
    """Account context provided to AI for decision making"""
    total_equity: float
    capital: float
    total_pnl: float
    total_pnl_percent: float
    open_positions: int
    max_positions: int
    performance: PerformanceStats


class PositionContext(TypedDict, total=False):
    """Current position context for a symbol"""
    side: str  # 'LONG' or 'SHORT'
    entry_price: float
    amount: float
    unrealized_pnl: float
    pnl_percent: float
    duration_minutes: int
    liquidation_price: float
    margin: float


class HistoricalContext(TypedDict, total=False):
    """Historical AI decision context"""
    decision: str  # 'BUY', 'SELL', 'HOLD'
    price: float
    executed: bool
    time_ago: str
    model_1_confidence: float
    model_2_confidence: float


class AIDecisionResult(TypedDict, total=False):
    """Result from a single AI model"""
    model: str
    decision: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 - 1.0
    reasoning: str
    response_time: float  # Seconds


class AccountSummary(TypedDict):
    """Complete account summary"""
    capital: float
    total_equity: float
    total_pnl: float
    total_pnl_percent: float
    total_margin: float
    total_unrealized_pnl: float
    open_positions: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_fees: float


class PositionData(TypedDict):
    """Position data stored in account snapshots"""
    side: str
    amount: float
    entry_price: float
    unrealized_pnl: float
    margin: float
    leverage: int


class TradeRecord(TypedDict, total=False):
    """Trade execution record"""
    id: int
    timestamp: datetime
    symbol: str
    order_type: str
    side: str
    amount: float
    price: float
    fee: float
    pnl: Optional[float]
    margin: Optional[float]
    leverage: Optional[int]
    reason: Optional[str]


# Type aliases for common patterns
PositionsDict = Dict[str, PositionData]
PricesDict = Dict[str, float]
SymbolList = List[str]


__all__ = [
    "TechnicalSummary",
    "FundamentalAnalysis",
    "MarketSentiment",
    "AnalysisResult",
    "PerformanceStats",
    "AccountContext",
    "PositionContext",
    "HistoricalContext",
    "AIDecisionResult",
    "AccountSummary",
    "PositionData",
    "TradeRecord",
    "PositionsDict",
    "PricesDict",
    "SymbolList",
]
