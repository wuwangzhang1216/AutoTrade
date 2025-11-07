"""
市场事件监控主控制器
"""
import threading
import time
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from events.event_types import EventType, EventSeverity, MarketEvent
from events.event_config import config
from events.event_detector import EventDetector
from data.market_data_collector import MarketDataCollector
from database.models import MarketEventRecord, get_session
from utils.logger import logger, log_error, log_warning, log_success
from config import TradingPairsConfig


class EventMonitor:
    """
    市场事件监控器

    负责：
    1. 定期检查市场数据（每5秒）
    2. 检测各种市场异常事件
    3. 记录事件到数据库和日志
    4. 提供事件统计和查询接口
    """

    def __init__(
        self,
        trading_symbols: Optional[List[str]] = None,
        check_interval: int = None,
    ):
        """
        初始化事件监控器

        Args:
            trading_symbols: 要监控的交易对列表（默认使用配置中的交易对）
            check_interval: 检查间隔秒数（默认使用配置值）
        """
        self.symbols = trading_symbols or TradingPairsConfig.get_all_symbols()
        self.check_interval = check_interval or config.CHECK_INTERVAL_SECONDS

        # 初始化组件
        self.detector = EventDetector()
        self.market_data = MarketDataCollector()

        # 监控状态
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None

        # 统计信息
        self.total_events_detected = 0
        self.events_by_type: Dict[str, int] = {}
        self.events_by_severity: Dict[str, int] = {}

        # 数据缓存（用于技术指标计算）
        self.klines_cache: Dict[str, Dict[str, List[dict]]] = {}

        logger.info(f"EventMonitor 初始化完成 - 监控{len(self.symbols)}个交易对")

    def start(self):
        """启动事件监控器"""
        if self.is_running:
            log_warning("EventMonitor 已在运行中")
            return

        if not config.ENABLED:
            log_warning("EventMonitor 已在配置中禁用")
            return

        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        log_success(f"EventMonitor 已启动 - 检查间隔: {self.check_interval}秒")

    def stop(self):
        """停止事件监控器"""
        if not self.is_running:
            return

        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)

        logger.info("EventMonitor 已停止")

    def _monitoring_loop(self):
        """监控主循环（在独立线程中运行）"""
        logger.info("EventMonitor 监控循环开始")

        while self.is_running:
            try:
                loop_start = time.time()

                # 检查所有交易对
                for symbol in self.symbols:
                    if not self.is_running:
                        break

                    try:
                        self._check_symbol(symbol)
                    except Exception as e:
                        log_error(f"检查 {symbol} 时出错: {e}")

                # 等待到下一个检查周期
                elapsed = time.time() - loop_start
                sleep_time = max(0, self.check_interval - elapsed)

                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                log_error(f"监控循环出错: {e}")
                time.sleep(self.check_interval)

        logger.info("EventMonitor 监控循环结束")

    def _check_symbol(self, symbol: str):
        """
        检查单个交易对的市场事件

        Args:
            symbol: 交易对符号
        """
        # 获取市场数据
        market_data = self._fetch_market_data(symbol)
        if not market_data:
            return

        # 检测各种事件
        events = []

        # 1. 检测快速下跌/上涨
        flash_event = self.detector.detect_flash_move(
            symbol=symbol,
            klines_1m=market_data.get('klines_1m', []),
            klines_5m=market_data.get('klines_5m', []),
            klines_15m=market_data.get('klines_15m', []),
        )
        if flash_event:
            events.append(flash_event)

        # 2. 检测成交量激增
        volume_spike_event = self.detector.detect_volume_spike(
            symbol=symbol,
            current_volume=market_data.get('current_volume', 0),
            avg_volume_24h=market_data.get('avg_volume_24h', 0),
        )
        if volume_spike_event:
            events.append(volume_spike_event)

        # 3. 检测成交量枯竭
        volume_dry_event = self.detector.detect_volume_dry(
            symbol=symbol,
            current_volume=market_data.get('current_volume', 0),
            avg_volume_24h=market_data.get('avg_volume_24h', 0),
        )
        if volume_dry_event:
            events.append(volume_dry_event)

        # 4. 检测波动率激增
        volatility_event = self.detector.detect_volatility_spike(
            symbol=symbol,
            klines_1h=market_data.get('klines_1h', []),
        )
        if volatility_event:
            events.append(volatility_event)

        # 5. 检测清算风险（需要持仓信息）
        # 注意：这里需要从交易引擎获取持仓信息
        # 现阶段可以先跳过，等集成时再添加
        # liquidation_event = self._check_liquidation_risk(symbol, market_data)
        # if liquidation_event:
        #     events.append(liquidation_event)

        # 处理检测到的事件
        for event in events:
            self._handle_event(event)

    def _fetch_market_data(self, symbol: str) -> Optional[Dict]:
        """
        获取市场数据

        Args:
            symbol: 交易对符号

        Returns:
            市场数据字典
        """
        try:
            data = {}

            # 获取当前ticker（用于价格和成交量）
            ticker = self.market_data.get_ticker(symbol)
            if not ticker:
                return None

            data['current_price'] = ticker['last']
            data['current_volume'] = ticker.get('volume', 0)

            # 获取K线数据（用于技术分析）
            # 1分钟K线（最近60根）
            klines_1m = self.market_data.get_ohlcv(symbol, timeframe='1m', limit=60)
            if klines_1m:
                data['klines_1m'] = self._format_klines(klines_1m)

            # 5分钟K线（最近60根）
            klines_5m = self.market_data.get_ohlcv(symbol, timeframe='5m', limit=60)
            if klines_5m:
                data['klines_5m'] = self._format_klines(klines_5m)

            # 15分钟K线（最近60根）
            klines_15m = self.market_data.get_ohlcv(symbol, timeframe='15m', limit=60)
            if klines_15m:
                data['klines_15m'] = self._format_klines(klines_15m)

            # 1小时K线（最近30根，用于ATR计算）
            klines_1h = self.market_data.get_ohlcv(symbol, timeframe='1h', limit=30)
            if klines_1h:
                data['klines_1h'] = self._format_klines(klines_1h)

            # 计算24小时平均成交量（使用1小时K线）
            if klines_1h and len(klines_1h) >= 24:
                volumes = [k['volume'] for k in data['klines_1h'][-24:]]
                data['avg_volume_24h'] = sum(volumes) / len(volumes) if volumes else 0
            else:
                # 备用：使用ticker的成交量
                data['avg_volume_24h'] = data['current_volume']

            return data

        except Exception as e:
            log_error(f"获取 {symbol} 市场数据失败: {e}")
            return None

    def _format_klines(self, klines: List) -> List[dict]:
        """
        格式化K线数据

        Args:
            klines: CCXT返回的K线数据 [[timestamp, open, high, low, close, volume], ...]

        Returns:
            格式化后的K线字典列表
        """
        formatted = []
        for kline in klines:
            formatted.append({
                'timestamp': kline[0],
                'open': kline[1],
                'high': kline[2],
                'low': kline[3],
                'close': kline[4],
                'volume': kline[5],
            })
        return formatted

    def _handle_event(self, event: MarketEvent):
        """
        处理检测到的事件

        Args:
            event: 市场事件
        """
        # 更新统计
        self.total_events_detected += 1
        event_type_key = event.event_type.value
        self.events_by_type[event_type_key] = self.events_by_type.get(event_type_key, 0) + 1
        severity_key = event.severity.value
        self.events_by_severity[severity_key] = self.events_by_severity.get(severity_key, 0) + 1

        # 记录到日志
        self._log_event(event)

        # 保存到数据库
        self._save_event_to_db(event)

    def _log_event(self, event: MarketEvent):
        """
        记录事件到日志

        Args:
            event: 市场事件
        """
        severity_emoji = {
            EventSeverity.LOW: "ℹ️",
            EventSeverity.MEDIUM: "⚠️",
            EventSeverity.HIGH: "🚨",
            EventSeverity.CRITICAL: "🔴",
        }

        emoji = severity_emoji.get(event.severity, "📊")

        # 构建日志消息
        message = f"{emoji} 市场事件检测"
        logger.info(message)
        logger.info(f"  交易对: {event.symbol}")
        logger.info(f"  事件类型: {event.event_type.value}")
        logger.info(f"  严重程度: {event.severity.value.upper()}")
        logger.info(f"  描述: {event.description}")

        if event.suggested_action:
            logger.info(f"  建议: {event.suggested_action}")

        if config.VERBOSE_LOGGING and event.metrics:
            logger.info(f"  指标: {event.metrics}")

        logger.info("-" * 60)

    def _save_event_to_db(self, event: MarketEvent):
        """
        保存事件到数据库

        Args:
            event: 市场事件
        """
        try:
            session = get_session()

            # 创建数据库记录
            db_event = MarketEventRecord(
                timestamp=event.timestamp,
                symbol=event.symbol,
                event_type=event.event_type.value,
                severity=event.severity.value,
                description=event.description,
                suggested_action=event.suggested_action,
                metrics=event.metrics,
                processed=False,
            )

            session.add(db_event)
            session.commit()

            # 更新事件ID
            event.id = db_event.id

            session.close()

        except SQLAlchemyError as e:
            log_error(f"保存事件到数据库失败: {e}")
        except Exception as e:
            log_error(f"保存事件时出现未知错误: {e}")

    def get_statistics(self) -> Dict:
        """
        获取事件监控统计信息

        Returns:
            统计信息字典
        """
        return {
            'total_events': self.total_events_detected,
            'events_by_type': self.events_by_type.copy(),
            'events_by_severity': self.events_by_severity.copy(),
            'monitored_symbols': len(self.symbols),
            'is_running': self.is_running,
        }

    def get_recent_events(
        self,
        symbol: Optional[str] = None,
        event_type: Optional[EventType] = None,
        limit: int = 10
    ) -> List[MarketEventRecord]:
        """
        从数据库获取最近的事件

        Args:
            symbol: 过滤交易对（可选）
            event_type: 过滤事件类型（可选）
            limit: 返回数量限制

        Returns:
            事件记录列表
        """
        try:
            session = get_session()

            query = session.query(MarketEventRecord)

            if symbol:
                query = query.filter(MarketEventRecord.symbol == symbol)

            if event_type:
                query = query.filter(MarketEventRecord.event_type == event_type.value)

            events = query.order_by(MarketEventRecord.timestamp.desc()).limit(limit).all()

            session.close()

            return events

        except Exception as e:
            log_error(f"查询事件失败: {e}")
            return []


# 全局单例
_event_monitor: Optional[EventMonitor] = None


def get_event_monitor() -> EventMonitor:
    """获取全局事件监控器实例（单例模式）"""
    global _event_monitor
    if _event_monitor is None:
        _event_monitor = EventMonitor()
    return _event_monitor


def start_event_monitor():
    """启动全局事件监控器"""
    monitor = get_event_monitor()
    monitor.start()


def stop_event_monitor():
    """停止全局事件监控器"""
    monitor = get_event_monitor()
    monitor.stop()


__all__ = [
    "EventMonitor",
    "get_event_monitor",
    "start_event_monitor",
    "stop_event_monitor",
]
