# AutoTrade AI - System Architecture

> **Version**: 3.0 (Consolidated)
> **Last Updated**: 2025-12
> **Status**: Production

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Backend Architecture](#2-backend-architecture)
3. [Frontend Architecture](#3-frontend-architecture)
4. [AI Decision System](#4-ai-decision-system)
5. [Event Monitoring System](#5-event-monitoring-system)
6. [Database Schema](#6-database-schema)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Performance & Optimization](#8-performance--optimization)

---

## 1. System Overview

**AutoTrade AI** is an autonomous cryptocurrency trading system using dual AI models (DeepSeek + Qwen) for trading decisions. The system features a decoupled frontend/backend architecture with real-time WebSocket updates.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│     Dashboard + Charts + WebSocket Real-time Updates            │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP/REST API + WebSocket
┌─────────────────────▼───────────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│  - REST API endpoints (/api/account, /api/positions...)        │
│  - WebSocket (/ws) real-time push                               │
│  - AI Scheduler (background thread with file lock)              │
└──────┬──────────────┬──────────────┬───────────────────────────┘
       │              │              │
       ▼              ▼              ▼
┌─────────────┐ ┌──────────┐ ┌─────────────────────────┐
│  Database   │ │  Market  │ │   AI Decision Engine    │
│ PostgreSQL  │ │   Data   │ │  OpenRouter API         │
│             │ │  CCXT    │ │  - DeepSeek Chat v3.1   │
│ - Trades    │ │ (Kraken) │ │  - Qwen3 VL 235B        │
│ - Decisions │ │          │ │                         │
│ - Snapshots │ │          │ │  Dual model + Voting    │
└─────────────┘ └──────────┘ └─────────────────────────┘
```

### Core Trading Pairs

Currently monitoring **3 core pairs**:
- **BTC/USDT** - Bitcoin
- **ETH/USDT** - Ethereum
- **SOL/USDT** - Solana

### Key Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| AI Decision Interval | 5 min | AIDecisionScheduler run interval |
| Event Detection Interval | 5 sec | EventMonitor run interval |
| AI Models | DeepSeek v3.1 + Qwen3 VL 235B | Dual model voting |
| Voting Strategy | Majority Vote | Default strategy |
| Confidence Threshold | 60% (dual) / 55% (single) | Min execution threshold |
| Leverage | Configurable | Default 20x |

---

## 2. Backend Architecture

### Technology Stack

- **Language**: Python 3.10+
- **Framework**: FastAPI + Uvicorn
- **Database**: SQLite (local) / PostgreSQL (production)
- **ORM**: SQLAlchemy 2.0
- **Market Data**: CCXT (Kraken exchange)
- **AI Models**: OpenRouter API (DeepSeek + Qwen)
- **Cache**: DiskCache + In-memory

### Directory Structure

```
backend/
├── main.py                    # Trading system entry (standalone)
├── api.py                     # FastAPI server (REST + WebSocket)
├── run_api.py                 # API server startup script
│
├── config/
│   └── settings.py            # Configuration (Pydantic)
│
├── core/
│   └── trading_engine.py      # Trading engine (leverage trading sim)
│
├── data/
│   ├── market_data_collector.py  # Market data (CCXT)
│   └── providers/                # Data providers
│       ├── fear_greed.py         # Fear & Greed Index
│       └── coingecko.py          # CoinGecko API
│
├── analysis/
│   ├── technical_indicators.py   # Technical analysis (20+ indicators)
│   └── fundamental_analyzer.py   # Fundamental analysis
│
├── ai/
│   ├── decision_engine.py        # Dual AI decision engine
│   ├── decision_scheduler.py     # Background AI scheduler
│   ├── openrouter_client.py      # OpenRouter API client
│   └── prompt_templates.py       # AI prompt templates
│
├── events/
│   ├── event_monitor.py          # Event monitoring controller
│   ├── event_detector.py         # Event detector
│   ├── event_types.py            # Event type definitions
│   └── event_config.py           # Event detection config
│
├── database/
│   ├── models.py                 # SQLAlchemy models
│   └── db_manager.py             # Database operations
│
└── utils/
    ├── logger.py                 # Rich logging
    └── helpers.py                # Utility functions
```

### Core Components

#### 1. Trading Engine (`TradingEngine`)
- **Location**: `backend/core/trading_engine.py`
- **Responsibilities**:
  - Leverage trading simulation (default 20x)
  - Position management (LONG/SHORT)
  - Liquidation detection and auto-close
  - Margin and capital management
  - Position stacking (DCA strategy)

#### 2. AI Decision Engine (`AIDecisionEngine`)
- **Location**: `backend/ai/decision_engine.py`
- **Responsibilities**:
  - Dual model parallel execution (ThreadPoolExecutor)
  - Voting strategy (majority/unanimous/weighted)
  - Confidence scoring (0-1)
  - Complete reasoning records

#### 3. Technical Analyzer (`TechnicalAnalyzer`)
- **Location**: `backend/analysis/technical_indicators.py`
- **Responsibilities**:
  - 20+ technical indicators (MA, EMA, MACD, RSI, BB, ATR, ADX, Stochastic, OBV)
  - Signal generation
  - Support/resistance identification

#### 4. Market Data Collector (`MarketDataCollector`)
- **Location**: `backend/data/market_data_collector.py`
- **Responsibilities**:
  - Batch price fetching (optimized)
  - OHLCV data retrieval
  - Retry logic (exponential backoff)

#### 5. Database Manager (`DatabaseManager`)
- **Location**: `backend/database/db_manager.py`
- **Responsibilities**:
  - Trade record persistence
  - AI decision logging
  - Account snapshot saving
  - Performance stats queries
  - Position recovery (crash recovery)

### Running Modes

#### Mode 1: Standalone Trading
```bash
cd backend
python main.py
```
- 5-minute trading cycle
- Rich console output
- Full AI decision flow

#### Mode 2: API Server Only
```bash
cd backend
python run_api.py
```
- REST API (port 8888)
- WebSocket real-time push
- No auto trading (API only)

#### Mode 3: Full System
```bash
# Terminal 1: API server
cd backend && python run_api.py

# Terminal 2: Trading system
cd backend && python main.py
```

### API Endpoints

```
GET  /api/account              # Account status
GET  /api/positions            # Current positions
GET  /api/trades               # Trade history
GET  /api/ai-decisions         # AI decision list
GET  /api/ai-decisions/{id}    # AI decision details
GET  /api/market-data/{symbol} # Real-time price
GET  /api/ohlcv/{symbol}       # Candlestick data
GET  /api/equity-curve         # Equity curve
GET  /api/performance          # Performance stats
GET  /api/trading-pairs        # Trading pair list

WebSocket: /ws                 # Real-time updates
```

---

## 3. Frontend Architecture

### Technology Stack

- **Language**: TypeScript 5.3
- **Framework**: React 18.2
- **Build Tool**: Vite 5.0
- **Charts**: TradingView Lightweight Charts 4.1
- **UI**: Headless UI 1.7
- **Styling**: Tailwind CSS 3.4 + Framer Motion 12.2
- **HTTP Client**: Axios 1.6

### Directory Structure

```
frontend/
├── src/
│   ├── App.tsx                      # Root component
│   ├── main.tsx                     # Entry point
│   │
│   ├── components/
│   │   ├── Dashboard.tsx            # Main dashboard (tabs)
│   │   ├── AccountSummary.tsx       # Account summary cards
│   │   ├── EquityChart.tsx          # Equity curve chart
│   │   ├── TradingChartContainer.tsx # Chart container
│   │   ├── TradingChart.tsx         # Candlestick (TradingView)
│   │   ├── PositionsList.tsx        # Position list
│   │   ├── TradeHistory.tsx         # Trade history
│   │   ├── AIDecisionsList.tsx      # AI decision list
│   │   ├── MarketOverview.tsx       # Market overview
│   │   └── ui/                      # UI effect components
│   │
│   ├── api/
│   │   └── client.ts                # Axios API client
│   │
│   ├── hooks/
│   │   └── useWebSocket.ts          # WebSocket hook (auto-reconnect)
│   │
│   └── config/
│       └── api.ts                   # API config
│
├── vite.config.ts                   # Vite config (port 5888, proxy)
├── tailwind.config.js               # Tailwind config (gold/black theme)
└── package.json
```

### Core Components

| Component | Responsibility |
|-----------|---------------|
| **Dashboard** | Tab navigation, component layout |
| **AccountSummary** | 4 metric cards (equity, P&L, positions, win rate) |
| **TradingChart** | TradingView Lightweight Charts, multi-timeframe |
| **PositionsList** | Real-time positions, unrealized P&L |
| **AIDecisionsList** | AI decision cards, dual model comparison |

### UI/UX Features

- **Gold/Black Theme**: Gold (#eab308) + Elite Black (#0a0a0a)
- **Glassmorphism**: Background blur + gradient overlays
- **Animations**: Framer Motion spring physics
- **Responsive**: Mobile-first design
- **Dark Mode**: Optimized for 24/7 trading

---

## 4. AI Decision System

### Decision Flow

```
┌──────────────────────────────────────────────────────────┐
│  AI Decision Scheduler (every 5 minutes)                  │
└──────────────────────┬───────────────────────────────────┘
                       │
        ┌──────────────▼────────────────┐
        │  1. Data Collection            │
        │     - Current price            │
        │     - OHLCV (200 candles)      │
        │     - Technical indicators     │
        │     - Fundamental data         │
        └──────────────┬────────────────┘
                       │
        ┌──────────────▼────────────────────────────────────┐
        │  2. Dual Model Decision                            │
        │  ┌────────────────────────────────────┐           │
        │  │  ThreadPoolExecutor (max_workers=2) │           │
        │  │  ┌──────────────┐  ┌──────────────┐ │           │
        │  │  │  DeepSeek    │  │  Qwen3 VL    │ │           │
        │  │  │  Chat v3.1   │  │  235B        │ │           │
        │  │  └──────┬───────┘  └──────┬───────┘ │           │
        │  │         │                 │         │           │
        │  │         ▼                 ▼         │           │
        │  │   {decision, confidence, reasoning} │           │
        │  └────────────────────────────────────┘           │
        │                                                    │
        │  3. Voting (majority/unanimous/weighted)          │
        │     → Final: BUY / SELL / HOLD                    │
        │                                                    │
        │  4. Execution Filter (confidence >= 60%)          │
        └──────────────┬────────────────────────────────────┘
                       │
        ┌──────────────▼────────────────────────────────────┐
        │  3. Trade Execution                                │
        │                                                    │
        │  BUY decision:                                     │
        │    - Has SHORT → Close SHORT first                 │
        │    - Has LONG → Stack (add to position)            │
        │    - No position → Open LONG                       │
        │                                                    │
        │  SELL decision:                                    │
        │    - Has LONG → Close LONG first                   │
        │    - Has SHORT → Stack (add to position)           │
        │    - No position → Open SHORT                      │
        └───────────────────────────────────────────────────┘
```

### Voting Strategies

#### Majority (Default)
```python
if model_1.decision == model_2.decision:
    if avg_confidence >= 0.6:
        return decision
    else:
        return "HOLD"
else:
    if |conf_diff| >= 0.2:  # 20% gap
        return higher_confidence_decision (if >= 0.6)
    else:
        return "HOLD"
```

#### Unanimous
Both models must agree with avg confidence >= 60%

#### Weighted
Uses weighted scores: `score = confidence * weight`

---

## 5. Event Monitoring System

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│  EventMonitor (every 5 seconds - separate thread)         │
├──────────────────────────────────────────────────────────┤
│  For each symbol:                                         │
│    1. Fetch market data (ticker, klines)                 │
│    2. Run EventDetector checks:                          │
│       - detect_flash_move()                              │
│       - detect_volume_spike()                            │
│       - detect_volume_dry()                              │
│       - detect_volatility_spike()                        │
│       - detect_liquidation_risk()                        │
│    3. Handle detected events:                            │
│       - Update stats                                     │
│       - Log to database                                  │
│       - WebSocket broadcast                              │
└──────────────────────────────────────────────────────────┘
```

### Event Types

| Event Type | Detection Logic | Threshold | Cooldown |
|------------|-----------------|-----------|----------|
| FLASH_CRASH | 1/5/15min price drop | >= 2% | 5 min |
| FLASH_RALLY | 1/5/15min price rise | >= 2% | 5 min |
| VOLUME_SPIKE | Current vol / 24h avg | >= 2x | 5 min |
| VOLUME_DRY | Current vol / 24h avg | <= 0.2x | 10 min |
| VOLATILITY_SPIKE | ATR ratio | >= 1.5x | 5 min |
| LIQUIDATION_RISK | Distance to liq price | <= 10% | 2 min |

### Severity Levels

- **CRITICAL**: Immediate attention (>5% drop, <2% to liquidation)
- **HIGH**: High alert (3-5% drop, 2-5% to liquidation)
- **MEDIUM**: Moderate concern (2-3% drop, 5-10% to liquidation)

---

## 6. Database Schema

### Core Tables

```sql
-- Trade records
trades (
    id, timestamp, symbol, order_type, side,
    amount, price, pnl, fee, margin, leverage
)

-- AI decision records
ai_decisions (
    id, timestamp, symbol,
    model_1_decision, model_2_decision, final_decision,
    model_1_confidence, model_2_confidence,
    model_1_reasoning, model_2_reasoning,
    executed, input_data (JSON)
)

-- Account snapshots (equity curve)
account_snapshots (
    id, timestamp, total_equity, total_capital,
    unrealized_pnl, open_positions (JSON),
    total_trades, winning_trades, losing_trades, win_rate, total_fees
)

-- Market events
market_events (
    id, timestamp, symbol, event_type, severity,
    description, suggested_action, metrics (JSON), processed
)

-- Market data cache
market_data_cache (
    id, timestamp, symbol, timeframe,
    ohlcv_data (JSON), indicators (JSON)
)
```

---

## 7. Deployment Architecture

### Local Development

```
┌─────────────┐     ┌─────────────┐
│  Frontend   │────>│   Backend   │
│ (Port 5888) │     │ (Port 8888) │
│   Vite Dev  │     │   Uvicorn   │
└─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   SQLite DB  │
                    │ autotrade.db │
                    └──────────────┘
```

### Production (Heroku)

```
┌────────────────┐          ┌────────────────┐
│  Frontend App  │─────────>│  Backend App   │
│  (Static Site) │          │   (FastAPI)    │
│  Express Server│          │  Gunicorn/Uvi  │
└────────────────┘          └────────────────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │  PostgreSQL   │
                            │ (Heroku DB)   │
                            └───────────────┘
```

### Environment Variables

```bash
# Required
OPENROUTER_API_KEY=sk-or-...
DATABASE_URL=postgresql://...

# Trading Config
INITIAL_CAPITAL=100000
LEVERAGE=20
COMMISSION_RATE=0.001
TRADING_INTERVAL_MINUTES=5
MAX_POSITIONS=100
POSITION_SIZE_PERCENT=100
CONFIDENCE_THRESHOLD=0.60

# AI Models
AI_MODEL_PRIMARY=deepseek/deepseek-chat-v3.1
AI_MODEL_SECONDARY=qwen/qwen3-vl-235b-a22b-instruct
AI_VOTING_STRATEGY=majority
```

---

## 8. Performance & Optimization

### Backend Optimizations

1. **Batch Price Fetching**: 1 API call for all prices (4x speedup)
2. **In-Memory Cache**: 30-60s TTL, reduces DB queries
3. **Lazy Loading**: AI reasoning loaded on demand (80% data reduction)
4. **Database Indexing**: Timestamp and symbol indexes
5. **Parallel AI Execution**: Dual models in parallel (halved decision time)

### Performance Benchmarks

| Endpoint | First Load | Cached |
|----------|------------|--------|
| `/api/account` | ~6ms | ~5ms |
| `/api/positions` | ~2.3s | ~2ms |
| `/api/trades` | ~15ms | - |
| `/api/ai-decisions` | ~20ms | - |
| `/api/equity-curve` | ~15ms | - |

### Frontend Optimizations

1. **Reduced Polling**: 30s intervals (was 5-15s)
2. **WebSocket Priority**: Real-time over polling
3. **Chart Optimization**: Triple validation, 3s throttle
4. **Lazy Loading**: AI reasoning on demand

---

## License

Mozilla Public License 2.0 (MPL-2.0)
Copyright (C) 2025 W Axis Inc.
