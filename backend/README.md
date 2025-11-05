# AutoTrade Backend

This is the backend component of the AutoTrade AI trading system. It can be deployed independently.

## 📦 What's Included

- **Trading System** (`main.py`) - Main AI trading engine
- **REST API** (`api.py`) - FastAPI application for web dashboard
- **WebSocket Server** - Real-time data streaming
- **AI Decision Engine** - Dual AI model decision making
- **Market Data Collection** - CCXT integration for price data
- **Technical Analysis** - 20+ indicators
- **Database Management** - SQLite with SQLAlchemy ORM

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp ../.env.example .env

# Edit .env and add your API key
nano .env  # or notepad .env on Windows
```

Required configuration:
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 3. Run the System

#### Option A: Trading System + API (Recommended)

Open 2 terminals:

**Terminal 1 - API Server:**
```bash
python run_api.py
```
API available at: http://localhost:8888
API docs: http://localhost:8888/docs

**Terminal 2 - Trading Engine:**
```bash
python main.py
```

#### Option B: API Server Only
```bash
python run_api.py
```

#### Option C: Trading System Only
```bash
python main.py
```

## 📁 Directory Structure

```
backend/
├── main.py                      # Trading system entry point
├── api.py                       # FastAPI application
├── run_api.py                   # API server launcher
├── clear_database.py            # Database utility
├── requirements.txt             # Python dependencies
├── config/
│   └── settings.py             # Configuration management
├── core/
│   └── trading_engine.py       # Trading engine logic
├── data/
│   ├── market_data_collector.py # Price data collection
│   ├── cache_manager.py        # Data caching
│   └── providers/              # External data sources
├── analysis/
│   ├── technical_indicators.py # Technical analysis
│   └── fundamental_analyzer.py # Fundamental analysis
├── ai/
│   ├── openrouter_client.py   # AI model client
│   ├── decision_engine.py     # AI decision logic
│   └── prompt_templates.py    # AI prompts
├── database/
│   ├── models.py              # Database models
│   ├── db_manager.py          # Database operations
│   └── __init__.py
└── utils/
    ├── logger.py              # Logging utilities
    └── helpers.py             # Helper functions
```

## 🌐 API Endpoints

### REST API

- `GET /api/account` - Account status and balance
- `GET /api/positions` - Currently open positions
- `GET /api/trades` - Complete trade history
- `GET /api/ai-decisions` - AI decision log
- `GET /api/ai-decisions/{id}` - Detailed AI decision with reasoning
- `GET /api/market-data/{symbol}` - Real-time price data
- `GET /api/ohlcv/{symbol}` - OHLCV data for charts
- `GET /api/equity-curve` - Historical equity data
- `GET /api/performance` - Performance statistics
- `GET /api/trading-pairs` - Configured trading pairs

### WebSocket

Connect to `ws://localhost:8888/ws` for real-time updates.

## ⚙️ Configuration

Edit `.env` file:

```env
# Required
OPENROUTER_API_KEY=your_key_here

# Trading Parameters
INITIAL_CAPITAL=10000
LEVERAGE=10
COMMISSION_RATE=0.001
TRADING_INTERVAL_MINUTES=15
MAX_POSITIONS=5
POSITION_SIZE_PERCENT=20
CONFIDENCE_THRESHOLD=0.60

# AI Models
AI_MODEL_PRIMARY=deepseek/deepseek-chat-v3.1
AI_MODEL_SECONDARY=qwen/qwen3-vl-235b-a22b-instruct
AI_VOTING_STRATEGY=majority

# Optional API Keys
COINGECKO_API_KEY=optional_key
```

## 🚀 Deploy to Heroku

The backend can be deployed independently to Heroku.

### Quick Deploy

```bash
# From backend directory
heroku create autotrade-backend-YOUR_NAME
heroku config:set OPENROUTER_API_KEY=your_key_here
git push heroku main
heroku ps:scale web=1
```

### Required Files

- ✅ `Procfile` - Heroku process configuration
- ✅ `runtime.txt` - Python 3.12.0
- ✅ `requirements.txt` - All dependencies
- ✅ `.slugignore` - Exclude unnecessary files

### Environment Variables

```bash
# Required
heroku config:set OPENROUTER_API_KEY=your_key

# Optional trading config
heroku config:set INITIAL_CAPITAL=10000
heroku config:set LEVERAGE=10
heroku config:set TRADING_INTERVAL_MINUTES=15
```

### Database Persistence

Heroku's filesystem is ephemeral. For persistent database:

```bash
# Add Postgres addon
heroku addons:create heroku-postgresql:mini

# Update database connection to use DATABASE_URL
```

### View Logs

```bash
heroku logs --tail
```

### Complete Guide

See [../HEROKU_DEPLOY.md](../HEROKU_DEPLOY.md) for full deployment instructions.

## 🐳 Docker Deployment (Optional)

### Build Image

```bash
docker build -t autotrade-backend .
```

### Run Container

```bash
docker run -d \
  --name autotrade \
  -p 8888:8888 \
  -v $(pwd)/../cache:/app/cache \
  -v $(pwd)/../logs:/app/logs \
  --env-file .env \
  autotrade-backend
```

## 📊 Database

The system uses SQLite by default:
- Location: `autotrade.db` (created automatically)
- Tables: `trades`, `ai_decisions`, `account_snapshots`, `system_logs`

### Database Management

```bash
# Clear database
python clear_database.py

# Query database
sqlite3 autotrade.db
```

### Database Schema

**Trades:**
- id, timestamp, symbol, order_type, side, amount, price, pnl, fee

**AI Decisions:**
- id, timestamp, symbol, model_1_decision, model_2_decision, final_decision
- model_1_confidence, model_2_confidence, model_1_reasoning, model_2_reasoning
- input_data, executed

**Account Snapshots:**
- id, timestamp, capital, total_equity, total_pnl, unrealized_pnl
- open_positions, total_trades, winning_trades, losing_trades, positions

## 🔒 Security

- **Paper Trading Only** - No real exchange authentication
- **API Keys** - Store in `.env`, never commit to git
- **CORS** - Configure allowed origins in `api.py`
- **No Authentication** - Add auth middleware if exposing publicly

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8888
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8888
kill -9 <PID>
```

### Database Locked

```bash
# Stop all running instances
pkill -f main.py
pkill -f run_api.py

# Clear locks
rm autotrade.db-shm autotrade.db-wal
```

### Import Errors

Ensure you're running from the backend directory:
```bash
cd backend
python main.py
```

## 📝 Logs

Logs are saved to `../logs/` directory:
- `trading_YYYYMMDD.log` - Trading system logs
- `api_YYYYMMDD.log` - API server logs

View live logs:
```bash
tail -f ../logs/trading_*.log
```

## 🔗 Related Components

- **Frontend**: `../frontend/` - React dashboard
- **Cache**: `../cache/` - Market data cache
- **Logs**: `../logs/` - System logs
- **Backups**: `../backups/` - Database backups

## 📄 License

MIT License - See main repository LICENSE file.

## 🤝 Support

For issues and questions, refer to the main repository README.
