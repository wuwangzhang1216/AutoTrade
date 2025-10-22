"""
Decision Executor - Executes trading decisions by sending orders to Trading Service
"""
import asyncio
import aiohttp
import logging
from typing import Optional
from datetime import datetime

from .models.trading import TradingDecision, ActionType
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DecisionExecutor:
    """执行交易决策"""

    def __init__(self):
        self.trading_service_url = f"http://{settings.TRADING_SERVICE_HOST}:{settings.TRADING_SERVICE_PORT}"
        logger.info(f"Decision Executor initialized with Trading Service at {self.trading_service_url}")

    async def execute_decision(self, decision: TradingDecision) -> Optional[dict]:
        """
        执行单个交易决策

        Args:
            decision: 交易决策对象

        Returns:
            交易执行结果或None
        """
        # Handle both enum and string action types
        action_str = decision.action.value if hasattr(decision.action, 'value') else decision.action

        # Only execute buy and sell decisions, skip hold
        if action_str.lower() == 'hold':
            logger.debug(f"Skipping HOLD decision from {decision.agent_id}")
            return None

        # Skip decisions without symbol or quantity
        if not decision.symbol or not decision.quantity:
            logger.warning(f"Skipping decision from {decision.agent_id}: missing symbol or quantity")
            return None

        try:
            # Prepare order data
            order_data = {
                "symbol": decision.symbol.replace("USDT", ""),  # Convert BTCUSDT -> BTC
                "side": action_str.lower(),  # buy or sell
                "quantity": decision.quantity,
                "order_type": "market",  # Use market orders for now
                "agent_id": decision.agent_id,  # Track which agent made this order
                "decision_id": getattr(decision, 'id', None),  # Link to decision if available
                "leverage": decision.leverage,  # 多倍ETF倍数
                "stop_loss": decision.stop_loss,
                "take_profit": decision.take_profit,
                "reasoning": decision.reasoning
            }

            # Add limit price if available
            if decision.current_price:
                order_data["price"] = decision.current_price

            logger.info(f"Executing {action_str.upper()} order for {decision.agent_id}: {decision.symbol} x{decision.quantity}")
            logger.info(f"Order data being sent: {order_data}")

            # Send order to Trading Service
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.trading_service_url}/api/orders",
                    json=order_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(
                            f"Order executed successfully for {decision.agent_id}: "
                            f"{result.get('id')} - {action_str} {decision.symbol} x{decision.quantity}"
                        )
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Failed to execute order for {decision.agent_id}: "
                            f"HTTP {response.status} - {error_text}"
                        )
                        return None

        except asyncio.TimeoutError:
            logger.error(f"Timeout executing order for {decision.agent_id}")
            return None
        except Exception as e:
            logger.error(f"Error executing order for {decision.agent_id}: {e}")
            return None

    async def execute_decisions_batch(self, decisions: list[TradingDecision]) -> dict:
        """
        批量执行多个交易决策

        Args:
            decisions: 决策列表

        Returns:
            执行统计信息
        """
        if not decisions:
            return {"executed": 0, "skipped": 0, "failed": 0}

        logger.info(f"Executing batch of {len(decisions)} decisions")

        executed = 0
        skipped = 0
        failed = 0

        # Execute all decisions concurrently
        tasks = [self.execute_decision(decision) for decision in decisions]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Decision {i} execution failed with exception: {result}")
                failed += 1
            elif result is None:
                skipped += 1
            else:
                executed += 1

        stats = {
            "total": len(decisions),
            "executed": executed,
            "skipped": skipped,
            "failed": failed
        }

        logger.info(f"Batch execution completed: {stats}")
        return stats
