# AutoTrade AI - Architecture Overview

## 项目概述

**AutoTrade AI** 是一个自主加密货币交易系统，使用双AI模型（DeepSeek + Qwen）进行交易决策。项目采用前后端分离架构，后端使用 Python/FastAPI，前端使用 React/TypeScript。

---

## 后端架构 (Backend)

### 技术栈
- **语言**: Python 3.10+
- **框架**: FastAPI + Uvicorn
- **数据库**: SQLite (本地) / PostgreSQL (生产)
- **ORM**: SQLAlchemy 2.0
- **市场数据**: CCXT (Kraken 交易所)
- **AI模型**: OpenRouter API (DeepSeek + Qwen)
- **缓存**: DiskCache

### 核心模块

```
backend/
├── main.py                    # 交易系统主入口 (独立运行)
├── api.py                     # FastAPI 服务器 (REST + WebSocket)
├── run_api.py                 # API 服务器启动脚本
│
├── config/
│   └── settings.py           # 配置管理 (Pydantic)
│
├── core/
│   └── trading_engine.py     # 交易引擎 (杠杆交易模拟)
│
├── data/
│   ├── market_data_collector.py  # 市场数据采集 (CCXT)
│   └── providers/                # 数据提供商
│       ├── fear_greed.py         # Fear & Greed Index
│       └── coingecko.py          # CoinGecko API
│
├── analysis/
│   ├── technical_indicators.py   # 技术分析 (20+ 指标)
│   └── fundamental_analyzer.py   # 基本面分析
│
├── ai/
│   ├── decision_engine.py        # 双AI决策引擎
│   ├── decision_scheduler.py     # 后台AI调度器
│   ├── openrouter_client.py      # OpenRouter API客户端
│   └── prompt_templates.py       # AI提示词模板
│
├── database/
│   ├── models.py                 # SQLAlchemy 模型
│   └── db_manager.py             # 数据库操作层
│
└── utils/
    ├── logger.py                 # Rich 日志系统
    └── helpers.py                # 工具函数
```

### 关键组件说明

#### 1. **交易引擎 (TradingEngine)**
- **位置**: `backend/core/trading_engine.py`
- **职责**:
  - 杠杆交易模拟 (默认20x杠杆)
  - 头寸管理 (LONG/SHORT)
  - 清算检测和自动平仓
  - 保证金和资金管理
  - 支持头寸堆叠 (DCA策略)

#### 2. **AI决策引擎 (AIDecisionEngine)**
- **位置**: `backend/ai/decision_engine.py`
- **职责**:
  - 双模型并行执行 (ThreadPoolExecutor)
  - 投票策略 (majority/unanimous/weighted)
  - 置信度评分 (0-1)
  - 完整推理记录

#### 3. **市场数据采集器 (MarketDataCollector)**
- **位置**: `backend/data/market_data_collector.py`
- **职责**:
  - 批量获取价格 (优化性能)
  - OHLCV数据获取
  - 重试逻辑 (指数退避)

#### 4. **技术分析器 (TechnicalAnalyzer)**
- **位置**: `backend/analysis/technical_indicators.py`
- **职责**:
  - 20+ 技术指标计算 (MA, EMA, MACD, RSI, Bollinger Bands, ATR, ADX, Stochastic, OBV)
  - 信号生成
  - 支持/阻力位识别

#### 5. **数据库管理器 (DatabaseManager)**
- **位置**: `backend/database/db_manager.py`
- **职责**:
  - 交易记录保存
  - AI决策日志
  - 账户快照保存
  - 性能统计查询
  - 头寸恢复 (崩溃恢复)

#### 6. **FastAPI 服务器 (api.py)**
- **位置**: `backend/api.py`
- **职责**:
  - REST API 端点 (15+ 接口)
  - WebSocket 实时推送
  - 内存缓存 (TTL: 30-60秒)
  - CORS 配置

### 数据库表结构

```sql
-- 交易记录
trades (
    id, timestamp, symbol, order_type, side,
    amount, price, pnl, fee
)

-- AI决策记录
ai_decisions (
    id, timestamp, symbol, model_1_decision,
    model_2_decision, final_decision,
    model_1_confidence, model_2_confidence,
    model_1_reasoning, model_2_reasoning,
    input_data (JSON)
)

-- 账户快照
account_snapshots (
    id, timestamp, total_equity, total_capital,
    unrealized_pnl, open_positions (JSON)
)

-- 市场数据缓存
market_data_cache (
    id, timestamp, symbol, timeframe,
    ohlcv_data (JSON), indicators (JSON)
)

-- 系统日志
system_logs (
    id, timestamp, level, message, module
)
```

### 运行模式

#### 模式 1: 独立交易系统
```bash
cd backend
python main.py
```
- 15分钟交易循环
- 控制台丰富输出
- 完整AI决策流程

#### 模式 2: API服务器
```bash
cd backend
python run_api.py
```
- REST API (端口 8888)
- WebSocket 实时推送
- 不执行自动交易 (仅提供API)

#### 模式 3: 完整系统
```bash
# Terminal 1: API服务器
cd backend && python run_api.py

# Terminal 2: 交易系统
cd backend && python main.py
```
- API + 交易系统同时运行
- 前端可以监控交易

### API端点

```
GET  /api/account              # 账户状态
GET  /api/positions            # 当前持仓
GET  /api/trades               # 交易历史
GET  /api/ai-decisions         # AI决策列表
GET  /api/ai-decisions/{id}   # AI决策详情
GET  /api/market-data/{symbol} # 实时价格
GET  /api/ohlcv/{symbol}       # K线数据
GET  /api/equity-curve         # 权益曲线
GET  /api/performance          # 性能统计
GET  /api/trading-pairs        # 交易对列表

WebSocket: /ws                 # 实时更新
```

### 性能优化

1. **批量价格获取**: 1次API调用获取所有价格 (4x速度提升)
2. **内存缓存**: 30-60秒TTL，减少数据库查询
3. **懒加载**: AI决策推理按需加载 (减少80%数据传输)
4. **数据库索引**: 时间戳和交易对索引
5. **并行AI执行**: 双模型并行，决策时间减半

---

## 前端架构 (Frontend)

### 技术栈
- **语言**: TypeScript 5.3
- **框架**: React 18.2
- **构建工具**: Vite 5.0
- **图表库**: TradingView Lightweight Charts 4.1
- **UI组件**: Headless UI 1.7
- **样式**: Tailwind CSS 3.4 + Framer Motion 12.2
- **HTTP客户端**: Axios 1.6
- **状态管理**: React Hooks (useState, useEffect)

### 项目结构

```
frontend/
├── src/
│   ├── App.tsx                      # 根组件
│   ├── main.tsx                     # 入口文件
│   │
│   ├── components/
│   │   ├── Dashboard.tsx            # 主仪表盘 (标签页)
│   │   ├── AccountSummary.tsx       # 账户摘要卡片
│   │   ├── EquityChart.tsx          # 权益曲线图
│   │   ├── TradingChartContainer.tsx # 图表容器 (交易对/时间框架选择)
│   │   ├── TradingChart.tsx         # K线图 (TradingView)
│   │   ├── PositionsList.tsx        # 持仓列表
│   │   ├── TradeHistory.tsx         # 交易历史
│   │   ├── AIDecisionsList.tsx      # AI决策列表
│   │   ├── MarketOverview.tsx       # 市场概览
│   │   ├── ChartErrorBoundary.tsx   # 图表错误边界
│   │   │
│   │   └── ui/                      # UI特效组件
│   │       ├── aurora-background.tsx
│   │       ├── grid-background.tsx
│   │       ├── spotlight.tsx
│   │       ├── moving-border.tsx
│   │       └── ...
│   │
│   ├── api/
│   │   └── client.ts                # Axios API客户端
│   │
│   ├── hooks/
│   │   └── useWebSocket.ts          # WebSocket Hook (自动重连)
│   │
│   ├── config/
│   │   └── api.ts                   # API配置 (URL, WebSocket)
│   │
│   └── lib/
│       └── utils.ts                 # 工具函数 (cn, tailwind merge)
│
├── public/
│   └── logo.png                     # Logo
│
├── index.html
├── vite.config.ts                   # Vite配置 (端口5888, 代理)
├── tailwind.config.js               # Tailwind配置 (金黑主题)
└── package.json
```

### 核心组件说明

#### 1. **Dashboard (仪表盘)**
- **位置**: `frontend/src/components/Dashboard.tsx`
- **职责**:
  - 标签页导航 (Overview, Positions, Trades, AI Decisions)
  - 组件布局和切换
  - 状态管理

#### 2. **AccountSummary (账户摘要)**
- **位置**: `frontend/src/components/AccountSummary.tsx`
- **职责**:
  - 4个指标卡片 (权益, P&L, 持仓数, 胜率)
  - 30秒轮询更新
  - WebSocket实时更新
  - 动画效果

#### 3. **TradingChart (交易图表)**
- **位置**: `frontend/src/components/TradingChart.tsx`
- **职责**:
  - TradingView Lightweight Charts集成
  - K线图渲染
  - 多时间框架支持 (5m, 15m, 1h, 4h, 1d)
  - 响应式缩放
  - 错误处理

#### 4. **PositionsList (持仓列表)**
- **位置**: `frontend/src/components/PositionsList.tsx`
- **职责**:
  - 实时持仓显示
  - 未实现盈亏计算
  - 清算价格警告
  - 30秒轮询 + WebSocket更新

#### 5. **AIDecisionsList (AI决策列表)**
- **位置**: `frontend/src/components/AIDecisionsList.tsx`
- **职责**:
  - AI决策卡片展示
  - 双模型对比 (DeepSeek vs Qwen)
  - 置信度条形图
  - 可展开查看完整推理
  - 懒加载推理内容

#### 6. **useWebSocket Hook**
- **位置**: `frontend/src/hooks/useWebSocket.ts`
- **职责**:
  - WebSocket连接管理
  - 自动重连 (5秒延迟)
  - 消息解析
  - 连接状态追踪

### 数据流

```
1. 初始加载
   ├─> REST API 获取初始数据
   ├─> 渲染页面
   └─> 建立 WebSocket 连接

2. 实时更新
   ├─> WebSocket 推送更新
   ├─> 更新组件状态
   └─> 重新渲染

3. 轮询刷新
   ├─> 定时器触发 (30-60秒)
   ├─> REST API 获取最新数据
   └─> 更新显示

4. 用户交互
   ├─> 切换交易对/时间框架
   ├─> API 获取数据
   └─> 图表重新渲染
```

### 性能优化

1. **减少轮询频率**:
   - Account: 30秒 (原5秒)
   - Positions: 30秒 (原15秒)
   - AI Decisions: 60秒 (原30秒)

2. **图表优化**:
   - 三重数据验证 (防止NaN/Infinity)
   - 节流更新 (3秒最小间隔)
   - 错误边界隔离故障

3. **懒加载**:
   - AI推理内容按需加载
   - 分页加载交易历史

4. **WebSocket优先**:
   - 实时更新优先于轮询
   - 消息节流处理

### UI/UX 特点

- **金黑主题**: 金色 (#eab308) + 精英黑 (#0a0a0a)
- **玻璃拟态**: 背景模糊 + 渐变叠加
- **动画效果**: Framer Motion 弹簧物理动画
- **响应式设计**: 移动端优先
- **深色模式**: 减少眼睛疲劳 (24/7交易优化)

### 运行模式

#### 开发模式
```bash
cd frontend
npm run dev
```
- Vite开发服务器 (端口 5888)
- 热模块替换 (HMR)
- 代理到后端 (端口 8888)

#### 生产模式
```bash
cd frontend
npm run build
node server.js
```
- 构建静态文件
- Express静态服务器
- Heroku部署就绪

---

## 系统交互流程

### 完整交易流程

```
1. 市场数据采集 (15分钟循环)
   ├─> CCXT 获取价格
   ├─> 获取 OHLCV 数据
   └─> 获取基本面数据 (缓存6小时)

2. 数据分析
   ├─> 技术分析 (20+ 指标)
   ├─> 基本面分析 (Fear & Greed)
   └─> 生成信号

3. AI决策
   ├─> 格式化数据为提示词
   ├─> 并行调用双AI模型
   │   ├─> DeepSeek Chat v3.1
   │   └─> Qwen 3 VL 235B
   ├─> 比较决策 (投票策略)
   └─> 执行决策 (置信度 > 60%)

4. 交易执行
   ├─> 计算头寸大小
   ├─> 模拟杠杆交易
   ├─> 追踪保证金和清算
   └─> 记录到数据库

5. 实时广播
   ├─> WebSocket 推送更新
   ├─> 前端更新显示
   └─> 保存账户快照
```

### 前后端通信

```
Frontend                    Backend
   |                          |
   |-- HTTP GET /api/account -->
   |<---- JSON (account) -----
   |                          |
   |-- WebSocket Connect ---->
   |<---- Real-time updates --
   |                          |
   |-- HTTP GET /api/ohlcv -->
   |<---- JSON (chart data) --
   |                          |
```

---

## 部署架构

### 本地开发
```
┌─────────────┐     ┌─────────────┐
│  Frontend   │────>│   Backend   │
│ (Port 5888) │     │ (Port 8888) │
│   Vite Dev  │     │   Uvicorn   │
└─────────────┘     └─────────────┘
                           │
                           v
                    ┌──────────────┐
                    │   SQLite DB  │
                    │ autotrade.db │
                    └──────────────┘
```

### 生产部署 (Heroku)
```
┌────────────────┐          ┌────────────────┐
│  Frontend App  │─────────>│  Backend App   │
│  (Static Site) │          │   (FastAPI)    │
│  Express Server│          │  Gunicorn/Uvi  │
└────────────────┘          └────────────────┘
                                    │
                                    v
                            ┌───────────────┐
                            │  PostgreSQL   │
                            │ (Heroku DB)   │
                            └───────────────┘
```

---

## 关键文件路径

### 配置文件
- 后端配置: `backend/.env`
- 前端配置: `frontend/.env`
- 交易对配置: `backend/config/settings.py`

### 数据库
- SQLite: `./autotrade.db` (项目根目录)
- PostgreSQL: 环境变量 `DATABASE_URL`

### 日志
- 日志目录: `./logs/`
- 日志文件: `autotrade_YYYY-MM-DD.log`

---

## 下一步开发建议

### 短期改进
1. **实时K线更新**: 当前K线图不会自动更新，需要手动刷新
2. **交易通知**: 添加邮件/Telegram通知
3. **止损/止盈**: 实现高级订单类型
4. **回测系统**: 历史数据回放引擎

### 中期增强
1. **多交易所支持**: 集成Binance, OKX等
2. **真实交易**: 接入交易所API (需要认证)
3. **风险管理**: 高级风险控制规则
4. **策略模板**: 可配置交易策略

### 长期规划
1. **用户系统**: 多用户支持
2. **云部署**: AWS/Azure生产部署
3. **移动应用**: React Native应用
4. **机器学习**: 训练自定义模型

---

## 常见问题

### 如何添加新的交易对?
编辑 `backend/config/settings.py`:
```python
DEFAULT_PAIRS = [
    "BTC/USDT",
    "ETH/USDT",
    "YOUR_PAIR/USDT",  # 添加新交易对
]
```

### 如何修改杠杆倍数?
编辑 `backend/.env`:
```env
LEVERAGE=10  # 修改为你想要的杠杆倍数
```

### 如何更改交易间隔?
编辑 `backend/.env`:
```env
TRADING_INTERVAL_MINUTES=30  # 改为30分钟
```

### 如何查看数据库内容?
```bash
sqlite3 autotrade.db
# 或使用 GUI 工具: DB Browser for SQLite
```

---

## 性能指标

### 后端性能
- `/api/account`: ~6ms (缓存命中)
- `/api/positions`: ~2.3s (首次) / ~2ms (缓存)
- `/api/trades`: ~15ms
- `/api/ai-decisions`: ~20ms (列表)

### 前端性能
- 首次加载: ~2秒
- 页面切换: <500ms
- 图表渲染: ~300ms
- WebSocket延迟: <100ms

### 资源消耗
- 后端内存: ~150MB
- 前端内存: ~80MB
- 数据库大小: ~10MB (1000条交易)
- 日志大小: ~5MB/天

---

## 许可证

Mozilla Public License 2.0 (MPL-2.0)
Copyright (C) 2025 W Axis Inc.
