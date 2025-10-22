from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Optional, List


class OHLCV(BaseModel):
    """OHLCV数据模型"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class TechnicalIndicators(BaseModel):
    """技术指标模型"""
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None


class OrderBook(BaseModel):
    """订单簿模型"""
    bids: List[List[float]]  # [[price, quantity], ...]
    asks: List[List[float]]
    timestamp: datetime


class Ticker24h(BaseModel):
    """24小时行情数据"""
    symbol: str
    price_change: float
    price_change_percent: float
    weighted_avg_price: float
    last_price: float
    last_qty: float
    bid_price: float
    ask_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float
    open_time: datetime
    close_time: datetime
    count: int


class MarketData(BaseModel):
    """完整市场数据"""
    symbol: str
    timestamp: datetime
    ohlcv: OHLCV
    indicators: TechnicalIndicators
    order_book: Optional[OrderBook] = None
    ticker: Optional[Ticker24h] = None  # 添加24小时行情数据，包含准确的价格变化百分比


class MarketSnapshot(BaseModel):
    """市场快照 - 发送给AI模型"""
    timestamp: datetime
    data: Dict[str, MarketData]
