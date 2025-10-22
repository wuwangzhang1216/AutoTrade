from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import aiohttp
from typing import Dict
from datetime import datetime
import logging

from .config import get_settings
from .database import Database
from .agents.agent_manager import AgentManager
from .agents.openrouter_agent import GPT4Agent, ClaudeAgent, DeepSeekAgent, QwenAgent, GeminiAgent, GrokAgent
from .models.trading import MarketDataSnapshot, AccountState
from .executor import DecisionExecutor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Decision Engine", version="1.0.0")

# Create API router
api_router = APIRouter()

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "decision_engine",
        "timestamp": datetime.utcnow().isoformat(),
        "agents_initialized": agent_manager is not None if 'agent_manager' in globals() else False
    }

@api_router.get("/api/signal/{symbol}")
async def get_trading_signal(symbol: str, strategy: str = None):
    """Get trading signal for a symbol"""
    # Return demo signal for now
    return {
        "symbol": symbol,
        "signal": "hold",
        "confidence": 0.75,
        "strategy": strategy or "trend_following",
        "reasoning": "Demo signal - AI agents not initialized",
        "suggested_position_size": 0.1,
        "timestamp": datetime.utcnow().isoformat()
    }

@api_router.get("/api/strategies")
async def get_strategies():
    """Get available trading strategies"""
    return ["trend_following", "mean_reversion", "momentum"]

# Include routes
app.include_router(api_router)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局组件
settings = get_settings()
database: Database = None
agent_manager: AgentManager = None
executor: DecisionExecutor = None


@app.on_event("startup")
async def startup_event():
    """启动时初始化组件"""
    global database, agent_manager, executor

    logger.info("Initializing Decision Engine...")

    try:
        # 初始化数据库
        database = Database(settings.database_url)
        database.initialize()
        logger.info("Database initialized successfully")

        # 初始化Agent Manager
        agent_manager = AgentManager()
        logger.info("Agent Manager initialized")

        # 初始化Decision Executor
        executor = DecisionExecutor()
        logger.info("Decision Executor initialized")

        # 创建并注册AI代理 - wrapped in try-catch to handle OpenAI compatibility issues
        try:
            api_key = settings.OPENROUTER_API_KEY

            # GPT-5 Agent
            gpt5_agent = GPT4Agent(
                agent_id="gpt5",
                api_key=api_key,
                initial_balance=settings.INITIAL_BALANCE,
                max_position_size=settings.MAX_POSITION_SIZE,
                risk_per_trade=settings.RISK_PER_TRADE
            )
            agent_manager.register_agent(gpt5_agent)
            database.create_agent(
                agent_id=gpt5_agent.agent_id,
                name=gpt5_agent.name,
                model_type=gpt5_agent.model_name,
                initial_balance=gpt5_agent.initial_balance
            )
            logger.info("GPT-5 Agent initialized")

            # Claude Agent
            claude_agent = ClaudeAgent(
                agent_id="claude",
                api_key=api_key,
                initial_balance=settings.INITIAL_BALANCE,
                max_position_size=settings.MAX_POSITION_SIZE,
                risk_per_trade=settings.RISK_PER_TRADE
            )
            agent_manager.register_agent(claude_agent)
            database.create_agent(
                agent_id=claude_agent.agent_id,
                name=claude_agent.name,
                model_type=claude_agent.model_name,
                initial_balance=claude_agent.initial_balance
            )
            logger.info("Claude Agent initialized")

            # DeepSeek Agent
            deepseek_agent = DeepSeekAgent(
                agent_id="deepseek",
                api_key=api_key,
                initial_balance=settings.INITIAL_BALANCE,
                max_position_size=settings.MAX_POSITION_SIZE,
                risk_per_trade=settings.RISK_PER_TRADE
            )
            agent_manager.register_agent(deepseek_agent)
            database.create_agent(
                agent_id=deepseek_agent.agent_id,
                name=deepseek_agent.name,
                model_type=deepseek_agent.model_name,
                initial_balance=deepseek_agent.initial_balance
            )
            logger.info("DeepSeek Agent initialized")

            # Qwen Agent
            qwen_agent = QwenAgent(
                agent_id="qwen",
                api_key=api_key,
                initial_balance=settings.INITIAL_BALANCE,
                max_position_size=settings.MAX_POSITION_SIZE,
                risk_per_trade=settings.RISK_PER_TRADE
            )
            agent_manager.register_agent(qwen_agent)
            database.create_agent(
                agent_id=qwen_agent.agent_id,
                name=qwen_agent.name,
                model_type=qwen_agent.model_name,
                initial_balance=qwen_agent.initial_balance
            )
            logger.info("Qwen Agent initialized")

            # Gemini Agent
            gemini_agent = GeminiAgent(
                agent_id="gemini",
                api_key=api_key,
                initial_balance=settings.INITIAL_BALANCE,
                max_position_size=settings.MAX_POSITION_SIZE,
                risk_per_trade=settings.RISK_PER_TRADE
            )
            agent_manager.register_agent(gemini_agent)
            database.create_agent(
                agent_id=gemini_agent.agent_id,
                name=gemini_agent.name,
                model_type=gemini_agent.model_name,
                initial_balance=gemini_agent.initial_balance
            )
            logger.info("Gemini Agent initialized")

            # Grok Agent
            grok_agent = GrokAgent(
                agent_id="grok",
                api_key=api_key,
                initial_balance=settings.INITIAL_BALANCE,
                max_position_size=settings.MAX_POSITION_SIZE,
                risk_per_trade=settings.RISK_PER_TRADE
            )
            agent_manager.register_agent(grok_agent)
            database.create_agent(
                agent_id=grok_agent.agent_id,
                name=grok_agent.name,
                model_type=grok_agent.model_name,
                initial_balance=grok_agent.initial_balance
            )
            logger.info("Grok Agent initialized")

            logger.info(f"Registered {len(agent_manager.agents)} agents")

            # 启动决策循环
            asyncio.create_task(decision_loop())

        except Exception as e:
            logger.error(f"Error initializing AI agents: {e}")
            logger.warning("Decision Engine will run without AI agents - using fallback logic")
            # Continue without AI agents - service will still provide demo responses

        logger.info("Decision Engine started successfully")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        logger.info("Decision Engine started in fallback mode")
        # Don't raise - allow service to start for health checks


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    logger.info("Shutting down Decision Engine...")
    logger.info("Decision Engine shutdown complete")


async def fetch_market_data() -> MarketDataSnapshot:
    """从Market Data Service获取市场数据"""
    market_data_url = f"http://{settings.MARKET_DATA_HOST}:{settings.MARKET_DATA_PORT}/api/market/latest"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(market_data_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return MarketDataSnapshot(**data)
                else:
                    logger.error(f"Failed to fetch market data: {response.status}")
                    return None

    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return None


async def decision_loop():
    """决策循环 - 定期运行所有代理的决策"""
    logger.info("Starting decision loop...")

    # 等待Market Data Service启动
    await asyncio.sleep(10)

    while True:
        try:
            logger.info("=== Decision Round Started ===")

            # 获取市场数据
            market_data = await fetch_market_data()

            if not market_data:
                logger.warning("No market data available, skipping this round")
                await asyncio.sleep(settings.DECISION_INTERVAL)
                continue

            logger.info(f"Fetched market data with {len(market_data.data)} symbols")

            # 获取所有代理的账户状态
            account_states: Dict[str, AccountState] = {}

            for agent_id in agent_manager.agents.keys():
                account_state = database.get_account_state(agent_id)

                if account_state:
                    account_states[agent_id] = account_state
                else:
                    # 创建初始账户状态
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

            # 运行决策轮
            decisions = await agent_manager.run_decision_round(
                market_data,
                account_states
            )

            # 保存所有决策到数据库
            for decision in decisions:
                try:
                    database.save_decision(decision)
                    # Handle both enum and string action types
                    action_str = decision.action.value if hasattr(decision.action, 'value') else decision.action
                    logger.info(
                        f"Saved decision from {decision.agent_id}: "
                        f"{action_str} {decision.symbol or 'N/A'}"
                    )
                except Exception as e:
                    logger.error(f"Error saving decision: {e}")

            # 执行决策（发送订单到Trading Service）
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

            # 等待下一轮
            await asyncio.sleep(settings.DECISION_INTERVAL)

        except Exception as e:
            logger.error(f"Error in decision loop: {e}")
            await asyncio.sleep(settings.DECISION_INTERVAL)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Decision Engine",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    db_ok = database.health_check()
    agent_health = await agent_manager.health_check()

    status = "healthy" if db_ok else "unhealthy"

    return {
        "status": status,
        "database": "ok" if db_ok else "error",
        "agents": agent_health
    }


@app.get("/api/agents")
async def list_agents():
    """列出所有代理"""
    return {
        "agents": agent_manager.list_agents(),
        "count": len(agent_manager.agents)
    }


@app.get("/api/agents/{agent_id}/account")
async def get_agent_account(agent_id: str):
    """获取代理的账户状态"""
    account_state = database.get_account_state(agent_id)

    if not account_state:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    return account_state.model_dump(mode='json')


@app.get("/api/agents/{agent_id}/decisions")
async def get_agent_decisions(agent_id: str, limit: int = 20):
    """获取代理的决策历史"""
    decisions = database.get_recent_decisions(agent_id, limit)

    return {
        "agent_id": agent_id,
        "decisions": [
            {
                "id": d.id,
                "timestamp": d.timestamp.isoformat(),
                "action": d.action,
                "symbol": d.symbol,
                "quantity": d.quantity,
                "stop_loss": d.stop_loss,
                "take_profit": d.take_profit,
                "reasoning": d.reasoning,
                "confidence": d.confidence
            }
            for d in decisions
        ],
        "count": len(decisions)
    }


@app.get("/api/agents/{agent_id}/positions")
async def get_agent_positions(agent_id: str):
    """获取代理的持仓"""
    positions = database.get_open_positions(agent_id)

    return {
        "agent_id": agent_id,
        "positions": [
            {
                "id": p.id,
                "symbol": p.symbol,
                "quantity": p.quantity,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "unrealized_pnl": p.unrealized_pnl,
                "entry_time": p.entry_time.isoformat()
            }
            for p in positions
        ],
        "count": len(positions)
    }


@app.get("/api/leaderboard")
async def get_leaderboard():
    """获取排行榜"""
    session = database.Session()
    try:
        from .database import AgentRecord

        agents = session.query(AgentRecord).order_by(
            AgentRecord.total_pnl.desc()
        ).all()

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.DECISION_ENGINE_PORT,
        reload=True
    )
