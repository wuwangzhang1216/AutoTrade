"""
市场事件检测算法
"""
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from events.event_types import EventType, EventSeverity, MarketEvent
from events.event_config import config
from utils.logger import logger
from analysis.technical_indicators import TechnicalAnalyzer


class EventDetector:
    """
    市场事件检测器

    负责根据市场数据检测各种异常事件
    """

    def __init__(self):
        """初始化检测器"""
        self.last_event_times: Dict[str, datetime] = {}  # 记录每个事件的最后触发时间
        self.technical_analyzer = TechnicalAnalyzer()  # 复用现有的技术指标分析器
        logger.info("EventDetector 初始化完成")

    def detect_flash_move(
        self,
        symbol: str,
        klines_1m: List[dict],
        klines_5m: List[dict],
        klines_15m: List[dict],
    ) -> Optional[MarketEvent]:
        """
        检测快速下跌/上涨

        Args:
            symbol: 交易对
            klines_1m: 1分钟K线数据（最近60根）
            klines_5m: 5分钟K线数据（最近60根）
            klines_15m: 15分钟K线数据（最近60根）

        Returns:
            MarketEvent 或 None
        """
        if not klines_1m or not klines_5m or not klines_15m:
            return None

        current_time = datetime.utcnow()

        # 检查1分钟变化
        move_1m = self._calculate_price_change(klines_1m[-1:], 1)
        # 检查5分钟变化
        move_5m = self._calculate_price_change(klines_5m[-1:], 1)
        # 检查15分钟变化
        move_15m = self._calculate_price_change(klines_15m[-1:], 1)

        # 确定最大移动和对应的时间窗口
        max_move = max(abs(move_1m), abs(move_5m), abs(move_15m))

        if abs(move_1m) == max_move:
            timeframe = "1分钟"
            move_percent = move_1m
        elif abs(move_5m) == max_move:
            timeframe = "5分钟"
            move_percent = move_5m
        else:
            timeframe = "15分钟"
            move_percent = move_15m

        # 判断是否触发阈值
        is_flash_crash = move_percent <= -config.FLASH_MOVE_1MIN_THRESHOLD
        is_flash_rally = move_percent >= config.FLASH_MOVE_1MIN_THRESHOLD

        if not (is_flash_crash or is_flash_rally):
            return None

        # 确定事件类型
        event_type = EventType.FLASH_CRASH if is_flash_crash else EventType.FLASH_RALLY

        # 检查冷却期
        if not self._check_cooldown(symbol, event_type, current_time):
            return None

        # 判断严重程度
        severity = self._get_flash_move_severity(abs(move_percent))

        # 获取当前价格
        current_price = float(klines_1m[-1]['close'])

        # 构建事件
        event = MarketEvent(
            event_type=event_type,
            symbol=symbol,
            severity=severity,
            timestamp=current_time,
            metrics={
                'price_change_percent': move_percent,
                'timeframe': timeframe,
                'current_price': current_price,
                'move_1m': move_1m,
                'move_5m': move_5m,
                'move_15m': move_15m,
            },
            description=f"{symbol} {timeframe}内{'下跌' if is_flash_crash else '上涨'}{abs(move_percent):.2f}%",
            suggested_action=config.SUGGESTION_TEMPLATES.get(event_type, "")
        )

        # 更新最后触发时间
        self._update_last_event_time(symbol, event_type, current_time)

        return event

    def detect_volume_spike(
        self,
        symbol: str,
        current_volume: float,
        avg_volume_24h: float,
    ) -> Optional[MarketEvent]:
        """
        检测成交量激增

        Args:
            symbol: 交易对
            current_volume: 当前成交量（最近1小时）
            avg_volume_24h: 24小时平均成交量

        Returns:
            MarketEvent 或 None
        """
        if not current_volume or not avg_volume_24h or avg_volume_24h == 0:
            return None

        current_time = datetime.utcnow()

        # 计算成交量比率
        volume_ratio = current_volume / avg_volume_24h

        # 检查是否触发激增阈值
        if volume_ratio < config.VOLUME_SPIKE_RATIO:
            return None

        # 检查冷却期
        if not self._check_cooldown(symbol, EventType.VOLUME_SPIKE, current_time):
            return None

        # 判断严重程度
        severity = self._get_volume_spike_severity(volume_ratio)

        # 构建事件
        event = MarketEvent(
            event_type=EventType.VOLUME_SPIKE,
            symbol=symbol,
            severity=severity,
            timestamp=current_time,
            metrics={
                'volume_ratio': volume_ratio,
                'current_volume': current_volume,
                'avg_volume_24h': avg_volume_24h,
            },
            description=f"{symbol} 成交量激增至平均值的{volume_ratio:.2f}倍",
            suggested_action=config.SUGGESTION_TEMPLATES.get(EventType.VOLUME_SPIKE, "")
        )

        # 更新最后触发时间
        self._update_last_event_time(symbol, EventType.VOLUME_SPIKE, current_time)

        return event

    def detect_volume_dry(
        self,
        symbol: str,
        current_volume: float,
        avg_volume_24h: float,
    ) -> Optional[MarketEvent]:
        """
        检测成交量枯竭

        Args:
            symbol: 交易对
            current_volume: 当前成交量（最近1小时）
            avg_volume_24h: 24小时平均成交量

        Returns:
            MarketEvent 或 None
        """
        if not current_volume or not avg_volume_24h or avg_volume_24h == 0:
            return None

        current_time = datetime.utcnow()

        # 计算成交量比率
        volume_ratio = current_volume / avg_volume_24h

        # 检查是否触发枯竭阈值
        if volume_ratio > config.VOLUME_DRY_RATIO:
            return None

        # 检查冷却期
        if not self._check_cooldown(symbol, EventType.VOLUME_DRY, current_time):
            return None

        # 成交量枯竭的严重程度（比率越低越严重）
        if volume_ratio < 0.1:
            severity = EventSeverity.CRITICAL
        elif volume_ratio < 0.15:
            severity = EventSeverity.HIGH
        elif volume_ratio < 0.2:
            severity = EventSeverity.MEDIUM
        else:
            severity = EventSeverity.LOW

        # 构建事件
        event = MarketEvent(
            event_type=EventType.VOLUME_DRY,
            symbol=symbol,
            severity=severity,
            timestamp=current_time,
            metrics={
                'volume_ratio': volume_ratio,
                'current_volume': current_volume,
                'avg_volume_24h': avg_volume_24h,
            },
            description=f"{symbol} 成交量枯竭至平均值的{volume_ratio * 100:.1f}%",
            suggested_action=config.SUGGESTION_TEMPLATES.get(EventType.VOLUME_DRY, "")
        )

        # 更新最后触发时间
        self._update_last_event_time(symbol, EventType.VOLUME_DRY, current_time)

        return event

    def detect_volatility_spike(
        self,
        symbol: str,
        klines_1h: List[dict],
    ) -> Optional[MarketEvent]:
        """
        检测波动率激增

        使用ATR（Average True Range）指标检测波动率

        Args:
            symbol: 交易对
            klines_1h: 1小时K线数据（至少需要28根用于计算）

        Returns:
            MarketEvent 或 None
        """
        if not klines_1h or len(klines_1h) < 28:  # 需要至少28根K线
            return None

        current_time = datetime.utcnow()

        # 转换为 DataFrame 并计算技术指标
        df = self._klines_to_dataframe(klines_1h)
        if df.empty or len(df) < 28:
            return None

        # 使用 TechnicalAnalyzer 计算所有指标（包括 ATR）
        try:
            df = self.technical_analyzer.calculate_all_indicators(df)
        except Exception as e:
            logger.warning(f"计算技术指标失败 ({symbol}): {e}")
            return None

        # 检查 ATR 列是否存在
        if 'ATR' not in df.columns or df['ATR'].isna().all():
            return None

        # 获取当前和历史 ATR（比较最新的 ATR 和 14 根前的 ATR）
        current_atr = df['ATR'].iloc[-1]
        historical_atr = df['ATR'].iloc[-15] if len(df) >= 15 else df['ATR'].iloc[0]

        if pd.isna(current_atr) or pd.isna(historical_atr) or historical_atr == 0:
            return None

        # 计算波动率变化倍数
        volatility_ratio = float(current_atr / historical_atr)

        # 检查是否触发阈值
        if volatility_ratio < config.VOLATILITY_SPIKE_THRESHOLD:
            return None

        # 检查冷却期
        if not self._check_cooldown(symbol, EventType.VOLATILITY_SPIKE, current_time):
            return None

        # 判断严重程度
        severity = self._get_volatility_severity(volatility_ratio)

        # 构建事件
        event = MarketEvent(
            event_type=EventType.VOLATILITY_SPIKE,
            symbol=symbol,
            severity=severity,
            timestamp=current_time,
            metrics={
                'volatility_ratio': volatility_ratio,
                'current_atr': current_atr,
                'historical_atr': historical_atr,
            },
            description=f"{symbol} 波动率激增至历史水平的{volatility_ratio:.2f}倍",
            suggested_action=config.SUGGESTION_TEMPLATES.get(EventType.VOLATILITY_SPIKE, "")
        )

        # 更新最后触发时间
        self._update_last_event_time(symbol, EventType.VOLATILITY_SPIKE, current_time)

        return event

    def detect_liquidation_risk(
        self,
        symbol: str,
        position: dict,
        current_price: float,
    ) -> Optional[MarketEvent]:
        """
        检测清算风险

        Args:
            symbol: 交易对
            position: 持仓信息（包含 liquidation_price, side 等）
            current_price: 当前价格

        Returns:
            MarketEvent 或 None
        """
        if not position or not current_price:
            return None

        liquidation_price = position.get('liquidation_price', 0)
        if not liquidation_price or liquidation_price == 0:
            return None

        current_time = datetime.utcnow()

        # 计算距离清算价格的百分比
        side = position.get('side', 'LONG')
        if side == 'LONG':
            # 多头：当前价格 > 清算价格，距离 = (当前 - 清算) / 当前
            distance_percent = abs((current_price - liquidation_price) / current_price * 100)
        else:
            # 空头：当前价格 < 清算价格，距离 = (清算 - 当前) / 当前
            distance_percent = abs((liquidation_price - current_price) / current_price * 100)

        # 检查是否触发阈值
        if distance_percent > config.LIQUIDATION_RISK_THRESHOLD:
            return None

        # 检查冷却期（清算风险冷却期较短，需要更频繁检查）
        if not self._check_cooldown(symbol, EventType.LIQUIDATION_RISK, current_time):
            return None

        # 判断严重程度（距离越小越严重）
        severity = self._get_liquidation_severity(distance_percent)

        # 构建事件
        event = MarketEvent(
            event_type=EventType.LIQUIDATION_RISK,
            symbol=symbol,
            severity=severity,
            timestamp=current_time,
            metrics={
                'distance_percent': distance_percent,
                'current_price': current_price,
                'liquidation_price': liquidation_price,
                'side': side,
                'position_size': position.get('size', 0),
                'unrealized_pnl': position.get('unrealized_pnl', 0),
            },
            description=f"{symbol} {side}仓位距离清算价格仅{distance_percent:.2f}%",
            suggested_action=config.SUGGESTION_TEMPLATES.get(EventType.LIQUIDATION_RISK, "")
        )

        # 更新最后触发时间
        self._update_last_event_time(symbol, EventType.LIQUIDATION_RISK, current_time)

        return event

    # ==================== 辅助方法 ====================

    def _klines_to_dataframe(self, klines: List[dict]) -> pd.DataFrame:
        """
        将K线列表转换为DataFrame格式（供TechnicalAnalyzer使用）

        Args:
            klines: K线数据列表，每个元素包含 timestamp, open, high, low, close, volume

        Returns:
            pandas DataFrame，包含 open, high, low, close, volume 列
        """
        if not klines:
            return pd.DataFrame()

        df = pd.DataFrame(klines)

        # 确保列名正确
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"K线数据缺少 {col} 列")
                return pd.DataFrame()

        # 转换为数值类型
        for col in required_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def _calculate_price_change(self, klines: List[dict], periods: int = 1) -> float:
        """
        计算价格变化百分比

        Args:
            klines: K线数据
            periods: 时间周期数

        Returns:
            价格变化百分比
        """
        if not klines or len(klines) < periods + 1:
            return 0.0

        try:
            start_price = float(klines[-periods - 1]['close'])
            end_price = float(klines[-1]['close'])

            if start_price == 0:
                return 0.0

            return ((end_price - start_price) / start_price) * 100
        except (KeyError, ValueError, IndexError):
            return 0.0

    def _check_cooldown(self, symbol: str, event_type: EventType, current_time: datetime) -> bool:
        """
        检查事件冷却期

        Args:
            symbol: 交易对
            event_type: 事件类型
            current_time: 当前时间

        Returns:
            True 如果可以触发，False 如果在冷却期内
        """
        event_key = f"{symbol}:{event_type.value}"

        if event_key not in self.last_event_times:
            return True

        last_time = self.last_event_times[event_key]
        cooldown_seconds = config.COOLDOWN_PERIODS.get(event_type, 300)

        time_diff = (current_time - last_time).total_seconds()

        return time_diff >= cooldown_seconds

    def _update_last_event_time(self, symbol: str, event_type: EventType, current_time: datetime):
        """更新事件最后触发时间"""
        event_key = f"{symbol}:{event_type.value}"
        self.last_event_times[event_key] = current_time

    def _get_flash_move_severity(self, move_percent: float) -> EventSeverity:
        """根据价格变化幅度判断严重程度"""
        if move_percent >= config.FLASH_MOVE_SEVERITY_THRESHOLDS[EventSeverity.CRITICAL]:
            return EventSeverity.CRITICAL
        elif move_percent >= config.FLASH_MOVE_SEVERITY_THRESHOLDS[EventSeverity.HIGH]:
            return EventSeverity.HIGH
        elif move_percent >= config.FLASH_MOVE_SEVERITY_THRESHOLDS[EventSeverity.MEDIUM]:
            return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW

    def _get_volume_spike_severity(self, volume_ratio: float) -> EventSeverity:
        """根据成交量比率判断严重程度"""
        if volume_ratio >= config.VOLUME_SPIKE_SEVERITY_THRESHOLDS[EventSeverity.CRITICAL]:
            return EventSeverity.CRITICAL
        elif volume_ratio >= config.VOLUME_SPIKE_SEVERITY_THRESHOLDS[EventSeverity.HIGH]:
            return EventSeverity.HIGH
        elif volume_ratio >= config.VOLUME_SPIKE_SEVERITY_THRESHOLDS[EventSeverity.MEDIUM]:
            return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW

    def _get_volatility_severity(self, volatility_ratio: float) -> EventSeverity:
        """根据波动率比率判断严重程度"""
        if volatility_ratio >= config.VOLATILITY_SEVERITY_THRESHOLDS[EventSeverity.CRITICAL]:
            return EventSeverity.CRITICAL
        elif volatility_ratio >= config.VOLATILITY_SEVERITY_THRESHOLDS[EventSeverity.HIGH]:
            return EventSeverity.HIGH
        elif volatility_ratio >= config.VOLATILITY_SEVERITY_THRESHOLDS[EventSeverity.MEDIUM]:
            return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW

    def _get_liquidation_severity(self, distance_percent: float) -> EventSeverity:
        """根据距离清算价格的百分比判断严重程度（距离越小越严重）"""
        if distance_percent <= config.LIQUIDATION_SEVERITY_THRESHOLDS[EventSeverity.CRITICAL]:
            return EventSeverity.CRITICAL
        elif distance_percent <= config.LIQUIDATION_SEVERITY_THRESHOLDS[EventSeverity.HIGH]:
            return EventSeverity.HIGH
        elif distance_percent <= config.LIQUIDATION_SEVERITY_THRESHOLDS[EventSeverity.MEDIUM]:
            return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW


__all__ = ["EventDetector"]
