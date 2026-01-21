# AutoTrade AI - Paper Trading 功能清单

## 概述

AutoTrade AI 是一个**完整的加密货币模拟交易（Paper Trading）系统**，所有交易都在内存中模拟执行，**不会连接真实交易所账户**，**不会执行真实买卖订单**，完全零风险。

---

## ✅ 核心 Paper Trading 功能

### 1. 模拟账户系统

**文件**: `backend/core/trading_engine.py` - `TradingEngine` 类

#### 1.1 账户初始化
```python
def __init__(self,
    initial_capital: float,      # 初始资金
    leverage: int = 10,           # 杠杆倍数
    commission_rate: float = 0.001, # 手续费率
    max_positions: int = 5        # 最大持仓数
)
```

**功能**:
- ✅ 设置初始模拟资金（默认 $10,000）
- ✅ 可配置杠杆倍数（1x - 100x，默认 20x）
- ✅ 模拟手续费（默认 0.1%）
- ✅ 限制最大持仓数量（默认 100，可配置）

**配置方式**: 编辑 `backend/.env`
```env
INITIAL_CAPITAL=10000      # 初始资金 $10,000
LEVERAGE=20                # 20倍杠杆
COMMISSION_RATE=0.001      # 0.1% 手续费
```

---

#### 1.2 账户状态追踪
```python
def get_account_summary(self, current_prices: Dict[str, float]) -> Dict
```

**实时追踪**:
- ✅ 可用资金 (`capital`)
- ✅ 总权益 (`total_equity`) = 可用资金 + 锁定保证金 + 未实现盈亏
- ✅ 总盈亏 (`total_pnl`)
- ✅ 盈亏百分比 (`total_pnl_percent`)
- ✅ 锁定保证金 (`total_margin`)
- ✅ 未实现盈亏 (`unrealized_pnl`)
- ✅ 持仓数量 (`open_positions`)
- ✅ 总交易次数 (`total_trades`)
- ✅ 胜率 (`win_rate`)
- ✅ 总手续费 (`total_fees`)

**前端展示**: Dashboard → Overview 标签页
- 4个实时更新的指标卡片
- 权益曲线图
- WebSocket 实时推送

---

### 2. 杠杆交易模拟

#### 2.1 保证金计算
```python
def get_position_size(self, price: float, amount: float) -> float:
    """
    计算开仓所需保证金
    保证金 = (价格 × 数量) / 杠杆
    """
    position_value = price * amount
    margin_required = position_value / self.leverage
    return margin_required
```

**示例**:
```
价格: $65,000
数量: 0.5 BTC
杠杆: 20x

仓位价值 = $65,000 × 0.5 = $32,500
保证金 = $32,500 / 20 = $1,625
```

---

#### 2.2 清算价格计算
```python
def _calculate_liquidation_price(self) -> float:
    """
    计算清算价格
    考虑因素：
    1. 开仓手续费（已支付）
    2. 平仓手续费（将支付）
    3. 维持保证金（90%损失阈值）
    """
```

**清算机制**:
- ✅ 自动计算清算价格
- ✅ 90% 损失阈值（保守估计）
- ✅ 考虑双向手续费（开仓 + 平仓）
- ✅ 多头清算：价格下跌至清算价
- ✅ 空头清算：价格上涨至清算价

**清算公式**:
```
有效亏损百分比 = (1 / 杠杆) × 0.9 - 手续费缓冲

多头清算价 = 入场价 × (1 - 有效亏损百分比)
空头清算价 = 入场价 × (1 + 有效亏损百分比)
```

**示例（20x 杠杆）**:
```
入场价: $65,000
杠杆: 20x
手续费: 0.1%

清算阈值: (1/20) × 0.9 - 0.002 = 0.043 = 4.3%

多头清算价: $65,000 × (1 - 0.043) = $62,205
空头清算价: $65,000 × (1 + 0.043) = $67,795
```

---

#### 2.3 自动清算检测
```python
def check_liquidations(self, current_prices: Dict[str, float]) -> List[str]:
    """
    检查并执行清算
    每个交易循环自动检查所有持仓
    """
```

**功能**:
- ✅ 实时监控所有持仓
- ✅ 价格触及清算价时自动平仓
- ✅ 记录清算原因到数据库
- ✅ 日志详细记录清算事件
- ✅ 防止负资金余额

**前端展示**:
- Positions 列表显示清算价格
- 接近清算时警告标识
- 清算后自动从列表移除

---

### 3. 交易功能

#### 3.1 开多仓（做多）
```python
def open_long(self, symbol: str, amount: float, price: float, reason: str = "") -> bool:
    """
    开多仓或增加现有多仓
    支持头寸堆叠（DCA策略）
    """
```

**功能**:
- ✅ 创建新多头仓位
- ✅ 计算并锁定保证金
- ✅ 扣除开仓手续费
- ✅ 计算清算价格
- ✅ 记录交易到数据库
- ✅ 支持头寸堆叠（同方向加仓）

**头寸堆叠逻辑**:
```
已有多仓: 1.0 BTC @ $60,000
新增多仓: 0.5 BTC @ $65,000

总数量: 1.5 BTC
新平均价: ($60,000 × 1.0 + $65,000 × 0.5) / 1.5 = $61,667
新保证金: 原保证金 + 新保证金
新清算价: 基于新平均价重新计算
```

---

#### 3.2 开空仓（做空）
```python
def open_short(self, symbol: str, amount: float, price: float, reason: str = "") -> bool:
    """
    开空仓或增加现有空仓
    支持头寸堆叠
    """
```

**功能**:
- ✅ 创建新空头仓位
- ✅ 做空盈利逻辑：价格下跌赚钱
- ✅ 做空亏损逻辑：价格上涨亏钱
- ✅ 支持头寸堆叠（同方向加仓）
- ✅ 与做多功能一致的保证金和清算机制

---

#### 3.3 平仓
```python
def close_position(self, symbol: str, price: float, reason: str = "") -> Tuple[bool, Optional[float]]:
    """
    平仓并计算实现盈亏
    防止负资金余额
    """
```

**功能**:
- ✅ 计算实现盈亏（Realized P&L）
- ✅ 释放锁定保证金
- ✅ 扣除平仓手续费
- ✅ 更新账户资金
- ✅ 更新交易统计（胜/负/胜率）
- ✅ 记录完整交易到数据库
- ✅ 防止极端亏损导致负余额

**盈亏计算**:
```python
# 多头盈亏
price_change_percent = (exit_price - entry_price) / entry_price
pnl = margin × price_change_percent × leverage

# 空头盈亏
price_change_percent = (entry_price - exit_price) / entry_price
pnl = margin × price_change_percent × leverage
```

**示例（多头）**:
```
入场: $60,000, 退出: $66,000
保证金: $1,500
杠杆: 20x

价格涨幅: ($66,000 - $60,000) / $60,000 = 10%
盈亏: $1,500 × 10% × 20 = $3,000 (+200%)
```

---

#### 3.4 反向交易逻辑
**文件**: `backend/main.py` - AI 决策执行部分

```python
# BUY 决策
if decision == "BUY":
    # 1. 如果有空仓 → 先平空仓
    if symbol in positions and positions[symbol].side == PositionSide.SHORT:
        close_position(symbol, current_price)

    # 2. 开多仓或加仓
    if symbol not in positions or positions[symbol].side == PositionSide.LONG:
        open_long(symbol, amount, current_price)

# SELL 决策
if decision == "SELL":
    # 1. 如果有多仓 → 先平多仓
    if symbol in positions and positions[symbol].side == PositionSide.LONG:
        close_position(symbol, current_price)

    # 2. 开空仓或加仓
    if symbol not in positions or positions[symbol].side == PositionSide.SHORT:
        open_short(symbol, amount, current_price)
```

**特点**:
- ✅ 智能反向交易
- ✅ 先平反向仓位
- ✅ 再开新方向仓位
- ✅ 确保盈亏正确结算

---

### 4. 风险管理功能

#### 4.1 资金验证
```python
def can_open_position(self, symbol: str, price: float, amount: float) -> Tuple[bool, str]:
    """
    检查是否可以开仓
    """
```

**检查项目**:
- ✅ 最大持仓数限制
- ✅ 可用资金充足性
- ✅ 保证金 + 手续费总额
- ✅ 反向仓位冲突检查
- ✅ 详细失败原因返回

---

#### 4.2 输入验证
```python
def _validate_trade_inputs(self, symbol: str, amount: float, price: float) -> bool:
    """
    全面输入验证，防止错误数据
    """
```

**验证项**:
- ✅ 交易对符号有效性
- ✅ 数量 > 0
- ✅ 价格 > 0
- ✅ 数值类型正确
- ✅ 防止极端数值（数值溢出保护）

---

#### 4.3 配置验证
```python
def _validate_configuration(self):
    """
    启动时验证配置安全性
    """
```

**检查项**:
- ✅ 最大资金利用率警告（>85%）
- ✅ 高杠杆警告（>20x）
- ✅ 高手续费警告（>0.2%）
- ✅ 资金分配合理性检查
- ✅ 推荐安全配置值

**示例输出**:
```
⚠️  CONFIGURATION WARNING: Maximum capital utilization is 150%!
   Max Positions: 100 × Position Size: 15% = 150%
   This does not leave enough buffer for fees, slippage, or unrealized losses.
   RECOMMENDATION: Reduce position size to 8.5% or reduce max positions to 56
```

---

#### 4.4 极端情况保护
```python
# 防止负资金余额
if capital_after_close < 0:
    actual_pnl = -position.margin  # 亏损封顶在保证金
    self.capital = max(0.0, ...)   # 资金保底为 0
```

**保护措施**:
- ✅ 亏损封顶（最多亏完保证金）
- ✅ 资金余额不会为负
- ✅ 紧急清算机制
- ✅ 详细错误日志

---

### 5. 崩溃恢复系统

#### 5.1 资金恢复
```python
def _restore_capital_from_database(self):
    """
    从数据库恢复账户资金和统计数据
    解决系统重启后数据丢失问题
    """
```

**恢复内容**:
- ✅ 可用资金
- ✅ 总交易次数
- ✅ 胜/负交易统计
- ✅ 累计手续费
- ✅ 数据合理性验证

**工作原理**:
```
启动时自动执行：
1. 查询 account_snapshots 表
2. 获取最新快照记录
3. 恢复资金和统计数据
4. 验证数据合理性
5. 日志记录恢复状态
```

---

#### 5.2 持仓恢复
```python
def _restore_positions_from_database(self):
    """
    从数据库重建未平仓位
    崩溃恢复必备功能
    """
```

**恢复逻辑**:
```
1. 查询所有 OPEN_LONG / OPEN_SHORT 交易
2. 检查每个开仓是否有对应平仓记录
3. 如果没有平仓 → 重建持仓对象
4. 恢复持仓属性：
   - 交易对
   - 方向（多/空）
   - 数量
   - 入场价
   - 保证金
   - 杠杆
   - 清算价
5. 验证数据一致性
```

**特点**:
- ✅ 完全自动化
- ✅ 无需手动操作
- ✅ 数据一致性检查
- ✅ 防止数据损坏

---

### 6. 性能统计与追踪

#### 6.1 交易统计
**追踪指标**:
- ✅ 总交易次数 (`total_trades`)
- ✅ 盈利交易次数 (`winning_trades`)
- ✅ 亏损交易次数 (`losing_trades`)
- ✅ 胜率 (`win_rate`) = winning / total × 100%
- ✅ 总手续费 (`total_fees`)

**自动更新**: 每次平仓后自动更新统计

---

#### 6.2 权益曲线
**文件**: `backend/database/models.py` - `AccountSnapshot` 表

**记录内容**:
- ✅ 时间戳
- ✅ 可用资金
- ✅ 总权益
- ✅ 未实现盈亏
- ✅ 持仓数量
- ✅ 交易统计
- ✅ 持仓详情（JSON）

**保存频率**: 每个交易循环（默认15分钟）

**前端展示**: Dashboard → 权益曲线图（实时更新）

---

#### 6.3 详细交易日志
**文件**: `backend/database/models.py` - `Trade` 表

**每笔交易记录**:
- ✅ 时间戳
- ✅ 交易对
- ✅ 订单类型（OPEN_LONG, CLOSE_SHORT 等）
- ✅ 方向（LONG/SHORT）
- ✅ 数量
- ✅ 价格
- ✅ 手续费
- ✅ 实现盈亏（平仓时）
- ✅ 保证金
- ✅ 杠杆
- ✅ 原因（AI 决策推理）

**查询示例**:
```sql
-- 查看最近10笔交易
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;

-- 查看盈利交易
SELECT * FROM trades WHERE pnl > 0 ORDER BY pnl DESC;

-- 查看最大亏损
SELECT * FROM trades WHERE pnl < 0 ORDER BY pnl ASC LIMIT 5;

-- 按交易对统计
SELECT symbol, COUNT(*), AVG(pnl), SUM(pnl)
FROM trades
WHERE order_type IN ('CLOSE_LONG', 'CLOSE_SHORT')
GROUP BY symbol;
```

---

### 7. 头寸管理功能

#### 7.1 头寸堆叠（Position Stacking）
**功能**: 同方向多次加仓（DCA 策略）

**特点**:
- ✅ 自动计算加权平均入场价
- ✅ 累加保证金
- ✅ 重新计算清算价
- ✅ 支持无限次堆叠（受资金限制）

**示例场景**:
```
第1次开仓:
  BTC/USDT LONG
  数量: 0.5 BTC
  价格: $60,000
  保证金: $1,500

第2次加仓:
  BTC/USDT LONG
  数量: 0.3 BTC
  价格: $58,000 (回调，加仓)
  保证金: $870

合并后持仓:
  总数量: 0.8 BTC
  平均价: ($60,000×0.5 + $58,000×0.3) / 0.8 = $59,250
  总保证金: $2,370
  新清算价: 基于 $59,250 重新计算
```

**日志输出**:
```
[TRADE] STACKED LONG BTC/USDT | Added: 0.3 | Price: $58,000 | New Avg: $59,250
Total Amount: 0.8 | Total Margin: $2,370
New Liquidation Price: $56,618
```

---

#### 7.2 未实现盈亏追踪
```python
def update_unrealized_pnl(self, current_price: float) -> float:
    """
    实时计算未实现盈亏
    """
```

**功能**:
- ✅ 每次价格更新自动计算
- ✅ 杠杆效应模拟
- ✅ 多头/空头不同逻辑
- ✅ 实时显示在前端

**计算公式**:
```python
# 多头
price_change_pct = (current - entry) / entry
unrealized_pnl = margin × price_change_pct × leverage

# 空头
price_change_pct = (entry - current) / entry
unrealized_pnl = margin × price_change_pct × leverage
```

---

#### 7.3 持仓信息查询
```python
# 获取所有持仓
positions: Dict[str, Position] = trading_engine.positions

# 单个持仓属性
position.symbol            # 交易对
position.side              # LONG/SHORT
position.amount            # 数量
position.entry_price       # 入场价
position.current_price     # 当前价
position.margin            # 保证金
position.leverage          # 杠杆
position.unrealized_pnl    # 未实现盈亏
position.liquidation_price # 清算价
position.open_time         # 开仓时间
```

**前端展示**: Positions 标签页
- 表格形式展示所有持仓
- 实时价格更新
- 盈亏颜色标识（红/绿）
- 清算价格警告

---

### 8. 手续费模拟

#### 8.1 手续费计算
```python
def calculate_fee(self, price: float, amount: float) -> float:
    """
    计算交易手续费
    fee = price × amount × commission_rate
    """
```

**特点**:
- ✅ 开仓时扣除
- ✅ 平仓时扣除
- ✅ 基于仓位价值计算（非保证金）
- ✅ 默认 0.1%（可配置）
- ✅ 累计统计总手续费

**示例**:
```
价格: $65,000
数量: 0.5 BTC
手续费率: 0.1%

仓位价值: $65,000 × 0.5 = $32,500
手续费: $32,500 × 0.001 = $32.50
```

---

#### 8.2 手续费追踪
```python
self.total_fees += fee  # 每次交易累加
```

**显示位置**:
- 账户摘要中显示累计手续费
- 每笔交易记录中单独记录
- 数据库 `trades` 表中保存

---

### 9. 数据库集成

#### 9.1 交易记录保存
**功能**: 所有交易自动保存到数据库

**保存时机**:
- ✅ 开仓时保存 OPEN_LONG / OPEN_SHORT
- ✅ 平仓时保存 CLOSE_LONG / CLOSE_SHORT
- ✅ 清算时保存并标注原因

**数据完整性**:
- ✅ 每笔交易唯一 ID
- ✅ 时间戳精确到秒
- ✅ 完整的交易参数
- ✅ AI 决策原因关联

---

#### 9.2 账户快照保存
**功能**: 定期保存账户状态

**保存内容**:
```python
{
    "timestamp": datetime.now(),
    "capital": 8500.0,
    "total_equity": 9200.0,
    "unrealized_pnl": 700.0,
    "open_positions": 3,
    "total_trades": 15,
    "winning_trades": 9,
    "losing_trades": 6,
    "total_fees": 150.0,
    "positions": {
        "BTC/USDT": {...},
        "ETH/USDT": {...}
    }
}
```

**用途**:
- ✅ 权益曲线绘制
- ✅ 崩溃恢复数据源
- ✅ 历史性能分析
- ✅ 系统审计

---

### 10. 日志系统

#### 10.1 Rich 控制台日志
**文件**: `backend/utils/logger.py`

**日志级别**:
- ✅ INFO - 常规信息（蓝色）
- ✅ SUCCESS - 成功操作（绿色）
- ✅ WARNING - 警告信息（黄色）
- ✅ ERROR - 错误信息（红色）
- ✅ TRADE - 交易专用（金色）
- ✅ AI - AI 决策（紫色）

**日志内容**:
```
[TRADE] LONG BTC/USDT | Amount: 0.5 | Price: $65,000
Margin: $1,625.00 | Fee: $32.50 | Available: $8,342.50
Liquidation Price: $62,205

[TRADE] CLOSE LONG BTC/USDT | Entry: $65,000 | Exit: $68,000
PnL: $3,000.00 (+184.62%) | Fee: $34.00
Capital: $11,308.50
```

---

#### 10.2 文件日志
**位置**: `logs/autotrade_YYYY-MM-DD.log`

**特点**:
- ✅ 每天自动轮换
- ✅ 完整交易历史
- ✅ 错误堆栈追踪
- ✅ 系统事件记录

---

### 11. 前端可视化

#### 11.1 Dashboard 组件
**位置**: `frontend/src/components/`

**Overview 标签页**:
- ✅ 总权益卡片（实时）
- ✅ 总盈亏卡片（百分比 + 金额）
- ✅ 持仓数量卡片
- ✅ 胜率卡片（W/L 统计）
- ✅ 权益曲线图（TradingView）

**Positions 标签页**:
- ✅ 持仓列表表格
- ✅ 实时价格更新
- ✅ 未实现盈亏（颜色标识）
- ✅ 清算价格显示
- ✅ 入场价 vs 当前价对比

**Trades 标签页**:
- ✅ 交易历史列表
- ✅ 买/卖标识（绿/红）
- ✅ 盈亏显示
- ✅ 手续费显示
- ✅ 分页加载

**Charts 组件**:
- ✅ TradingView K线图
- ✅ 多时间框架（5m, 15m, 1h, 4h, 1d）
- ✅ 交易对切换
- ✅ 实时价格更新

---

#### 11.2 WebSocket 实时更新
**功能**: 自动推送账户变化

**推送事件**:
- ✅ 账户余额变化
- ✅ 新持仓开仓
- ✅ 持仓平仓
- ✅ 清算事件
- ✅ AI 决策完成

**更新频率**:
- 广播更新: 每 10 秒
- 单客户端: 每 5 秒
- 重要事件: 立即推送

---

### 12. 配置选项

#### 12.1 环境变量配置
**文件**: `backend/.env`

```env
# 账户配置
INITIAL_CAPITAL=10000          # 初始资金
LEVERAGE=20                    # 杠杆倍数
COMMISSION_RATE=0.001          # 手续费率 0.1%

# 交易配置
TRADING_INTERVAL_MINUTES=15    # 交易循环间隔
MAX_POSITIONS=100              # 最大持仓数（高风险）
POSITION_SIZE_PERCENT=15       # 每次交易占用资金比例

# AI 配置
MIN_CONFIDENCE=0.6             # 最低置信度阈值
AI_VOTING_STRATEGY=majority    # 投票策略
```

---

#### 12.2 交易对配置
**文件**: `backend/config/settings.py`

```python
class TradingPairsConfig:
    DEFAULT_PAIRS = [
        "BTC/USDT",
        "ETH/USDT",
        "SOL/USDT",
        "BNB/USDT",
        "XRP/USDT",
        "ADA/USDT",
        "DOGE/USDT",
        "AVAX/USDT",
        "DOT/USDT",
    ]

    MAX_POSITIONS = 100  # 最大持仓数
    POSITION_SIZE_PERCENT = 15.0  # 单次交易规模
```

---

### 13. 安全特性

#### 13.1 零真实交易风险
- ✅ 不连接交易所账户 API
- ✅ 不执行真实买卖订单
- ✅ 仅使用公开市场数据
- ✅ 所有交易在内存中模拟

---

#### 13.2 数据保护
- ✅ 本地 SQLite 数据库
- ✅ 不上传敏感数据
- ✅ 完整的审计追踪
- ✅ 错误自动恢复

---

#### 13.3 错误处理
- ✅ 全面输入验证
- ✅ 异常捕获和日志
- ✅ 优雅降级
- ✅ 自动重试机制

---

## 📊 使用示例

### 完整 Paper Trading 流程

#### 1. 启动系统
```bash
# Terminal 1: 后端 API
cd backend && python run_api.py

# Terminal 2: 前端
cd frontend && npm run dev

# Terminal 3: 交易系统
cd backend && python main.py
```

---

#### 2. 系统自动运行
```
15分钟交易循环:

1. 获取市场数据
   ├─ Kraken 实时价格
   ├─ OHLCV K线数据
   └─ Fear & Greed 指数

2. 技术分析
   ├─ 计算 20+ 技术指标
   └─ 生成交易信号

3. AI 决策
   ├─ DeepSeek 分析
   ├─ Qwen 分析
   └─ 投票决策

4. 模拟交易执行
   ├─ 检查资金可用性
   ├─ 计算保证金和手续费
   ├─ 更新持仓
   └─ 记录到数据库

5. 清算检查
   ├─ 检查所有持仓
   ├─ 价格触及清算价 → 自动平仓
   └─ 记录清算事件

6. 保存账户快照
   └─ 权益曲线数据点

7. WebSocket 推送
   └─ 前端实时更新

8. 等待 15 分钟
   └─ 重复循环
```

---

#### 3. 监控和分析
```bash
# 查看实时日志
tail -f logs/autotrade_*.log

# 查询数据库
sqlite3 autotrade.db

# 查看交易历史
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;

# 查看持仓盈亏
# 前端 Dashboard → Positions 标签页

# 分析 AI 决策
# 前端 Dashboard → AI Decisions 标签页
```

---

## 🎯 与真实交易的区别

| 特性 | Paper Trading | 真实交易 |
|------|--------------|---------|
| **资金风险** | ❌ 无风险 | ⚠️ 真实资金风险 |
| **API 密钥** | ❌ 不需要 | ✅ 需要交易所 API |
| **订单执行** | 模拟（内存） | 真实提交到交易所 |
| **滑点** | 无 | 有（价格差异） |
| **延迟** | 无 | 有（网络/交易所） |
| **市场冲击** | 无 | 大单会影响价格 |
| **手续费** | 模拟扣除 | 真实扣除 |
| **清算** | 模拟计算 | 交易所强制清算 |
| **数据来源** | 公开市场数据 | 相同 |
| **学习价值** | ✅ 高 | ✅ 最高（有代价） |

---

## 💡 最佳实践

### 1. 初始配置建议
```env
# 保守配置（新手推荐）
INITIAL_CAPITAL=10000
LEVERAGE=5               # 低杠杆，更安全
MAX_POSITIONS=5          # 限制持仓数量
POSITION_SIZE_PERCENT=10 # 单次交易 10%
MIN_CONFIDENCE=0.7       # 高置信度才交易
```

### 2. 运行建议
- ✅ 先运行 2-4 周模拟交易
- ✅ 每周分析交易数据
- ✅ 调整参数优化表现
- ✅ 确认胜率稳定 >55%
- ✅ 然后考虑真实交易（可选）

### 3. 监控重点
- ✅ 每日检查权益曲线
- ✅ 分析最佳/最差交易
- ✅ 评估 AI 决策质量
- ✅ 关注清算事件
- ✅ 追踪胜率变化

---

## 📚 相关文档

- [项目架构](./ARCHITECTURE.md)
- [主文档](../README.md)

---

## 🎉 总结

AutoTrade AI 提供了**完整的 Paper Trading 功能**，从账户管理、杠杆交易、风险控制到性能追踪，一应俱全。这是一个：

✅ **零风险**的学习平台
✅ **专业级**的模拟交易系统
✅ **功能完整**的测试环境
✅ **数据完整**的分析工具

非常适合：
- 学习加密货币交易
- 测试 AI 交易策略
- 理解杠杆交易机制
- 优化风险管理

在考虑真实交易之前，充分利用这个无风险的 Paper Trading 系统！🚀
