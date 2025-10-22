import asyncio
from typing import Dict, List, Optional
import logging
from datetime import datetime

from .base_agent import BaseAgent
from ..models.trading import TradingDecision, AccountState, MarketDataSnapshot

logger = logging.getLogger(__name__)


class AgentManager:
    """管理所有交易代理"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.decision_queue: asyncio.Queue = asyncio.Queue()
        logger.info("AgentManager initialized")

    def register_agent(self, agent: BaseAgent):
        """注册代理

        Args:
            agent: BaseAgent实例
        """
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.name} ({agent.agent_id}) using {agent.model_name}")

    def unregister_agent(self, agent_id: str):
        """注销代理

        Args:
            agent_id: 代理ID
        """
        if agent_id in self.agents:
            agent = self.agents.pop(agent_id)
            logger.info(f"Unregistered agent: {agent.name} ({agent_id})")
        else:
            logger.warning(f"Agent {agent_id} not found")

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取代理

        Args:
            agent_id: 代理ID

        Returns:
            BaseAgent实例或None
        """
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict]:
        """列出所有代理

        Returns:
            代理信息列表
        """
        return [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "model_name": agent.model_name,
                "initial_balance": agent.initial_balance
            }
            for agent in self.agents.values()
        ]

    async def run_decision_round(
        self,
        market_data: MarketDataSnapshot,
        account_states: Dict[str, AccountState]
    ) -> List[TradingDecision]:
        """运行一轮决策 - 所有代理并发决策

        Args:
            market_data: 市场数据快照
            account_states: 代理ID -> 账户状态的映射

        Returns:
            决策列表
        """
        if not self.agents:
            logger.warning("No agents registered")
            return []

        logger.info(f"Starting decision round for {len(self.agents)} agents")

        tasks = []
        for agent_id, agent in self.agents.items():
            # 获取账户状态
            account_state = account_states.get(agent_id)

            if not account_state:
                logger.warning(f"No account state for agent {agent_id}")
                continue

            # 创建决策任务
            task = asyncio.create_task(
                self._make_decision_with_timeout(
                    agent,
                    market_data,
                    account_state
                )
            )
            tasks.append((agent_id, task))

        # 等待所有决策完成
        decisions = []
        for agent_id, task in tasks:
            try:
                decision = await task
                decisions.append(decision)

                # 将决策放入队列
                await self.decision_queue.put(decision)

                # Handle both enum and string action types
                action_str = decision.action.value if hasattr(decision.action, 'value') else decision.action
                logger.info(
                    f"Agent {agent_id} decision: {action_str} "
                    f"{decision.symbol or 'N/A'}"
                )

            except Exception as e:
                logger.error(f"Agent {agent_id} decision failed: {e}")

        logger.info(f"Decision round completed. {len(decisions)} decisions made")
        return decisions

    async def _make_decision_with_timeout(
        self,
        agent: BaseAgent,
        market_data: MarketDataSnapshot,
        account_state: AccountState,
        timeout: int = 60
    ) -> TradingDecision:
        """带超时的决策

        Args:
            agent: 代理实例
            market_data: 市场数据
            account_state: 账户状态
            timeout: 超时时间（秒）

        Returns:
            TradingDecision对象
        """
        try:
            return await asyncio.wait_for(
                agent.make_decision(market_data, account_state),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Agent {agent.agent_id} decision timeout after {timeout}s")
            return agent._create_hold_decision("决策超时 - Decision timeout occurred", confidence=0.0)
        except Exception as e:
            logger.error(f"Agent {agent.agent_id} decision error: {e}")
            return agent._create_hold_decision(f"决策错误 - Error: {str(e)}", confidence=0.0)

    async def get_next_decision(self) -> TradingDecision:
        """从队列获取下一个决策（阻塞）

        Returns:
            TradingDecision对象
        """
        return await self.decision_queue.get()

    def get_decision_queue_size(self) -> int:
        """获取决策队列大小

        Returns:
            队列中的决策数量
        """
        return self.decision_queue.qsize()

    async def health_check(self) -> Dict:
        """健康检查

        Returns:
            健康状态
        """
        return {
            "agents_count": len(self.agents),
            "agents": self.list_agents(),
            "queue_size": self.get_decision_queue_size(),
            "status": "healthy"
        }
