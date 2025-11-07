# Event Monitor 实施方案文档

> **项目**: AutoTrade AI - 事件驱动监控系统
> **版本**: v1.0
> **创建日期**: 2025-11-07
> **状态**: 待实施

---

## 📋 目录

1. [项目背景](#1-项目背景)
2. [目标与范围](#2-目标与范围)
3. [系统架构](#3-系统架构)
4. [技术规格](#4-技术规格)
5. [实施步骤](#5-实施步骤)
6. [代码实现](#6-代码实现)
7. [数据库设计](#7-数据库设计)
8. [配置说明](#8-配置说明)
9. [测试验证](#9-测试验证)
10. [维护与监控](#10-维护与监控)

---

## 1. 项目背景

### 1.1 现状问题

当前 AutoTrade AI 系统使用**时间驱动**决策模式：
- 每5分钟固定执行AI分析
- 无论市场是否有变化
- 可能错过关键时刻（如暴跌）
- 平静期浪费API调用

### 1.2 改进需求

建立**事件驱动**监控系统：
- 实时监控市场异常
- 快速响应突发事件
- 记录事件数据用于回测
- 为后续自动响应打基础

### 1.3 设计原则

1. **独立运行** - 不干扰现有交易系统
2. **只监控不决策** - 第一阶段只检测和记录
3. **可配置** - 阈值、频率可调整
4. **渐进式** - 分阶段扩展功能
5. **生产就绪** - 完善的错误处理和日志

---

## 2. 目标与范围

### 2.1 核心目标

✅ **Phase 1（本次实施）**：
- 实时监控市场数据
- 检测6种异常事件
- 记录到数据库和日志
- 统计分析事件频率

❌ **Phase 2（后续）**：
- 触发AI紧急分析
- 自动响应机制
- 前端实时通知
- 高级事件类型

### 2.2 监控的事件类型

| 事件类型 | 触发条件 | 严重程度判定 |
|---------|---------|-------------|
| **快速下跌** (Flash Crash) | 1分钟 ≥2%, 5分钟 ≥3.5%, 15分钟 ≥5% | 2%=low, 3.5%=medium, 5%=high, 7%=critical |
| **快速上涨** (Flash Rally) | 同上（正向） | 同上 |
| **成交量激增** (Volume Spike) | 5分钟成交量 ≥ 1小时均值的3倍 | 2x=low, 3x=medium, 5x=high, 8x=critical |
| **成交量枯竭** (Volume Dry) | 连续30分钟 < 均值的30% | （暂不实施） |
| **波动率激增** (Volatility Spike) | ATR在1小时内增加 ≥50% | （暂不实施） |
| **清算风险** (Liquidation Risk) | 持仓距清算价 <20% | 30%=low, 20%=medium, 15%=high, 10%=critical |

### 2.3 监控对象

- **交易对**: BTC/USDT, ETH/USDT, SOL/USDT
- **数据源**: Kraken (通过 CCXT)
- **监控频率**: 5秒/次

---

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Event Monitor Layer                       │
│                      (新增独立层)                             │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
        ┌─────────┐  ┌──────────┐  ┌─────────┐
        │ Detector│  │  Logger  │  │Database │
        │ (检测)  │  │  (日志)  │  │ (存储)  │
        └─────────┘  └──────────┘  └─────────┘
                            │
                            │ (Phase 2 才连接)
                            ▼
                ┌───────────────────────┐
                │   AI Decision System  │
                │    (现有系统)         │
                └───────────────────────┘
```

### 3.2 模块关系

```
EventMonitor (主控制器)
    ├── EventDetector (检测算法)
    │   ├── check_flash_move()
    │   ├── check_volume_anomaly()
    │   ├── check_liquidation_risk()
    │   └── (更多检测方法...)
    │
    ├── MarketDataCollector (数据获取)
    │   └── 已有模块，直接复用
    │
    ├── DatabaseManager (数据存储)
    │   └── 已有模块，新增 MarketEvent 表
    │
    └── Logger (日志输出)
        └── 已有模块，直接使用
```

### 3.3 数据流

```
1. EventMonitor 每5秒轮询
   ↓
2. 获取实时价格和成交量
   ↓
3. EventDetector 分析数据
   ↓
4. 检测到异常 → 创建 MarketEvent
   ↓
5. 记录到日志（彩色输出）
   ↓
6. 保存到数据库
   ↓
7. 更新统计信息
```

---

## 4. 技术规格

### 4.1 技术栈

| 组件 | 技术 | 版本要求 |
|------|------|---------|
| 语言 | Python | 3.9+ |
| 数据库 | PostgreSQL | 12+ |
| ORM | SQLAlchemy | 已有 |
| 日志 | Rich + logging | 已有 |
| 并发 | Threading | 标准库 |
| 数据分析 | Pandas | 已有 |

### 4.2 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 检测延迟 | <5秒 | 从事件发生到检测到 |
| CPU占用 | <5% | 后台运行时 |
| 内存占用 | <100MB | 持续运行 |
| 日志文件增长 | ~10MB/天 | 假设每天50个事件 |
| 数据库增长 | ~1000行/天 | 假设每天50个事件 |

### 4.3 依赖关系

**已有依赖（无需新增）**：
- `ccxt` - 市场数据获取
- `pandas` - 数据处理
- `sqlalchemy` - 数据库ORM
- `rich` - 日志美化

**无新增依赖** ✅

---

## 5. 实施步骤

### 5.1 总体流程

```
Phase 1: 准备工作 (30分钟)
├─ 创建目录结构
├─ 创建数据库表
└─ 配置环境变量

Phase 2: 核心开发 (2-3小时)
├─ Step 1: 事件类型定义 (event_types.py)
├─ Step 2: 配置文件 (event_config.py)
├─ Step 3: 检测器 (event_detector.py)
├─ Step 4: 监控器 (event_monitor.py)
└─ Step 5: 数据库模型 (models.py)

Phase 3: 系统集成 (30分钟)
├─ 修改 api.py 启动逻辑
├─ 创建 __init__.py
└─ 测试导入

Phase 4: 测试验证 (1小时)
├─ 单元测试
├─ 集成测试
└─ 观察运行

Phase 5: 部署上线 (30分钟)
├─ 数据库迁移
├─ 环境变量配置
└─ 启动监控
```

### 5.2 详细步骤

#### Step 0: 准备工作

```bash
# 1. 创建目录结构
mkdir -p backend/events

# 2. 创建数据库表（SQL见后文）
psql -d autotrade -f create_market_events_table.sql

# 3. 配置环境变量
echo "ENABLE_EVENT_MONITOR=true" >> .env
```

#### Step 1: 创建 event_types.py

**文件**: `backend/events/event_types.py`
**大小**: ~100行
**依赖**: 仅标准库
**用时**: 10分钟

**内容**:
- `EventType` 枚举
- `EventSeverity` 枚举
- `MarketEvent` dataclass

#### Step 2: 创建 event_config.py

**文件**: `backend/events/event_config.py`
**大小**: ~100行
**依赖**: 无
**用时**: 10分钟

**内容**:
- `EventMonitorConfig` 类
- 所有阈值配置
- 冷却期设置

#### Step 3: 创建 event_detector.py

**文件**: `backend/events/event_detector.py`
**大小**: ~300行
**依赖**: event_types, event_config, data, utils
**用时**: 60分钟

**内容**:
- `EventDetector` 类
- `check_flash_move()` 方法
- `check_volume_anomaly()` 方法
- `check_liquidation_risk()` 方法
- 辅助方法

#### Step 4: 创建 event_monitor.py

**文件**: `backend/events/event_monitor.py`
**大小**: ~350行
**依赖**: event_detector, database, utils
**用时**: 60分钟

**内容**:
- `EventMonitor` 类
- 主监控循环
- 事件处理逻辑
- 统计功能

#### Step 5: 修改 models.py

**文件**: `backend/database/models.py`
**修改**: 添加 ~30行
**用时**: 10分钟

**内容**:
- `MarketEvent` 模型类

#### Step 6: 修改 api.py

**文件**: `backend/api.py`
**修改**: 添加 ~50行
**用时**: 15分钟

**内容**:
- `start_event_monitor_if_needed()` 函数
- 启动逻辑
- 关闭逻辑

#### Step 7: 创建 __init__.py

**文件**: `backend/events/__init__.py`
**大小**: ~10行
**用时**: 5分钟

**内容**:
- 导出主要类

---

## 6. 代码实现

### 6.1 文件结构

```
backend/
├── events/                          # 新增目录
│   ├── __init__.py                 # 模块导出
│   ├── event_types.py              # 事件类型定义
│   ├── event_config.py             # 配置文件
│   ├── event_detector.py           # 检测算法
│   └── event_monitor.py            # 主控制器
│
├── database/
│   └── models.py                   # 修改：添加 MarketEvent
│
└── api.py                          # 修改：集成启动逻辑
```

### 6.2 核心代码框架

#### 6.2.1 event_types.py

```python
"""事件类型定义"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime

class EventType(Enum):
    """市场事件类型"""
    FLASH_CRASH = "flash_crash"
    FLASH_RALLY = "flash_rally"
    VOLUME_SPIKE = "volume_spike"
    LIQUIDATION_RISK = "liquidation_risk"
    # ... 更多类型

class EventSeverity(Enum):
    """事件严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class MarketEvent:
    """市场事件数据结构"""
    event_type: EventType
    symbol: str
    severity: EventSeverity
    timestamp: datetime
    metrics: Dict[str, float]
    description: str
    suggested_action: Optional[str] = None
    id: Optional[int] = None
    processed: bool = False
```

#### 6.2.2 event_config.py

```python
"""事件监控配置"""
class EventMonitorConfig:
    # 监控频率
    CHECK_INTERVAL_SECONDS = 5

    # 快速价格变动阈值
    FLASH_MOVE_1MIN_THRESHOLD = 2.0
    FLASH_MOVE_5MIN_THRESHOLD = 3.5
    FLASH_MOVE_15MIN_THRESHOLD = 5.0

    # 成交量异常阈值
    VOLUME_SPIKE_RATIO = 3.0

    # 清算风险阈值
    LIQUIDATION_DISTANCE_WARNING = 0.20
    LIQUIDATION_DISTANCE_CRITICAL = 0.15

    # 冷却期设置
    COOLDOWN_PERIODS = {
        'flash_crash': 300,
        'flash_rally': 300,
        'volume_spike': 180,
        'liquidation_risk': 120,
    }

    # 严重程度判定
    SEVERITY_THRESHOLDS = {
        'flash_move': {
            'low': 2.0,
            'medium': 3.5,
            'high': 5.0,
            'critical': 7.0,
        },
        # ... 更多配置
    }
```

#### 6.2.3 event_detector.py

```python
"""事件检测算法"""
from typing import Optional, List, Dict
from datetime import datetime, timedelta

class EventDetector:
    """事件检测器"""

    def __init__(self):
        self.config = EventMonitorConfig()
        self.market_data = MarketDataCollector()
        self.price_history = {}
        self.last_triggered = {}

    def check_flash_move(
        self,
        symbol: str,
        current_price: float
    ) -> Optional[MarketEvent]:
        """检测快速价格变动"""
        # 更新价格历史
        # 计算不同时间窗口的变化
        # 判断是否触发
        # 检查冷却期
        # 创建事件对象
        pass

    def check_volume_anomaly(
        self,
        symbol: str,
        current_volume: float
    ) -> Optional[MarketEvent]:
        """检测成交量异常"""
        # 获取历史成交量
        # 计算比率
        # 判断是否触发
        pass

    def check_liquidation_risk(
        self,
        symbol: str,
        current_price: float,
        positions: dict
    ) -> Optional[MarketEvent]:
        """检测清算风险"""
        # 计算距离清算价的距离
        # 判断严重程度
        pass

    def _check_cooldown(
        self,
        event_type: EventType,
        symbol: str
    ) -> bool:
        """检查冷却期"""
        # 防止重复触发
        pass

    def _determine_severity(
        self,
        metric_type: str,
        value: float
    ) -> EventSeverity:
        """确定严重程度"""
        pass
```

#### 6.2.4 event_monitor.py

```python
"""事件监控器"""
from threading import Thread
from typing import Optional, List

class EventMonitor:
    """事件监控器 - 主控制器"""

    def __init__(self, trading_engine=None):
        self.config = EventMonitorConfig()
        self.detector = EventDetector()
        self.market_data = MarketDataCollector()
        self.db = get_db_manager()
        self.trading_engine = trading_engine
        self.running = False
        self.thread = None
        self.stats = {}

    def start(self):
        """启动监控器"""
        self.running = True
        self.thread = Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """停止监控器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)

    def _monitor_loop(self):
        """主监控循环"""
        while self.running:
            try:
                # 检测所有交易对
                events = self._check_all_symbols()

                # 处理事件
                if events:
                    self._handle_events(events)

                # 等待下一周期
                time.sleep(self.config.CHECK_INTERVAL_SECONDS)
            except Exception as e:
                log_error(f"Error in monitor loop: {e}")

    def _check_all_symbols(self) -> List[MarketEvent]:
        """检测所有交易对"""
        detected_events = []
        for symbol in self.symbols:
            # 获取当前数据
            # 调用检测器
            # 收集事件
            pass
        return detected_events

    def _handle_events(self, events: List[MarketEvent]):
        """处理事件"""
        for event in events:
            self._log_event(event)
            self._save_event(event)
            self._update_stats(event)

    def _log_event(self, event: MarketEvent):
        """记录到日志"""
        pass

    def _save_event(self, event: MarketEvent):
        """保存到数据库"""
        pass

    def _update_stats(self, event: MarketEvent):
        """更新统计"""
        pass
```

#### 6.2.5 models.py (新增)

```python
"""在 backend/database/models.py 中添加"""

class MarketEvent(Base):
    """市场事件表"""
    __tablename__ = 'market_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    severity = Column(String(20), nullable=False)
    metrics = Column(JSON, nullable=True)
    description = Column(String(500), nullable=True)
    suggested_action = Column(String(200), nullable=True)
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime, nullable=True)
```

#### 6.2.6 api.py (修改)

```python
"""在 backend/api.py 中添加"""

# 全局变量
event_monitor = None
_event_monitor_started = False

def start_event_monitor_if_needed():
    """启动事件监控器"""
    global event_monitor, _event_monitor_started

    if _event_monitor_started:
        return

    enable = os.getenv('ENABLE_EVENT_MONITOR', 'true').lower() == 'true'
    if not enable:
        log_info("Event Monitor DISABLED")
        _event_monitor_started = True
        return

    _event_monitor_started = True

    def _start():
        global event_monitor
        from events import EventMonitor

        trading_engine = None
        if ai_scheduler:
            trading_engine = ai_scheduler.trading_engine

        event_monitor = EventMonitor(trading_engine)
        event_monitor.start()
        log_info("Event Monitor started")

    threading.Thread(target=_start, daemon=True).start()

@app.on_event("startup")
async def startup_event():
    # 启动事件监控器
    start_event_monitor_if_needed()

@app.on_event("shutdown")
async def shutdown_event():
    # 停止事件监控器
    if event_monitor:
        event_monitor.stop()
```

#### 6.2.7 __init__.py

```python
"""backend/events/__init__.py"""

from .event_types import EventType, EventSeverity, MarketEvent
from .event_config import EventMonitorConfig
from .event_detector import EventDetector
from .event_monitor import EventMonitor

__all__ = [
    "EventType",
    "EventSeverity",
    "MarketEvent",
    "EventMonitorConfig",
    "EventDetector",
    "EventMonitor",
]
```

---

## 7. 数据库设计

### 7.1 表结构

```sql
CREATE TABLE market_events (
    -- 主键
    id SERIAL PRIMARY KEY,

    -- 时间戳
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 事件信息
    event_type VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    severity VARCHAR(20) NOT NULL,

    -- 事件数据（JSON格式）
    metrics JSONB,

    -- 描述信息
    description VARCHAR(500),
    suggested_action VARCHAR(200),

    -- 处理状态
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP
);

-- 索引
CREATE INDEX idx_market_events_timestamp ON market_events(timestamp);
CREATE INDEX idx_market_events_symbol ON market_events(symbol);
CREATE INDEX idx_market_events_type ON market_events(event_type);
CREATE INDEX idx_market_events_processed ON market_events(processed);
CREATE INDEX idx_market_events_severity ON market_events(severity);

-- 复合索引（用于常见查询）
CREATE INDEX idx_market_events_symbol_timestamp
    ON market_events(symbol, timestamp DESC);
CREATE INDEX idx_market_events_type_timestamp
    ON market_events(event_type, timestamp DESC);
```

### 7.2 示例数据

```json
{
  "id": 127,
  "timestamp": "2025-11-07T15:36:45Z",
  "event_type": "flash_crash",
  "symbol": "BTC/USDT",
  "severity": "high",
  "metrics": {
    "price_change_1m": -1.20,
    "price_change_5m": -3.54,
    "price_change_15m": -2.80,
    "current_price": 48234.50,
    "old_price": 50000.00
  },
  "description": "Crash: 3.54% in 5 minutes (BTC/USDT)",
  "suggested_action": "Consider closing LONG positions",
  "processed": false,
  "processed_at": null
}
```

### 7.3 常用查询

```sql
-- 查询最近24小时的事件
SELECT * FROM market_events
WHERE timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- 查询特定交易对的事件
SELECT * FROM market_events
WHERE symbol = 'BTC/USDT'
ORDER BY timestamp DESC
LIMIT 50;

-- 统计事件类型分布
SELECT event_type, severity, COUNT(*) as count
FROM market_events
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY event_type, severity
ORDER BY count DESC;

-- 查询未处理的严重事件
SELECT * FROM market_events
WHERE processed = FALSE
  AND severity IN ('high', 'critical')
ORDER BY timestamp DESC;
```

---

## 8. 配置说明

### 8.1 环境变量

```bash
# .env 文件添加

# Event Monitor 配置
ENABLE_EVENT_MONITOR=true          # 是否启用（默认true）
EVENT_CHECK_INTERVAL=5             # 检查间隔（秒，可选）

# 数据库配置（已有）
DATABASE_URL=postgresql://user:pass@host/autotrade
```

### 8.2 阈值调整

**在 `event_config.py` 中调整**：

```python
# 保守配置（减少误报）
FLASH_MOVE_1MIN_THRESHOLD = 2.5
FLASH_MOVE_5MIN_THRESHOLD = 4.0
VOLUME_SPIKE_RATIO = 4.0

# 激进配置（更敏感）
FLASH_MOVE_1MIN_THRESHOLD = 1.5
FLASH_MOVE_5MIN_THRESHOLD = 2.5
VOLUME_SPIKE_RATIO = 2.0

# 当前推荐（平衡）
FLASH_MOVE_1MIN_THRESHOLD = 2.0
FLASH_MOVE_5MIN_THRESHOLD = 3.5
VOLUME_SPIKE_RATIO = 3.0
```

### 8.3 冷却期调整

```python
COOLDOWN_PERIODS = {
    'flash_crash': 300,       # 5分钟（推荐）
    'flash_rally': 300,
    'volume_spike': 180,      # 3分钟（可调整）
    'liquidation_risk': 120,  # 2分钟（紧急事件）
}
```

---

## 9. 测试验证

### 9.1 单元测试

```python
# tests/test_event_detector.py

def test_flash_crash_detection():
    """测试快速下跌检测"""
    detector = EventDetector()

    # 模拟价格历史
    detector.price_history['BTC/USDT'] = [
        (datetime.now() - timedelta(minutes=5), 50000),
        (datetime.now(), 48000)  # 下跌4%
    ]

    event = detector.check_flash_move('BTC/USDT', 48000)

    assert event is not None
    assert event.event_type == EventType.FLASH_CRASH
    assert event.severity in [EventSeverity.MEDIUM, EventSeverity.HIGH]

def test_cooldown_mechanism():
    """测试冷却期机制"""
    detector = EventDetector()

    # 第一次触发
    result1 = detector._check_cooldown(EventType.FLASH_CRASH, 'BTC/USDT')
    assert result1 == True

    # 立即再次触发（应被阻止）
    result2 = detector._check_cooldown(EventType.FLASH_CRASH, 'BTC/USDT')
    assert result2 == False
```

### 9.2 集成测试

```python
# tests/test_event_monitor.py

def test_event_monitor_lifecycle():
    """测试监控器启动和停止"""
    monitor = EventMonitor()

    # 启动
    monitor.start()
    assert monitor.running == True
    assert monitor.thread is not None

    time.sleep(2)

    # 停止
    monitor.stop()
    assert monitor.running == False
```

### 9.3 手动测试场景

#### 场景1：模拟快速下跌

```bash
# 观察日志输出
tail -f backend/logs/autotrade_$(date +%Y%m%d).log

# 等待BTC价格快速变化（自然发生）
# 或者在测试环境中模拟价格数据
```

#### 场景2：验证数据库记录

```sql
-- 启动系统后，等待5-10分钟
-- 查看是否有事件记录
SELECT * FROM market_events ORDER BY timestamp DESC LIMIT 10;

-- 应该看到一些事件（取决于市场波动）
```

#### 场景3：统计信息输出

```
# 系统每500秒（约8分钟）输出一次统计
# 观察日志中的 "EVENT MONITOR STATISTICS"
```

### 9.4 验收标准

✅ **必须满足**：
- [ ] 系统启动时显示 "EventMonitor started"
- [ ] 无异常错误或崩溃
- [ ] 数据库表创建成功
- [ ] 至少检测到1个事件（等待市场波动）
- [ ] 事件正确保存到数据库
- [ ] 日志输出格式正确且彩色显示
- [ ] 统计信息正常输出

✅ **理想状态**：
- [ ] 在波动市场中，每小时检测到5-15个事件
- [ ] 事件类型分布合理（不全是某一种）
- [ ] 严重程度判断准确
- [ ] 冷却期机制正常工作（无重复事件）
- [ ] CPU占用 <5%
- [ ] 内存占用稳定

---

## 10. 维护与监控

### 10.1 日常监控指标

| 指标 | 正常范围 | 异常阈值 | 处理方式 |
|------|---------|---------|---------|
| **事件频率** | 5-20个/小时 | >50个/小时 | 检查阈值设置 |
| **数据库增长** | <1MB/天 | >10MB/天 | 清理旧数据 |
| **检测延迟** | <5秒 | >30秒 | 检查API响应 |
| **错误率** | 0% | >1% | 查看错误日志 |

### 10.2 日志分析

```bash
# 查看今天的事件数量
grep "EVENT DETECTED" backend/logs/autotrade_$(date +%Y%m%d).log | wc -l

# 按事件类型分类
grep "EVENT DETECTED" backend/logs/autotrade_$(date +%Y%m%d).log | \
  awk '{print $4}' | sort | uniq -c

# 查看错误
grep "ERROR" backend/logs/autotrade_$(date +%Y%m%d).log
```

### 10.3 数据库维护

```sql
-- 清理30天前的数据（定期执行）
DELETE FROM market_events
WHERE timestamp < NOW() - INTERVAL '30 days';

-- 分析表性能
ANALYZE market_events;

-- 重建索引（如果需要）
REINDEX TABLE market_events;
```

### 10.4 故障排查

#### 问题1：无事件检测

**症状**：系统运行但没有检测到任何事件

**排查步骤**：
1. 检查市场是否波动：`SELECT * FROM market_events LIMIT 1;`
2. 检查阈值是否过高：调低 `FLASH_MOVE_*_THRESHOLD`
3. 检查API连接：查看 `market_data.get_ticker()` 返回值
4. 检查日志错误：`grep ERROR logs/*.log`

#### 问题2：事件过多

**症状**：每分钟触发几十个事件

**解决方案**：
1. 调高阈值：`FLASH_MOVE_1MIN_THRESHOLD = 3.0`
2. 延长冷却期：`'flash_crash': 600`
3. 检查是否有数据异常

#### 问题3：CPU占用高

**症状**：Event Monitor 占用 >10% CPU

**解决方案**：
1. 增加检查间隔：`CHECK_INTERVAL_SECONDS = 10`
2. 减少交易对数量
3. 优化数据库查询
4. 检查是否有死循环

#### 问题4：数据库连接失败

**症状**：日志显示 "Failed to save event"

**解决方案**：
1. 检查数据库连接：`psql -d autotrade -c "SELECT 1"`
2. 检查表是否存在：`\dt market_events`
3. 检查权限
4. 重启数据库连接池

### 10.5 性能优化建议

1. **批量插入**（如果事件很多）
   ```python
   # 累积10个事件后批量插入
   self.db.session.bulk_insert_mappings(MarketEvent, event_list)
   ```

2. **异步写入**（Phase 2）
   ```python
   # 使用队列异步写入数据库
   self.event_queue.put(event)
   ```

3. **索引优化**
   ```sql
   -- 根据实际查询模式创建复合索引
   CREATE INDEX idx_custom ON market_events(symbol, timestamp DESC, severity);
   ```

4. **数据归档**
   ```sql
   -- 将旧数据移到归档表
   CREATE TABLE market_events_archive AS
   SELECT * FROM market_events WHERE timestamp < NOW() - INTERVAL '90 days';
   ```

---

## 11. 扩展规划

### 11.1 Phase 2: 智能响应

```python
# 在 EventMonitor._handle_events() 中添加

if event.severity == EventSeverity.CRITICAL:
    # 触发紧急AI分析
    await self.trigger_emergency_analysis(event)
```

### 11.2 Phase 3: 前端通知

```python
# WebSocket 实时推送
await manager.broadcast({
    'type': 'market_event',
    'data': event.to_dict()
})
```

### 11.3 Phase 4: 高级事件

- 多头/空头陷阱检测
- 支撑/阻力突破
- 波动率聚类
- 相关性异常

---

## 12. 检查清单

### 12.1 实施前检查

- [ ] 确认 PostgreSQL 数据库可用
- [ ] 确认当前系统正常运行
- [ ] 备份数据库
- [ ] 阅读完整实施方案
- [ ] 准备测试环境（或直接生产）

### 12.2 实施过程检查

- [ ] 创建 `backend/events/` 目录
- [ ] 创建 4 个核心 Python 文件
- [ ] 修改 `models.py`
- [ ] 修改 `api.py`
- [ ] 创建数据库表
- [ ] 配置环境变量
- [ ] 测试导入（`python -c "from events import EventMonitor"`）
- [ ] 启动系统

### 12.3 实施后验证

- [ ] 检查启动日志
- [ ] 等待5-10分钟观察运行
- [ ] 查询数据库是否有数据
- [ ] 查看统计信息输出
- [ ] 验证CPU/内存占用正常
- [ ] 检查无错误日志

---

## 13. 常见问题 (FAQ)

### Q1: Event Monitor 会影响现有交易系统吗？

**A**: 不会。Event Monitor 是完全独立的线程，只监控不决策，不会干扰 AI Scheduler。

### Q2: 为什么选择5秒间隔？

**A**: 平衡响应速度和系统负载。更短（如2秒）会增加API调用和CPU占用；更长（如10秒）可能错过快速波动。

### Q3: 如果数据库连接失败会怎样？

**A**: Event Monitor 会记录错误日志但继续运行，不会影响主系统。事件会暂时丢失，但系统不会崩溃。

### Q4: 可以监控更多交易对吗？

**A**: 可以。在 `TradingPairsConfig.DEFAULT_PAIRS` 中添加即可。但要注意API速率限制。

### Q5: 事件数据会占用多少存储空间？

**A**: 假设每天50个事件，每个事件~1KB，一年约18MB。非常小。

### Q6: 可以实时查看检测到的事件吗？

**A**: 可以。通过以下方式：
1. 实时日志：`tail -f logs/autotrade_*.log | grep EVENT`
2. 数据库查询：每分钟查询一次最新事件
3. （Phase 2）前端实时通知

### Q7: 如何调整灵敏度？

**A**: 修改 `event_config.py` 中的阈值：
- 降低阈值 = 更灵敏（更多事件）
- 提高阈值 = 更保守（更少事件）

### Q8: 冷却期是什么？为什么需要？

**A**: 冷却期防止同一事件重复触发。例如，BTC下跌3%触发事件后，5分钟内不会再次触发"快速下跌"事件，避免日志刷屏。

---

## 14. 参考资料

### 14.1 相关文档

- [系统架构分析](./SYSTEM_ARCHITECTURE_ANALYSIS.md)
- [AI 配置文档](./CURRENT_AI_AGENT_CONFIGURATION.md)
- [交易手册设计](./TRADING_MANUAL_DESIGN.md) (待创建)

### 14.2 技术文档

- Python Threading: https://docs.python.org/3/library/threading.html
- SQLAlchemy ORM: https://docs.sqlalchemy.org/
- Rich Logging: https://rich.readthedocs.io/

### 14.3 市场知识

- 快速崩盘 (Flash Crash): 瞬间大幅下跌后快速恢复
- 成交量分析: 放量突破/缩量反弹的意义
- 清算机制: 杠杆交易的风险管理

---

## 15. 更新日志

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-11-07 | 初始版本，完整实施方案 | Claude |
| v1.1 | 待定 | Phase 2: 智能响应集成 | - |
| v1.2 | 待定 | Phase 3: 前端通知 | - |

---

## 16. 批准与签核

| 角色 | 姓名 | 日期 | 签名 |
|------|------|------|------|
| 需求方 | - | 2025-11-07 | ✅ 已确认 |
| 开发者 | Claude | 2025-11-07 | ✅ 已完成设计 |
| 测试者 | - | 待定 | - |
| 部署者 | - | 待定 | - |

---

**文档状态**: ✅ 已完成，等待实施
**下一步**: 开始创建文件并实施

---

*文档结束*
