from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ActionType(str, Enum):
    """交易动作类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


class Position(BaseModel):
    """持仓模型"""
    id: Optional[int] = None
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    entry_time: datetime
    side: str = "long"  # long or short
    leverage: float = 1.0  # 杠杆倍数，1-10倍

    @property
    def pnl_percentage(self) -> float:
        """盈亏百分比（基于保证金）"""
        if self.entry_price == 0:
            return 0.0
        # 盈亏百分比 = (未实现盈亏 / 保证金) * 100
        # 保证金 = (entry_price * quantity) / leverage
        margin = (self.entry_price * self.quantity) / self.leverage
        if margin == 0:
            return 0.0
        return (self.unrealized_pnl / margin) * 100


class AccountState(BaseModel):
    """账户状态"""
    agent_id: str
    balance: float
    total_value: float
    positions: List[Position] = []
    total_pnl: float = 0.0
    trade_count: int = 0
    win_count: int = 0
    loss_count: int = 0

    @property
    def win_rate(self) -> float:
        """胜率"""
        if self.trade_count == 0:
            return 0.0
        return self.win_count / self.trade_count


class TradingDecision(BaseModel):
    """交易决策"""
    agent_id: str
    timestamp: datetime
    action: ActionType
    symbol: Optional[str] = None
    quantity: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    leverage: float = 1.0  # 杠杆倍数，1-10倍
    reasoning: str = ""
    confidence: float = 0.5
    raw_response: str = ""
    current_price: Optional[float] = None

    class Config:
        use_enum_values = True


class Trade(BaseModel):
    """交易记录"""
    id: Optional[int] = None
    agent_id: str
    decision_id: Optional[int] = None
    symbol: str
    side: str  # buy/sell
    quantity: float
    price: float
    commission: float = 0.0
    pnl: Optional[float] = None
    executed_at: datetime
    is_simulated: bool = True


class MarketDataSnapshot(BaseModel):
    """市场数据快照（从market_data_service获取）"""
    timestamp: datetime
    data: dict  # symbol -> market data
