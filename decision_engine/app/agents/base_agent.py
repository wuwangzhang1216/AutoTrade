from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..models.trading import (
    Position, AccountState, TradingDecision,
    ActionType, MarketDataSnapshot
)

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """AI交易代理基类"""

    def __init__(
        self,
        agent_id: str,
        name: str,
        model_name: str,
        initial_balance: float = 10000.0,
        max_position_size: float = 0.3,
        risk_per_trade: float = 0.02
    ):
        self.agent_id = agent_id
        self.name = name
        self.model_name = model_name
        self.initial_balance = initial_balance
        self.max_position_size = max_position_size
        self.risk_per_trade = risk_per_trade

        # 对话历史（用于上下文）
        self.conversation_history: List[Dict] = []
        self.max_history_length = 10

        logger.info(f"Initialized agent: {self.name} ({self.agent_id}) using {self.model_name}")

    @abstractmethod
    async def make_decision(
        self,
        market_data: MarketDataSnapshot,
        account_state: AccountState
    ) -> TradingDecision:
        """做出交易决策 - 子类必须实现

        Args:
            market_data: 市场数据快照
            account_state: 账户状态

        Returns:
            TradingDecision对象
        """
        pass

    def add_to_history(self, role: str, content: str):
        """添加到对话历史

        Args:
            role: 角色（user/assistant）
            content: 内容
        """
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        # 保持历史长度
        if len(self.conversation_history) > self.max_history_length * 2:
            self.conversation_history = self.conversation_history[-self.max_history_length * 2:]

    def get_context_summary(self) -> str:
        """获取上下文摘要"""
        if not self.conversation_history:
            return "这是你的第一次决策。"

        recent_decisions = [
            h for h in self.conversation_history[-6:]
            if h['role'] == 'assistant'
        ]

        if not recent_decisions:
            return "你还没有做过决策。"

        summary = "## 你最近的决策:\n"
        for i, decision in enumerate(recent_decisions, 1):
            content = decision['content']
            # 截取前100个字符
            preview = content[:100] + "..." if len(content) > 100 else content
            summary += f"{i}. {preview}\n"

        return summary

    def _create_hold_decision(self, reason: str, timestamp: datetime = None, confidence: float = 1.0) -> TradingDecision:
        """创建持仓（不交易）决策

        Args:
            reason: 原因
            timestamp: 时间戳
            confidence: 置信度（默认1.0）

        Returns:
            TradingDecision对象
        """
        return TradingDecision(
            agent_id=self.agent_id,
            timestamp=timestamp or datetime.now(),
            action=ActionType.HOLD,
            reasoning=reason,
            confidence=confidence,
            raw_response=""
        )

    def _build_prompt(
        self,
        market_data: MarketDataSnapshot,
        account_state: AccountState
    ) -> str:
        """构建提示词

        Args:
            market_data: 市场数据
            account_state: 账户状态

        Returns:
            提示词字符串
        """
        # 基础信息
        prompt = f"""# 当前时间
{market_data.timestamp.strftime("%Y-%m-%d %H:%M:%S")}

# 账户状态
- 可用余额: ${account_state.balance:.2f}
- 总资产价值: ${account_state.total_value:.2f}
- 总盈亏: ${account_state.total_pnl:.2f} ({account_state.total_pnl/self.initial_balance*100:+.2f}%)
- 交易次数: {account_state.trade_count}
- 胜率: {account_state.win_rate*100:.1f}%

"""

        # 当前持仓
        prompt += "# 当前持仓\n"
        if account_state.positions:
            for pos in account_state.positions:
                stop_loss_str = f"${pos.stop_loss:.2f}" if pos.stop_loss else 'N/A'
                take_profit_str = f"${pos.take_profit:.2f}" if pos.take_profit else 'N/A'
                prompt += f"""
- {pos.symbol}:
  * 数量: {pos.quantity} ({pos.side})
  * 入场价: ${pos.entry_price:.2f}
  * 当前价: ${pos.current_price:.2f}
  * 未实现盈亏: ${pos.unrealized_pnl:.2f} ({pos.pnl_percentage:+.2f}%)
  * 止损: {stop_loss_str}
  * 止盈: {take_profit_str}
  * 入场时间: {pos.entry_time.strftime("%Y-%m-%d %H:%M:%S")}
"""
        else:
            prompt += "无持仓\n"

        # 市场数据
        prompt += "\n# 市场数据\n"
        for symbol, data in market_data.data.items():
            ohlcv = data.get('ohlcv', {})
            indicators = data.get('indicators', {})

            prompt += f"""
## {symbol}
当前价格: ${ohlcv.get('close', 0):.2f}
- 开盘: ${ohlcv.get('open', 0):.2f}
- 最高: ${ohlcv.get('high', 0):.2f}
- 最低: ${ohlcv.get('low', 0):.2f}
- 成交量: {ohlcv.get('volume', 0):,.0f}

技术指标:
- RSI(14): {indicators.get('rsi', 0):.2f} {'超买' if indicators.get('rsi', 50) > 70 else '超卖' if indicators.get('rsi', 50) < 30 else '中性'}
- MACD: {indicators.get('macd', 0):.4f}, 信号线: {indicators.get('macd_signal', 0):.4f}, 柱状图: {indicators.get('macd_hist', 0):.4f}
- SMA(20): ${indicators.get('sma_20', 0):.2f}, SMA(50): ${indicators.get('sma_50', 0):.2f}
- 布林带: 上轨 ${indicators.get('bollinger_upper', 0):.2f}, 中轨 ${indicators.get('bollinger_middle', 0):.2f}, 下轨 ${indicators.get('bollinger_lower', 0):.2f}
"""

        # 历史决策回顾
        prompt += "\n# 历史决策回顾\n"
        prompt += self.get_context_summary()

        prompt += "\n\n请基于以上信息做出交易决策。"

        return prompt

    def _get_system_prompt(self) -> str:
        """获取系统提示词 - 子类可以覆盖"""
        return """你是一个专业的加密货币交易AI。你的任务是基于市场数据做出明智的交易决策。

关键原则:
1. 风险管理第一 - 永远设置止损
2. 不要过度交易 - 只在有明确信号时交易
3. 使用技术分析 - RSI、MACD、布林带等
4. 考虑市场趋势和动量
5. 记录你的推理过程
6. 根据市场波动性调整仓位大小，仓位越大止损应该越严格

**重要：系统支持做多和做空双向交易**
- 看涨时使用 "buy" 开仓做多（Long）
- 看跌时使用 "sell" 开仓做空（Short）
- 想平仓时使用 "close" 平掉当前持仓
- 观望时使用 "hold" 不交易

**做多（Long）盈利逻辑**: 价格上涨盈利，价格下跌亏损
**做空（Short）盈利逻辑**: 价格下跌盈利，价格上涨亏损

你必须以JSON格式回复，格式如下:
{
    "action": "buy/sell/close/hold",  // buy=做多, sell=做空, close=平仓, hold=观望
    "symbol": "BTCUSDT",
    "quantity": 0.1,
    "stop_loss": 95000,  // 做多时低于入场价，做空时高于入场价
    "take_profit": 105000,  // 做多时高于入场价，做空时低于入场价
    "reasoning": "详细解释你的决策逻辑、方向判断和仓位大小选择...",
    "confidence": 0.75
}

注意:
- 做多示例: action="buy", stop_loss < entry_price, take_profit > entry_price
- 做空示例: action="sell", stop_loss > entry_price, take_profit < entry_price
- 如果你决定不交易，action应该是"hold"
"""
