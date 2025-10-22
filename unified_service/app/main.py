"""
Unified Trading Service
Combines Market Data Service, Decision Engine, and Trading Service into one application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import aiohttp
from typing import Set, Dict, Optional
from datetime import datetime
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add paths for importing from other services
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'market_data_service'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'decision_engine'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'trading_service'))

# Import Market Data Service components
from market_data_service.app.config import get_settings as get_market_settings
from market_data_service.app.models import MarketSnapshot, MarketData, OHLCV
from market_data_service.app.collectors.binance import BinanceCollector
from market_data_service.app.storage.redis_cache import RedisCache
from market_data_service.app.storage.timescale_db import TimescaleDB
from market_data_service.app.processors.indicators import IndicatorCalculator
from market_data_service.app.api import routes as market_routes

# Import Decision Engine components
from decision_engine.app.config import get_settings as get_decision_settings
from decision_engine.app.database import Database
from decision_engine.app.agents.agent_manager import AgentManager
from decision_engine.app.agents.openrouter_agent import (
    GPT4Agent, ClaudeAgent, DeepSeekAgent, QwenAgent, GeminiAgent, GrokAgent
)
from decision_engine.app.models.trading import MarketDataSnapshot, AccountState
from decision_engine.app.executor import DecisionExecutor

# Import Trading Service components
from trading_service.app.config import get_settings as get_trading_settings
from trading_service.app.execution.simulator import SimulatedExecutor, ExecutionResult
from trading_service.app.risk.risk_manager import RiskManager
from trading_service.app.portfolio_manager import PortfolioManager
from trading_service.app.multi_agent_portfolio import MultiAgentPortfolio
from trading_service.app.performance_tracker import PerformanceTracker
from trading_service.app import api_routes as trading_routes

# Create FastAPI app
app = FastAPI(
    title="Unified Trading Platform",
    version="1.0.0",
    description="Combined Market Data, Decision Engine, and Trading Services"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global settings
market_settings = get_market_settings()
decision_settings = get_decision_settings()
trading_settings = get_trading_settings()

# Market Data Service globals
redis_cache: RedisCache = None
timescale_db: TimescaleDB = None
collector: BinanceCollector = None
active_connections: Set[WebSocket] = set()

# Decision Engine globals
database: Database = None
agent_manager: AgentManager = None
executor: DecisionExecutor = None

# Trading Service globals
sim_executor: SimulatedExecutor = None
risk_manager: RiskManager = None
multi_portfolio: MultiAgentPortfolio = None
performance_tracker: PerformanceTracker = None

# AI Agents list
AI_AGENTS = ['gpt5', 'claude', 'gemini', 'grok', 'deepseek', 'qwen']


@app.on_event("startup")
async def startup_event():
    """Initialize all services on startup"""
    global redis_cache, timescale_db, collector
    global database, agent_manager, executor
    global sim_executor, risk_manager, multi_portfolio, performance_tracker

    logger.info("=" * 60)
    logger.info("🚀 Starting Unified Trading Platform...")
    logger.info("=" * 60)

    # ========== Initialize Market Data Service ==========
    logger.info("📊 Initializing Market Data Service...")

    # Initialize Redis
    if market_settings.REDIS_URL:
        redis_cache = RedisCache(url=market_settings.redis_url)
    else:
        redis_cache = RedisCache(
            host=market_settings.REDIS_HOST,
            port=market_settings.REDIS_PORT,
            db=market_settings.REDIS_DB
        )
    await redis_cache.connect()

    # Initialize TimescaleDB
    timescale_db = TimescaleDB(market_settings.database_url)
    timescale_db.initialize()

    # Initialize Market routes dependencies
    market_routes.init_dependencies(redis_cache, timescale_db)

    # Initialize data collector
    collector = BinanceCollector(symbols=market_settings.symbols_list)

    logger.info(f"✅ Market Data Service initialized - Monitoring {len(market_settings.symbols_list)} symbols")

    # ========== Initialize Decision Engine ==========
    logger.info("🤖 Initializing Decision Engine...")

    try:
        # Initialize database
        database = Database(decision_settings.database_url)
        database.initialize()

        # Initialize Agent Manager
        agent_manager = AgentManager()

        # Initialize Decision Executor
        executor = DecisionExecutor()

        # Create and register AI agents
        try:
            api_key = decision_settings.OPENROUTER_API_KEY

            agents_config = [
                (GPT4Agent, "gpt5"),
                (ClaudeAgent, "claude"),
                (DeepSeekAgent, "deepseek"),
                (QwenAgent, "qwen"),
                (GeminiAgent, "gemini"),
                (GrokAgent, "grok")
            ]

            for AgentClass, agent_id in agents_config:
                agent = AgentClass(
                    agent_id=agent_id,
                    api_key=api_key,
                    initial_balance=decision_settings.INITIAL_BALANCE,
                    max_position_size=decision_settings.MAX_POSITION_SIZE,
                    risk_per_trade=decision_settings.RISK_PER_TRADE
                )
                agent_manager.register_agent(agent)
                database.create_agent(
                    agent_id=agent.agent_id,
                    name=agent.name,
                    model_type=agent.model_name,
                    initial_balance=agent.initial_balance
                )
                logger.info(f"  ✓ {agent.name} Agent registered")

            logger.info(f"✅ Decision Engine initialized - {len(agent_manager.agents)} agents registered")

        except Exception as e:
            logger.error(f"Error initializing AI agents: {e}")
            logger.warning("Decision Engine will run in fallback mode")

    except Exception as e:
        logger.error(f"Error during Decision Engine startup: {e}")
        logger.info("Decision Engine started in fallback mode")

    # ========== Initialize Trading Service ==========
    logger.info("💰 Initializing Trading Service...")

    # Initialize multi-agent portfolio system
    multi_portfolio = MultiAgentPortfolio(
        agents=AI_AGENTS,
        initial_cash=10000.0
    )

    # Initialize simulated executor
    sim_executor = SimulatedExecutor(
        commission_rate=trading_settings.COMMISSION_RATE,
        slippage_rate=trading_settings.SLIPPAGE_RATE
    )

    # Initialize risk manager
    risk_manager = RiskManager(
        max_position_size=1.0,
        max_drawdown=1.0
    )

    # Initialize performance tracker
    performance_tracker = PerformanceTracker(max_points=288)

    # Initialize Trading API routes
    trading_routes.init_multi_portfolio(multi_portfolio)
    trading_routes.init_performance_tracker(performance_tracker)

    logger.info(f"✅ Trading Service initialized - {len(AI_AGENTS)} AI traders ready")

    # ========== Start Background Tasks ==========
    logger.info("⚙️  Starting background tasks...")

    # Start market data collection
    asyncio.create_task(collect_market_data_loop())
    logger.info("  ✓ Market data collection loop started")

    # Start decision loop
    asyncio.create_task(decision_loop())
    logger.info("  ✓ Decision loop started")

    # Start trading execution loop
    asyncio.create_task(multi_agent_trading_loop())
    logger.info("  ✓ Multi-agent trading loop started")

    logger.info("=" * 60)
    logger.info("✅ Unified Trading Platform started successfully!")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down Unified Trading Platform...")

    if redis_cache:
        await redis_cache.close()

    logger.info("Shutdown complete")


# ========== Market Data Service Functions ==========

async def collect_market_data_loop():
    """Market data collection loop"""
    logger.info("Starting market data collection loop...")
    await asyncio.sleep(2)  # Wait for initialization

    await redis_cache.set_collection_status("running")

    async with collector:
        while True:
            try:
                logger.debug("Collecting market data...")

                all_data = await collector.collect_all_symbols()
                market_snapshot_data = {}

                for symbol, data in all_data.items():
                    try:
                        historical_klines = data.get('historical_klines', [])

                        if historical_klines:
                            timescale_db.save_ohlcv_batch(historical_klines)
                            for kline in historical_klines[-100:]:
                                await redis_cache.push_price_history(symbol, kline)

                        latest_ohlcv = data.get('latest_ohlcv')
                        if not latest_ohlcv:
                            continue

                        indicators = IndicatorCalculator.calculate_all(historical_klines)
                        ticker = data.get('ticker')

                        market_data = MarketData(
                            symbol=symbol,
                            timestamp=latest_ohlcv.timestamp,
                            ohlcv=latest_ohlcv,
                            indicators=indicators,
                            order_book=data.get('order_book'),
                            ticker=ticker
                        )

                        market_snapshot_data[symbol] = market_data
                        await redis_cache.cache_market_data(symbol, market_data)
                        await redis_cache.cache_ohlcv(symbol, latest_ohlcv)

                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        continue

                if market_snapshot_data:
                    snapshot = MarketSnapshot(
                        timestamp=datetime.now(),
                        data=market_snapshot_data
                    )
                    await redis_cache.set_market_snapshot(snapshot)
                    await broadcast_market_data(snapshot)
                    logger.info(f"Market snapshot updated with {len(market_snapshot_data)} symbols")

                await asyncio.sleep(market_settings.DATA_COLLECTION_INTERVAL)

            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                await redis_cache.set_collection_status("error")
                await asyncio.sleep(5)


async def broadcast_market_data(snapshot: MarketSnapshot):
    """Broadcast market data to WebSocket clients"""
    if not active_connections:
        return

    data = snapshot.model_dump(mode='json')
    disconnected = set()

    for connection in active_connections:
        try:
            await connection.send_json(data)
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            disconnected.add(connection)

    active_connections.difference_update(disconnected)


# ========== Decision Engine Functions ==========

async def fetch_market_data_internal() -> Optional[MarketDataSnapshot]:
    """Fetch market data from internal cache"""
    try:
        snapshot = await redis_cache.get_market_snapshot()
        if snapshot:
            return MarketDataSnapshot(**snapshot.model_dump())
        return None
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return None


async def decision_loop():
    """Decision loop for AI agents"""
    logger.info("Starting decision loop...")
    await asyncio.sleep(10)  # Wait for market data

    while True:
        try:
            logger.info("=== Decision Round Started ===")

            market_data = await fetch_market_data_internal()
            if not market_data:
                logger.warning("No market data available")
                await asyncio.sleep(decision_settings.DECISION_INTERVAL)
                continue

            logger.info(f"Fetched market data with {len(market_data.data)} symbols")

            account_states: Dict[str, AccountState] = {}
            for agent_id in agent_manager.agents.keys():
                account_state = database.get_account_state(agent_id)
                if account_state:
                    account_states[agent_id] = account_state
                else:
                    agent = agent_manager.get_agent(agent_id)
                    account_states[agent_id] = AccountState(
                        agent_id=agent_id,
                        balance=agent.initial_balance,
                        total_value=agent.initial_balance,
                        positions=[],
                        total_pnl=0.0,
                        trade_count=0,
                        win_count=0,
                        loss_count=0
                    )

            decisions = await agent_manager.run_decision_round(market_data, account_states)

            for decision in decisions:
                try:
                    database.save_decision(decision)
                    action_str = decision.action.value if hasattr(decision.action, 'value') else decision.action
                    logger.info(f"Saved decision from {decision.agent_id}: {action_str} {decision.symbol or 'N/A'}")
                except Exception as e:
                    logger.error(f"Error saving decision: {e}")

            if executor and decisions:
                try:
                    logger.info(f"Executing {len(decisions)} decisions...")
                    execution_stats = await executor.execute_decisions_batch(decisions)
                    logger.info(
                        f"Execution completed: {execution_stats['executed']} executed, "
                        f"{execution_stats['skipped']} skipped, {execution_stats['failed']} failed"
                    )
                except Exception as e:
                    logger.error(f"Error executing decisions: {e}")

            logger.info(f"=== Decision Round Completed: {len(decisions)} decisions ===")
            await asyncio.sleep(decision_settings.DECISION_INTERVAL)

        except Exception as e:
            logger.error(f"Error in decision loop: {e}")
            await asyncio.sleep(decision_settings.DECISION_INTERVAL)


# ========== Trading Service Functions ==========

async def get_current_price_internal(symbol: str) -> Optional[float]:
    """Get current price from internal cache"""
    try:
        market_data = await redis_cache.get_market_data(symbol)
        if market_data:
            return market_data.ohlcv.close
        return None
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return None


async def multi_agent_trading_loop():
    """Multi-agent AI trading execution loop"""
    logger.info("🤖 Multi-Agent AI Trading loop started...")
    await asyncio.sleep(15)  # Wait for initialization

    symbols = ['BTC', 'ETH', 'SOL']
    iteration = 0

    while True:
        try:
            iteration += 1

            # Get current prices
            prices = {}
            for symbol in symbols:
                price = await get_current_price_internal(symbol)
                if price:
                    prices[symbol] = price

            # Update portfolio prices
            if prices:
                multi_portfolio.update_all_prices(prices)

            # Record performance snapshot
            if performance_tracker and iteration % 3 == 0:
                agent_values = {}
                for agent_id in AI_AGENTS:
                    agent_portfolio = multi_portfolio.get_portfolio(agent_id)
                    summary = agent_portfolio.get_summary()
                    agent_values[agent_id] = summary['total_value']
                performance_tracker.record_snapshot(agent_values)

            # Show leaderboard periodically
            if iteration % 6 == 1:
                leaderboard = multi_portfolio.get_leaderboard()
                logger.info("📊 Agent Leaderboard:")
                for entry in leaderboard[:3]:
                    logger.info(
                        f"  #{entry['rank']} {entry['agent_id']}: "
                        f"${entry['total_value']:.2f} ({entry['total_pnl_percent']:+.2f}%)"
                    )

            await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"Error in trading loop: {e}", exc_info=True)
            await asyncio.sleep(10)


# ========== API Routes ==========

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Unified Trading Platform",
        "version": "1.0.0",
        "status": "running",
        "services": {
            "market_data": "operational",
            "decision_engine": "operational",
            "trading_service": "operational"
        }
    }


# Health check endpoint
@app.get("/api/health")
async def health_check():
    redis_ok = await redis_cache.health_check() if redis_cache else False
    timescale_ok = timescale_db.health_check() if timescale_db else False
    db_ok = database.health_check() if database else False

    return {
        "status": "healthy" if (redis_ok and timescale_ok and db_ok) else "degraded",
        "redis": "ok" if redis_ok else "error",
        "timescale": "ok" if timescale_ok else "error",
        "database": "ok" if db_ok else "error",
        "agents": len(agent_manager.agents) if agent_manager else 0
    }


# WebSocket endpoint for market data
@app.websocket("/ws/market")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"New WebSocket connection. Total: {len(active_connections)}")

    try:
        snapshot = await redis_cache.get_market_snapshot()
        if snapshot:
            await websocket.send_json(snapshot.model_dump(mode='json'))

        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                logger.debug(f"Received from client: {message}")
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining: {len(active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


# Include API routes from services
# Note: Routes already have their paths defined (e.g., /api/market/, /api/agents/)
# So we include them without additional prefixes to avoid duplication
app.include_router(market_routes.router, tags=["Market Data"])
app.include_router(trading_routes.router, tags=["Trading"])


# Additional endpoints for compatibility
@app.get("/api/market/latest")
async def get_latest_market_data():
    """Get latest market data"""
    snapshot = await redis_cache.get_market_snapshot()
    if snapshot:
        return snapshot.model_dump(mode='json')
    return {"error": "No data available"}


@app.get("/api/agents")
async def list_agents():
    """List all agents"""
    if not agent_manager:
        return {"error": "Agent manager not initialized"}
    return {
        "agents": agent_manager.list_agents(),
        "count": len(agent_manager.agents)
    }


@app.get("/api/agents/leaderboard")
async def get_leaderboard():
    """Get leaderboard"""
    if not database:
        # Fallback to portfolio leaderboard
        if multi_portfolio:
            return multi_portfolio.get_leaderboard()
        return {"error": "Services not initialized"}

    session = database.Session()
    try:
        from decision_engine.app.database import AgentRecord

        agents = session.query(AgentRecord).order_by(AgentRecord.total_pnl.desc()).all()

        return {
            "leaderboard": [
                {
                    "rank": i + 1,
                    "agent_id": agent.id,
                    "name": agent.name,
                    "model": agent.model_type,
                    "total_pnl": agent.total_pnl,
                    "win_rate": (agent.win_count / agent.trade_count * 100) if agent.trade_count > 0 else 0,
                    "trade_count": agent.trade_count
                }
                for i, agent in enumerate(agents)
            ]
        }
    finally:
        session.close()


@app.get("/api/agents/{agent_id}/decisions")
async def get_agent_decisions(agent_id: str, limit: int = 50):
    """Get decision history for a specific agent"""
    if not database:
        return {"error": "Database not initialized", "decisions": [], "count": 0}

    session = database.Session()
    try:
        from decision_engine.app.database import DecisionRecord
        from sqlalchemy import desc

        # Query decisions for this agent, ordered by timestamp descending
        decisions_query = session.query(DecisionRecord).filter(
            DecisionRecord.agent_id == agent_id
        ).order_by(desc(DecisionRecord.timestamp)).limit(limit)

        decisions = decisions_query.all()

        return {
            "agent_id": agent_id,
            "decisions": [
                {
                    "id": str(decision.id),
                    "timestamp": decision.timestamp.isoformat() if decision.timestamp else None,
                    "action": decision.action,
                    "symbol": decision.symbol,
                    "quantity": float(decision.quantity) if decision.quantity else 0,
                    "reasoning": decision.reasoning,
                    "confidence": float(decision.confidence) if decision.confidence else 0,
                    "stop_loss": float(decision.stop_loss) if decision.stop_loss else None,
                    "take_profit": float(decision.take_profit) if decision.take_profit else None,
                    "leverage": float(decision.leverage) if decision.leverage else 1.0,
                    "current_price": float(decision.current_price) if decision.current_price else None,
                }
                for decision in decisions
            ],
            "count": len(decisions)
        }
    except Exception as e:
        logger.error(f"Error fetching decisions for {agent_id}: {e}")
        return {"error": str(e), "decisions": [], "count": 0}
    finally:
        session.close()


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
