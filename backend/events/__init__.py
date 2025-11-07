"""
市场事件监控模块

提供市场异常事件的实时检测和监控功能
"""
from events.event_types import EventType, EventSeverity, MarketEvent
from events.event_config import EventMonitorConfig, config
from events.event_detector import EventDetector
from events.event_monitor import (
    EventMonitor,
    get_event_monitor,
    start_event_monitor,
    stop_event_monitor,
)

__all__ = [
    # Types
    "EventType",
    "EventSeverity",
    "MarketEvent",
    # Config
    "EventMonitorConfig",
    "config",
    # Detector
    "EventDetector",
    # Monitor
    "EventMonitor",
    "get_event_monitor",
    "start_event_monitor",
    "stop_event_monitor",
]
