"""
事件类型和严重程度定义
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime


class EventType(Enum):
    """市场事件类型"""
    FLASH_CRASH = "flash_crash"           # 快速下跌
    FLASH_RALLY = "flash_rally"           # 快速上涨
    VOLUME_SPIKE = "volume_spike"         # 成交量激增
    VOLUME_DRY = "volume_dry"             # 成交量枯竭
    VOLATILITY_SPIKE = "volatility_spike" # 波动率激增
    LIQUIDATION_RISK = "liquidation_risk" # 清算风险
    SUPPORT_BREAK = "support_break"       # 跌破支撑
    RESISTANCE_BREAK = "resistance_break" # 突破阻力
    BULL_TRAP = "bull_trap"               # 多头陷阱
    BEAR_TRAP = "bear_trap"               # 空头陷阱


class EventSeverity(Enum):
    """事件严重程度"""
    LOW = "low"           # 轻微异常
    MEDIUM = "medium"     # 中等异常
    HIGH = "high"         # 严重异常
    CRITICAL = "critical" # 极严重（需立即关注）


@dataclass
class MarketEvent:
    """市场事件数据结构"""
    event_type: EventType
    symbol: str
    severity: EventSeverity
    timestamp: datetime

    # 事件指标
    metrics: Dict[str, float]

    # 描述信息
    description: str
    suggested_action: Optional[str] = None

    # 内部使用
    id: Optional[int] = None
    processed: bool = False


__all__ = ["EventType", "EventSeverity", "MarketEvent"]
