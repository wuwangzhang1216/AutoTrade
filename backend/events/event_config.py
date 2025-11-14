"""
事件监控配置参数
"""
from typing import Dict
from events.event_types import EventType, EventSeverity


class EventMonitorConfig:
    """Event Monitor 配置类"""

    # ==================== 基本配置 ====================

    # 检查间隔（秒）
    CHECK_INTERVAL_SECONDS = 5

    # 是否启用事件监控
    ENABLED = True


    # ==================== 快速下跌/上涨检测 ====================

    # 快速移动阈值（百分比）
    FLASH_MOVE_1MIN_THRESHOLD = 2.0   # 1分钟内 ±2%
    FLASH_MOVE_5MIN_THRESHOLD = 3.5   # 5分钟内 ±3.5%
    FLASH_MOVE_15MIN_THRESHOLD = 5.0  # 15分钟内 ±5%


    # ==================== 成交量检测 ====================

    # 成交量激增（相对于24小时平均成交量的倍数）
    VOLUME_SPIKE_RATIO = 3.0  # 3倍以上为激增

    # 成交量枯竭（相对于24小时平均成交量的比例）
    VOLUME_DRY_RATIO = 0.3    # 低于30%为枯竭


    # ==================== 波动率检测 ====================

    # 波动率激增阈值（ATR相对变化）
    VOLATILITY_SPIKE_THRESHOLD = 2.0  # ATR突然增加2倍

    # 波动率计算周期
    VOLATILITY_PERIOD = 14  # 14个周期的ATR


    # ==================== 清算风险检测 ====================

    # 距离清算价格的阈值（百分比）
    LIQUIDATION_RISK_THRESHOLD = 20.0  # 小于20%距离触发警告
    LIQUIDATION_CRITICAL_THRESHOLD = 10.0  # 小于10%触发严重警告


    # ==================== 支撑/阻力突破检测 ====================

    # 突破确认阈值（突破后的最小距离百分比）
    BREAKOUT_CONFIRMATION_PERCENT = 0.5  # 突破后需要移动0.5%以上才确认

    # 支撑/阻力强度阈值（触及次数）
    SR_STRENGTH_THRESHOLD = 3  # 至少触及3次才认为是有效支撑/阻力


    # ==================== 多头/空头陷阱检测 ====================

    # 陷阱检测参数
    TRAP_FALSE_BREAKOUT_PERCENT = 1.0  # 假突破幅度
    TRAP_REVERSAL_PERCENT = 1.5        # 反转幅度
    TRAP_DETECTION_WINDOW = 60         # 检测窗口（分钟）


    # ==================== 冷却期配置 ====================

    # 每种事件类型的冷却期（秒）- 防止同一事件重复触发
    COOLDOWN_PERIODS: Dict[EventType, int] = {
        EventType.FLASH_CRASH: 300,        # 5分钟
        EventType.FLASH_RALLY: 300,        # 5分钟
        EventType.VOLUME_SPIKE: 600,       # 10分钟
        EventType.VOLUME_DRY: 600,         # 10分钟
        EventType.VOLATILITY_SPIKE: 900,   # 15分钟
        EventType.LIQUIDATION_RISK: 180,   # 3分钟（更频繁检查）
        EventType.SUPPORT_BREAK: 600,      # 10分钟
        EventType.RESISTANCE_BREAK: 600,   # 10分钟
        EventType.BULL_TRAP: 1800,         # 30分钟
        EventType.BEAR_TRAP: 1800,         # 30分钟
    }


    # ==================== 严重程度判定规则 ====================

    # Flash Crash/Rally 严重程度阈值
    FLASH_MOVE_SEVERITY_THRESHOLDS = {
        EventSeverity.LOW: 2.0,      # 2-3%
        EventSeverity.MEDIUM: 3.0,   # 3-5%
        EventSeverity.HIGH: 5.0,     # 5-7%
        EventSeverity.CRITICAL: 7.0, # >7%
    }

    # Volume Spike 严重程度阈值（倍数）
    VOLUME_SPIKE_SEVERITY_THRESHOLDS = {
        EventSeverity.LOW: 3.0,      # 3-5倍
        EventSeverity.MEDIUM: 5.0,   # 5-8倍
        EventSeverity.HIGH: 8.0,     # 8-10倍
        EventSeverity.CRITICAL: 10.0,# >10倍
    }

    # Volatility Spike 严重程度阈值（ATR倍数）
    VOLATILITY_SEVERITY_THRESHOLDS = {
        EventSeverity.LOW: 1.5,      # 1.5-2倍
        EventSeverity.MEDIUM: 2.0,   # 2-3倍
        EventSeverity.HIGH: 3.0,     # 3-4倍
        EventSeverity.CRITICAL: 4.0, # >4倍
    }

    # Liquidation Risk 严重程度阈值（距离百分比）
    LIQUIDATION_SEVERITY_THRESHOLDS = {
        EventSeverity.LOW: 20.0,     # 15-20%
        EventSeverity.MEDIUM: 15.0,  # 10-15%
        EventSeverity.HIGH: 10.0,    # 5-10%
        EventSeverity.CRITICAL: 5.0, # <5%
    }


    # ==================== 数据源配置 ====================

    # K线数据周期（用于技术指标计算）
    KLINE_INTERVALS = {
        '1m': 60,      # 1分钟K线，保留60根
        '5m': 60,      # 5分钟K线，保留60根
        '15m': 60,     # 15分钟K线，保留60根
        '1h': 24,      # 1小时K线，保留24根
    }

    # 数据缓存大小（每个交易对）
    MAX_CACHE_SIZE = 1000  # 保留最近1000个数据点


    # ==================== 日志配置 ====================

    # 是否输出详细日志
    VERBOSE_LOGGING = True

    # 是否记录所有检测结果（包括未触发的）
    LOG_ALL_CHECKS = False


    # ==================== 建议动作配置 ====================

    # 是否生成建议动作
    GENERATE_SUGGESTIONS = True

    # 建议动作模板
    SUGGESTION_TEMPLATES = {
        EventType.FLASH_CRASH: "考虑评估是否为买入机会或现有多头止损",
        EventType.FLASH_RALLY: "考虑评估是否为卖出机会或现有空头止损",
        EventType.VOLUME_SPIKE: "关注价格方向，可能出现突破",
        EventType.VOLUME_DRY: "警惕流动性不足，避免大额交易",
        EventType.VOLATILITY_SPIKE: "提高警惕，可能出现大幅波动",
        EventType.LIQUIDATION_RISK: "立即检查持仓风险，考虑减仓或平仓",
        EventType.SUPPORT_BREAK: "关注下行风险，考虑止损",
        EventType.RESISTANCE_BREAK: "关注上行机会，考虑追多",
        EventType.BULL_TRAP: "警惕假突破，避免追高",
        EventType.BEAR_TRAP: "警惕假跌破，可能反弹",
    }


# 便捷访问配置实例
config = EventMonitorConfig()


__all__ = ["EventMonitorConfig", "config"]
