from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import aiohttp
from typing import Dict, Optional
from datetime import datetime
import logging
import sys
import os

# 添加父目录到路径，以便导入decision_engine模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'decision_engine'))

from .config import get_settings
from .execution.simulator import SimulatedExecutor, ExecutionResult
from .risk.risk_manager import RiskManager
from .portfolio_manager import PortfolioManager
from .multi_agent_portfolio import MultiAgentPortfolio
from .performance_tracker import PerformanceTracker
from . import api_routes

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading Service", version="1.0.0")

# Include API routes
app.include_router(api_routes.router)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI代理列表
AI_AGENTS = [
    'gpt5',
    'claude',
    'gemini',
    'grok',
    'deepseek',
    'qwen'
]

# 全局组件
settings = get_settings()
executor: SimulatedExecutor = None
risk_manager: RiskManager = None
multi_portfolio: MultiAgentPortfolio = None
performance_tracker: PerformanceTracker = None
# Backward compatibility
portfolio: PortfolioManager = None


@app.on_event("startup")
async def startup_event():
    """启动时初始化组件"""
    global executor, risk_manager, multi_portfolio, portfolio, performance_tracker

    logger.info("Initializing Multi-Agent Trading Service...")

    # 初始化多代理投资组合系统
    multi_portfolio = MultiAgentPortfolio(
        agents=AI_AGENTS,
        initial_cash=10000.0
    )

    # Backward compatibility - use first agent's portfolio
    portfolio = multi_portfolio.get_portfolio(AI_AGENTS[0])

    # 初始化模拟执行器
    executor = SimulatedExecutor(
        commission_rate=settings.COMMISSION_RATE,
        slippage_rate=settings.SLIPPAGE_RATE
    )

    # 初始化风险管理器
    risk_manager = RiskManager(
        max_position_size=1.0,  # 允许100%仓位，可以all-in
        max_drawdown=1.0  # 移除回撤限制
    )

    # 初始化性能跟踪器
    performance_tracker = PerformanceTracker(max_points=288)

    # 初始化API routes的multi_portfolio引用
    api_routes.init_multi_portfolio(multi_portfolio)
    api_routes.init_performance_tracker(performance_tracker)

    # 启动多代理交易执行循环
    logger.info("🤖 Starting multi-agent automated trading loop...")
    asyncio.create_task(multi_agent_trading_loop())

    logger.info(f"Trading Service started successfully - {len(AI_AGENTS)} AI agents are now trading!")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    logger.info("Shutting down Trading Service...")
    logger.info("Trading Service shutdown complete")


async def fetch_decisions() -> Optional[list]:
    """从Decision Engine获取最新决策"""
    try:
        # 这里我们直接访问数据库获取新决策
        # 在实际生产环境中，可以使用消息队列
        from decision_engine.app.database import Database

        db = Database(settings.database_url)

        # 获取所有代理的最新决策
        decisions = []

        session = db.Session()
        try:
            from decision_engine.app.database import DecisionRecord, AgentRecord

            # 获取所有代理
            agents = session.query(AgentRecord).all()

            for agent in agents:
                # 获取该代理最新的未执行决策
                latest_decision = session.query(DecisionRecord).filter_by(
                    agent_id=agent.id
                ).order_by(DecisionRecord.timestamp.desc()).first()

                if latest_decision:
                    decisions.append({
                        'id': latest_decision.id,
                        'agent_id': latest_decision.agent_id,
                        'timestamp': latest_decision.timestamp,
                        'action': latest_decision.action,
                        'symbol': latest_decision.symbol,
                        'quantity': latest_decision.quantity,
                        'stop_loss': latest_decision.stop_loss,
                        'take_profit': latest_decision.take_profit,
                        'current_price': latest_decision.current_price
                    })

        finally:
            session.close()

        return decisions

    except Exception as e:
        logger.error(f"Error fetching decisions: {e}")
        return None


async def get_current_price(symbol: str) -> Optional[float]:
    """获取当前价格"""
    market_data_url = f"http://market_data_service:8001/api/market/{symbol}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(market_data_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('price')
                else:
                    logger.warning(f"Failed to get price for {symbol}: HTTP {response.status}")

    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")

    return None


async def update_portfolio_prices():
    """更新投资组合中所有持仓的当前价格"""
    if not portfolio:
        return

    for symbol in list(portfolio.positions.keys()):
        current_price = await get_current_price(symbol)
        if current_price:
            portfolio.update_position_price(symbol, current_price)
            logger.debug(f"Updated {symbol} price to ${current_price:.2f}")


async def execute_decision(decision: dict):
    """执行交易决策"""
    from decision_engine.app.database import Database
    from decision_engine.app.models.trading import Trade

    db = Database(settings.database_url)

    agent_id = decision['agent_id']
    action = decision['action']
    symbol = decision['symbol']
    quantity = decision['quantity']

    logger.info(f"Executing decision for {agent_id}: {action} {symbol}")

    # 获取账户状态
    account_state = db.get_account_state(agent_id)
    if not account_state:
        logger.error(f"No account state for {agent_id}")
        return

    # 获取当前价格
    current_price = decision.get('current_price')
    if not current_price and symbol:
        current_price = await get_current_price(symbol)

    if not current_price and action != "hold":
        logger.error(f"No current price for {symbol}")
        return

    # 执行不同的动作
    if action == "hold":
        logger.info(f"{agent_id} decided to hold")
        return

    elif action == "buy":
        # 风险检查
        is_valid, message = risk_manager.validate_new_position(
            quantity=quantity,
            price=current_price,
            total_equity=account_state.total_value
        )

        if not is_valid:
            logger.warning(f"Risk check failed for {agent_id}: {message}")
            return

        # 执行买入
        result: ExecutionResult = executor.execute_buy(
            symbol=symbol,
            quantity=quantity,
            current_price=current_price,
            available_balance=account_state.balance
        )

        if result.success:
            # 创建持仓记录
            from decision_engine.app.models.trading import Position

            position = Position(
                symbol=symbol,
                quantity=result.executed_quantity,
                entry_price=result.executed_price,
                current_price=result.executed_price,
                unrealized_pnl=0.0,
                stop_loss=decision.get('stop_loss'),
                take_profit=decision.get('take_profit'),
                entry_time=datetime.now(),
                side="long"
            )

            position_id = db.create_position(position, agent_id)

            # 创建交易记录
            trade = Trade(
                agent_id=agent_id,
                decision_id=decision['id'],
                symbol=symbol,
                side="buy",
                quantity=result.executed_quantity,
                price=result.executed_price,
                commission=result.commission,
                executed_at=datetime.now(),
                is_simulated=True
            )

            db.save_trade(trade)

            # 更新账户余额
            amount_to_deduct = result.executed_price * result.executed_quantity + result.commission
            new_balance = account_state.balance - amount_to_deduct
            db.update_agent_balance(agent_id, new_balance, account_state.total_pnl)

            logger.info(
                f"BUY executed for {agent_id}: {result.executed_quantity} {symbol} "
                f"@ ${result.executed_price:.2f}"
            )

        else:
            logger.warning(f"BUY failed for {agent_id}: {result.message}")

    elif action == "sell" or action == "close":
        # 查找持仓
        positions = db.get_open_positions(agent_id)

        if not positions:
            logger.warning(f"No open positions for {agent_id}")
            return

        # 找到对应symbol的持仓
        target_position = None
        for pos in positions:
            if pos.symbol == symbol:
                target_position = pos
                break

        if not target_position:
            logger.warning(f"No position for {symbol} in {agent_id}")
            return

        # 执行卖出
        sell_quantity = quantity if action == "sell" else target_position.quantity

        result: ExecutionResult = executor.execute_sell(
            symbol=symbol,
            quantity=sell_quantity,
            current_price=current_price,
            available_quantity=target_position.quantity
        )

        if result.success:
            # 获取持仓信息
            entry_price = target_position.entry_price

            # 计算盈亏 (不含手续费)
            pnl_before_commission = (result.executed_price - entry_price) * result.executed_quantity

            # 计算返回金额: 卖出收入 - 手续费
            amount_to_return = result.executed_price * result.executed_quantity - result.commission

            # 净盈亏 (扣除手续费)
            pnl = pnl_before_commission - result.commission

            # 创建交易记录
            from decision_engine.app.models.trading import Trade

            trade = Trade(
                agent_id=agent_id,
                decision_id=decision['id'],
                symbol=symbol,
                side="sell",
                quantity=result.executed_quantity,
                price=result.executed_price,
                commission=result.commission,
                pnl=pnl,
                executed_at=datetime.now(),
                is_simulated=True
            )

            db.save_trade(trade)

            # 更新账户余额
            new_balance = account_state.balance + amount_to_return
            new_pnl = account_state.total_pnl + pnl
            db.update_agent_balance(agent_id, new_balance, new_pnl)

            # 关闭或更新持仓
            if result.executed_quantity >= target_position.quantity:
                db.close_position(target_position.id)
            else:
                # 部分平仓，更新数量
                pass

            logger.info(
                f"SELL executed for {agent_id}: {result.executed_quantity} {symbol} "
                f"@ ${result.executed_price:.2f}, PnL: ${pnl:.2f}"
            )

        else:
            logger.warning(f"SELL failed for {agent_id}: {result.message}")


async def update_positions():
    """更新所有持仓的当前价格和未实现盈亏"""
    from decision_engine.app.database import Database

    db = Database(settings.database_url)

    session = db.Session()
    try:
        from decision_engine.app.database import PositionRecord

        # 获取所有未平仓持仓
        positions = session.query(PositionRecord).filter_by(is_closed=False).all()

        for position in positions:
            # 获取当前价格
            current_price = await get_current_price(position.symbol)

            if current_price:
                # 计算未实现盈亏
                _, unrealized_pnl = executor.calculate_position_value(
                    entry_price=position.entry_price,
                    current_price=current_price,
                    quantity=position.quantity,
                    side=position.side
                )

                # 更新持仓
                db.update_position(position.id, current_price, unrealized_pnl)

                # 检查止损止盈
                trigger = executor.check_stop_loss_take_profit(
                    current_price=current_price,
                    entry_price=position.entry_price,
                    stop_loss=position.stop_loss,
                    take_profit=position.take_profit,
                    side=position.side
                )

                if trigger:
                    logger.info(
                        f"Position {position.id} triggered {trigger}: "
                        f"{position.symbol} @ ${current_price:.2f}"
                    )

                    # 自动平仓
                    result = executor.execute_sell(
                        symbol=position.symbol,
                        quantity=position.quantity,
                        current_price=current_price,
                        available_quantity=position.quantity
                    )

                    if result.success:
                        from decision_engine.app.models.trading import Trade

                        pnl = (result.executed_price - position.entry_price) * result.executed_quantity - result.commission

                        trade = Trade(
                            agent_id=position.agent_id,
                            symbol=position.symbol,
                            side="sell",
                            quantity=result.executed_quantity,
                            price=result.executed_price,
                            commission=result.commission,
                            pnl=pnl,
                            executed_at=datetime.now(),
                            is_simulated=True
                        )

                        db.save_trade(trade)
                        db.close_position(position.id)

                        # 更新余额
                        account_state = db.get_account_state(position.agent_id)
                        if account_state:
                            new_balance = account_state.balance + (
                                result.executed_price * result.executed_quantity - result.commission
                            )
                            new_pnl = account_state.total_pnl + pnl
                            db.update_agent_balance(position.agent_id, new_balance, new_pnl)

    finally:
        session.close()


async def get_ai_signal(symbol: str) -> Optional[dict]:
    """从决策引擎获取AI交易信号"""
    decision_engine_url = f"http://decision_engine:8002/api/signal/{symbol}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(decision_engine_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Failed to get AI signal for {symbol}: HTTP {response.status}")
    except Exception as e:
        logger.error(f"Error fetching AI signal for {symbol}: {e}")

    return None


async def execute_ai_trade(symbol: str, signal: dict):
    """根据AI信号执行交易"""
    if not portfolio or not executor:
        logger.error("Portfolio or executor not initialized")
        return

    action = signal.get('signal', 'hold').lower()
    confidence = signal.get('confidence', 0)

    # 只在高置信度时交易
    if confidence < 0.6:
        logger.debug(f"Skipping {symbol} trade - confidence too low: {confidence}")
        return

    # 获取当前价格
    current_price = await get_current_price(symbol)
    if not current_price:
        logger.warning(f"Cannot execute trade for {symbol} - no current price")
        return

    # 计算交易数量 (使用建议仓位大小，基于现金余额的百分比)
    suggested_size = signal.get('suggested_position_size', 0.1)
    max_investment = portfolio.cash * suggested_size
    quantity = max_investment / current_price if current_price > 0 else 0

    if action == 'buy':
        # 检查是否已有持仓
        if portfolio.has_position(symbol):
            logger.info(f"Already have position in {symbol}, skipping buy signal")
            return

        # 检查是否有足够现金
        cost = quantity * current_price
        commission = cost * settings.COMMISSION_RATE
        total_cost = cost + commission

        if total_cost > portfolio.cash:
            logger.warning(f"Insufficient cash for {symbol}: need ${total_cost:.2f}, have ${portfolio.cash:.2f}")
            return

        # 执行买入
        result = executor.execute_buy(
            symbol=symbol,
            quantity=quantity,
            current_price=current_price,
            available_balance=portfolio.cash
        )

        if result.success:
            # 扣除现金
            portfolio.deduct_cash(result.executed_price * result.executed_quantity + result.commission)

            # 添加持仓
            portfolio.add_position(
                symbol=symbol,
                quantity=result.executed_quantity,
                entry_price=result.executed_price,
                side='long',
                stop_loss=decision.get('stop_loss'),
                take_profit=decision.get('take_profit'),
                reasoning=decision.get('reasoning')
            )

            # 记录交易
            portfolio.record_trade({
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'side': 'buy',
                'quantity': result.executed_quantity,
                'price': result.executed_price,
                'commission': result.commission,
                'total_cost': result.executed_price * result.executed_quantity + result.commission,
                'signal_confidence': confidence,
                'reasoning': signal.get('reasoning', '')
            })

            logger.info(f"✅ BUY executed: {result.executed_quantity:.6f} {symbol} @ ${result.executed_price:.2f}, cost: ${result.executed_price * result.executed_quantity:.2f}")

        else:
            logger.warning(f"❌ BUY failed for {symbol}: {result.message}")

    elif action == 'sell' or action == 'close':
        # 检查是否有持仓
        if not portfolio.has_position(symbol):
            logger.debug(f"No position in {symbol} to sell")
            return

        position = portfolio.get_position(symbol)
        sell_quantity = position['quantity']

        # 执行卖出
        result = executor.execute_sell(
            symbol=symbol,
            quantity=sell_quantity,
            current_price=current_price,
            available_quantity=sell_quantity
        )

        if result.success:
            # 计算盈亏
            pnl = (result.executed_price - position['entry_price']) * result.executed_quantity - result.commission

            # 增加现金
            portfolio.add_cash(result.executed_price * result.executed_quantity - result.commission)

            # 减少持仓
            portfolio.reduce_position(symbol, result.executed_quantity)

            # 记录交易
            portfolio.record_trade({
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'side': 'sell',
                'quantity': result.executed_quantity,
                'price': result.executed_price,
                'commission': result.commission,
                'total_revenue': result.executed_price * result.executed_quantity - result.commission,
                'pnl': pnl,
                'signal_confidence': confidence,
                'reasoning': signal.get('reasoning', '')
            })

            logger.info(f"✅ SELL executed: {result.executed_quantity:.6f} {symbol} @ ${result.executed_price:.2f}, P&L: ${pnl:.2f}")

        else:
            logger.warning(f"❌ SELL failed for {symbol}: {result.message}")


async def get_agent_signal(agent_id: str, symbol: str) -> Optional[dict]:
    """从决策引擎获取指定代理的AI交易信号"""
    decision_engine_url = f"http://decision_engine:8002/api/agent/{agent_id}/signal/{symbol}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(decision_engine_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    # Fallback to generic signal endpoint
                    return await get_ai_signal(symbol)
    except Exception as e:
        logger.debug(f"Error fetching agent signal for {agent_id}/{symbol}: {e}")
        # Fallback to generic signal
        return await get_ai_signal(symbol)


async def execute_agent_trade(agent_id: str, symbol: str, signal: dict):
    """根据AI信号为特定代理执行交易"""
    if not multi_portfolio or not executor:
        logger.error("Multi-portfolio or executor not initialized")
        return

    # 获取该代理的投资组合
    agent_portfolio = multi_portfolio.get_portfolio(agent_id)
    if not agent_portfolio:
        logger.error(f"Portfolio not found for agent: {agent_id}")
        return

    action = signal.get('signal', 'hold').lower()
    confidence = signal.get('confidence', 0)

    # 只在高置信度时交易
    if confidence < 0.6:
        return

    # 获取当前价格
    current_price = await get_current_price(symbol)
    if not current_price:
        return

    # 计算交易数量
    suggested_size = signal.get('suggested_position_size', 0.1)
    max_investment = agent_portfolio.cash * suggested_size
    quantity = max_investment / current_price if current_price > 0 else 0

    if action == 'buy':
        if agent_portfolio.has_position(symbol):
            return

        cost = quantity * current_price
        commission = cost * settings.COMMISSION_RATE
        total_cost = cost + commission

        if total_cost > agent_portfolio.cash:
            return

        result = executor.execute_buy(
            symbol=symbol,
            quantity=quantity,
            current_price=current_price,
            available_balance=agent_portfolio.cash
        )

        if result.success:
            agent_portfolio.deduct_cash(result.executed_price * result.executed_quantity + result.commission)
            agent_portfolio.add_position(
                symbol=symbol,
                quantity=result.executed_quantity,
                entry_price=result.executed_price,
                side='long',
                stop_loss=decision.get('stop_loss'),
                take_profit=decision.get('take_profit'),
                reasoning=decision.get('reasoning')
            )
            agent_portfolio.record_trade({
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'side': 'buy',
                'quantity': result.executed_quantity,
                'price': result.executed_price,
                'commission': result.commission,
                'total_cost': result.executed_price * result.executed_quantity + result.commission,
                'signal_confidence': confidence,
                'reasoning': signal.get('reasoning', '')
            })

            logger.info(f"✅ [{agent_id}] BUY: {result.executed_quantity:.6f} {symbol} @ ${result.executed_price:.2f}")

    elif action == 'sell' or action == 'close':
        if not agent_portfolio.has_position(symbol):
            return

        position = agent_portfolio.get_position(symbol)
        sell_quantity = position['quantity']

        result = executor.execute_sell(
            symbol=symbol,
            quantity=sell_quantity,
            current_price=current_price,
            available_quantity=sell_quantity
        )

        if result.success:
            pnl = (result.executed_price - position['entry_price']) * result.executed_quantity - result.commission
            agent_portfolio.add_cash(result.executed_price * result.executed_quantity - result.commission)
            agent_portfolio.reduce_position(symbol, result.executed_quantity)
            agent_portfolio.record_trade({
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'side': 'sell',
                'quantity': result.executed_quantity,
                'price': result.executed_price,
                'commission': result.commission,
                'total_revenue': result.executed_price * result.executed_quantity - result.commission,
                'pnl': pnl,
                'signal_confidence': confidence,
                'reasoning': signal.get('reasoning', '')
            })

            logger.info(f"✅ [{agent_id}] SELL: {result.executed_quantity:.6f} {symbol} @ ${result.executed_price:.2f}, P&L: ${pnl:.2f}")


async def multi_agent_trading_loop():
    """多代理AI驱动的交易执行循环"""
    logger.info("🤖 Multi-Agent AI Trading loop started...")

    # 等待市场数据服务和决策引擎启动
    await asyncio.sleep(15)

    # 监控的交易对
    symbols = ['BTC', 'ETH', 'SOL']

    iteration = 0

    while True:
        try:
            iteration += 1

            # 获取当前价格
            prices = {}
            for symbol in symbols:
                price = await get_current_price(symbol)
                if price:
                    prices[symbol] = price

            # 更新所有代理的持仓价格
            if prices:
                multi_portfolio.update_all_prices(prices)

            # 记录性能快照
            if performance_tracker and iteration % 3 == 0:  # 每30秒记录一次
                agent_values = {}
                for agent_id in AI_AGENTS:
                    agent_portfolio = multi_portfolio.get_portfolio(agent_id)
                    summary = agent_portfolio.get_summary()
                    agent_values[agent_id] = summary['total_value']
                performance_tracker.record_snapshot(agent_values)

            # 每隔一段时间获取AI信号并执行交易
            if iteration % 6 == 1:  # 每60秒执行一次
                logger.info("🔍 Checking AI signals for all agents...")

                # 为每个代理获取信号并执行交易
                for agent_id in AI_AGENTS:
                    for symbol in symbols:
                        # 获取该代理的AI信号
                        signal = await get_agent_signal(agent_id, symbol)

                        if signal:
                            # 执行交易
                            await execute_agent_trade(agent_id, symbol, signal)

                        # 避免请求过快
                        await asyncio.sleep(0.5)

                # 显示排行榜
                leaderboard = multi_portfolio.get_leaderboard()
                logger.info("📊 Agent Leaderboard:")
                for entry in leaderboard[:3]:  # 显示前3名
                    logger.info(f"  #{entry['rank']} {entry['agent_id']}: ${entry['total_value']:.2f} ({entry['total_pnl_percent']:+.2f}%)")

            # 每10秒循环一次
            await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"Error in multi-agent trading loop: {e}", exc_info=True)
            await asyncio.sleep(10)


# 保留旧的单代理循环以便向后兼容
async def trading_execution_loop():
    """AI驱动的交易执行循环 (向后兼容)"""
    await multi_agent_trading_loop()


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Trading Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "executor": "simulated",
        "commission_rate": settings.COMMISSION_RATE,
        "slippage_rate": settings.SLIPPAGE_RATE
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.TRADING_SERVICE_PORT,
        reload=True
    )
