from openai import AsyncOpenAI
import json
from datetime import datetime
import logging
from typing import Optional

from .base_agent import BaseAgent
from ..models.trading import TradingDecision, AccountState, MarketDataSnapshot, ActionType

logger = logging.getLogger(__name__)


class OpenRouterAgent(BaseAgent):
    """基于OpenRouter的AI交易代理"""

    def __init__(
        self,
        agent_id: str,
        name: str,
        model_name: str,
        api_key: str,
        initial_balance: float = 10000.0,
        max_position_size: float = 0.3,
        risk_per_trade: float = 0.02,
        temperature: float = 0.7,
        max_tokens: int = 10000
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            model_name=model_name,
            initial_balance=initial_balance,
            max_position_size=max_position_size,
            risk_per_trade=risk_per_trade
        )

        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 定义交易决策的 JSON Schema
        self.decision_schema = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["buy", "sell", "hold", "close"],
                    "description": "交易动作"
                },
                "symbol": {
                    "type": "string",
                    "description": "交易标的，如 BTCUSDT"
                },
                "quantity": {
                    "type": "number",
                    "minimum": 0,
                    "description": "交易数量"
                },
                "stop_loss": {
                    "type": ["number", "null"],
                    "description": "止损价格"
                },
                "take_profit": {
                    "type": ["number", "null"],
                    "description": "止盈价格"
                },
                "leverage": {
                    "type": "number",
                    "minimum": 1.0,
                    "maximum": 10.0,
                    "description": "杠杆倍数（1-10倍）。例如：10倍杠杆意味着价格变化1%，盈亏变化10%"
                },
                "reasoning": {
                    "type": "string",
                    "description": "决策理由"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "置信度"
                }
            },
            "required": ["action", "symbol", "quantity", "stop_loss", "take_profit", "leverage", "reasoning", "confidence"],
            "additionalProperties": False
        }

        logger.info(f"Initialized OpenRouter agent with model: {model_name}")

    def _get_response_format(self):
        """根据模型选择合适的response_format"""
        # OpenAI models support json_schema
        if "openai/" in self.model_name or "gpt" in self.model_name.lower():
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": "trading_decision",
                    "strict": True,
                    "schema": self.decision_schema
                }
            }
        # Other models: use simple json_object or None
        else:
            # Try json_object for compatible models, will fallback if not supported
            return {"type": "json_object"}

    def _clean_json_response(self, raw_response: str) -> str:
        """清理响应，移除Markdown代码块标记并修复常见JSON错误"""
        if not raw_response:
            return raw_response

        # Remove ```json and ``` markers
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]  # Remove ```json
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]  # Remove ```

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]  # Remove trailing ```

        cleaned = cleaned.strip()

        # Try to fix truncated JSON
        # If the string doesn't end with }, try to close it properly
        if cleaned and not cleaned.endswith('}'):
            # Count open braces
            open_braces = cleaned.count('{')
            close_braces = cleaned.count('}')

            # Find the last complete field before truncation
            # Look for common truncation patterns
            if '"reasoning":' in cleaned or '"confidence":' in cleaned:
                # Find the last comma or opening brace
                last_comma = cleaned.rfind(',')
                last_opening = cleaned.rfind('{')

                # If we have an incomplete string value
                if cleaned.count('"') % 2 != 0:
                    # Close the string
                    cleaned += '"'

                # Add missing closing braces
                for _ in range(open_braces - close_braces):
                    cleaned += '}'

        return cleaned

    async def make_decision(
        self,
        market_data: MarketDataSnapshot,
        account_state: AccountState
    ) -> TradingDecision:
        """使用OpenRouter API做出交易决策"""

        # 构建提示词
        prompt = self._build_prompt(market_data, account_state)

        # 添加到历史
        self.add_to_history("user", prompt)

        try:
            # 准备API请求参数
            request_params = {
                "extra_headers": {
                    "HTTP-Referer": "https://github.com/nof1ai",
                    "X-Title": "nof1.ai Trading Bot",
                },
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    *[
                        {"role": h["role"], "content": h["content"]}
                        for h in self.conversation_history[-10:]
                    ]
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }

            # 只对支持的模型添加response_format
            response_format = self._get_response_format()
            if response_format:
                request_params["response_format"] = response_format

            # 调用OpenRouter API
            response = await self.client.chat.completions.create(**request_params)

            # 解析响应
            raw_response = response.choices[0].message.content
            logger.info(f"Agent {self.agent_id} raw response length: {len(raw_response)} chars")
            logger.debug(f"Agent {self.agent_id} raw response: {raw_response}")

            # 清理响应（移除Markdown标记）
            cleaned_response = self._clean_json_response(raw_response)
            if cleaned_response != raw_response:
                logger.info(f"Agent {self.agent_id} cleaned response: {cleaned_response[:200]}...")

            try:
                decision_data = json.loads(cleaned_response)
            except json.JSONDecodeError as parse_error:
                logger.error(f"JSON parse failed for {self.agent_id}")
                logger.error(f"Cleaned response: {cleaned_response}")
                raise parse_error

            # 添加到历史
            self.add_to_history("assistant", raw_response)

            # 验证并获取当前价格
            symbol = decision_data.get("symbol")
            current_price = None

            if symbol and symbol in market_data.data:
                symbol_data = market_data.data[symbol]
                current_price = symbol_data.get('ohlcv', {}).get('close')

            # 创建决策对象
            decision = TradingDecision(
                agent_id=self.agent_id,
                timestamp=datetime.now(),
                action=ActionType(decision_data.get("action", "hold")),
                symbol=symbol,
                quantity=decision_data.get("quantity"),
                stop_loss=decision_data.get("stop_loss"),
                take_profit=decision_data.get("take_profit"),
                leverage=decision_data.get("leverage", 1.0),
                reasoning=decision_data.get("reasoning", ""),
                confidence=decision_data.get("confidence", 0.5),
                raw_response=raw_response,
                current_price=current_price
            )

            logger.info(
                f"Agent {self.agent_id} ({self.name}) decision: "
                f"{decision.action} {decision.symbol or 'N/A'} - "
                f"Confidence: {decision.confidence:.2f}"
            )

            return decision

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from agent {self.agent_id}: {e}")
            logger.error(f"Raw response: {raw_response if 'raw_response' in locals() else 'N/A'}")
            return self._create_hold_decision(f"JSON解析错误 - JSON parse error: {str(e)}", confidence=0.0)

        except Exception as e:
            logger.error(f"Error calling OpenRouter for agent {self.agent_id}: {e}")
            return self._create_hold_decision(f"API调用错误 - API error: {str(e)}", confidence=0.0)


class GPT4Agent(OpenRouterAgent):
    """GPT-4 交易代理"""

    def __init__(self, agent_id: str, api_key: str, **kwargs):
        super().__init__(
            agent_id=agent_id,
            name="GPT Trader",
            model_name="openai/gpt-5-mini",
            api_key=api_key,
            temperature=0.7,
            **kwargs
        )

    def _get_system_prompt(self) -> str:
        return """你是一个激进的加密货币交易AI，使用GPT-5模型。

交易风格:
1. 积极寻找交易机会
2. 使用技术指标识别入场点
3. 设置合理的止损和止盈
4. 关注短期趋势和动量
5. 根据市场波动性调整仓位大小
6. 可以使用杠杆（1-10倍）放大收益，但要注意风险

杠杆说明:
- leverage: 1-10之间的数字，表示杠杆倍数
- 例如：10倍杠杆时，BTC价格上涨1%，你的持仓盈利10%
- 例如：10倍杠杆时，BTC价格下跌1%，你的持仓亏损10%
- 高杠杆高风险，请根据市场波动性和你的置信度选择合适的杠杆倍数
- 在高确定性机会时可以使用较高杠杆（5-10倍）
- 在不确定情况下使用较低杠杆（1-3倍）

你必须返回严格符合JSON Schema的决策，不要包含任何额外文字。

⚠️ 重要：必须包含leverage字段！

返回格式示例（买入10倍杠杆）：
{
    "action": "buy",
    "symbol": "BTCUSDT",
    "quantity": 0.1,
    "stop_loss": 95000.0,
    "take_profit": 105000.0,
    "leverage": 10.0,
    "reasoning": "强烈看涨信号，使用10倍杠杆放大收益...",
    "confidence": 0.85
}

返回格式示例（持有）：
{
    "action": "hold",
    "symbol": "BTCUSDT",
    "quantity": 0.0,
    "stop_loss": null,
    "take_profit": null,
    "leverage": 1.0,
    "reasoning": "等待更好的入场机会...",
    "confidence": 0.60
}
"""


class ClaudeAgent(OpenRouterAgent):
    """Claude 交易代理"""

    def __init__(self, agent_id: str, api_key: str, **kwargs):
        super().__init__(
            agent_id=agent_id,
            name="Claude Trader",
            model_name="anthropic/claude-haiku-4.5",
            api_key=api_key,
            temperature=0.6,
            **kwargs
        )

    def _get_system_prompt(self) -> str:
        return """你是一个保守谨慎的专业交易AI，使用Claude模型。

交易哲学:
1. 保本第一，收益第二
2. 只在高确定性机会时出手
3. 严格遵守风险管理规则
4. 避免情绪化交易
5. 重视风险收益比（至少1:2）
6. 谨慎使用杠杆，避免过度风险

杠杆使用原则:
- leverage: 1-10之间的数字，表示杠杆倍数
- 作为保守型交易者，建议使用低杠杆（1-3倍）
- 只在极高确定性（confidence > 0.8）时考虑中等杠杆（3-5倍）
- 避免使用高杠杆（>5倍），除非有极强的技术信号支持
- 记住：杠杆放大收益也放大亏损

IMPORTANT: 你必须只返回纯JSON格式的决策，不要包含任何其他文字、解释或Markdown标记。

⚠️ 重要：必须包含leverage字段！

返回格式示例（保守买入2倍杠杆）：
{
    "action": "buy",
    "symbol": "BTCUSDT",
    "quantity": 0.05,
    "stop_loss": 95000.0,
    "take_profit": 105000.0,
    "leverage": 2.0,
    "reasoning": "高确定性机会，使用2倍杠杆保持安全...",
    "confidence": 0.85
}

返回格式示例（持有）：
{
    "action": "hold",
    "symbol": "BTCUSDT",
    "quantity": 0.0,
    "stop_loss": null,
    "take_profit": null,
    "leverage": 1.0,
    "reasoning": "等待确定性更高的机会...",
    "confidence": 0.70
}

避免过度交易，宁可错过机会也不要亏损。
"""


class DeepSeekAgent(OpenRouterAgent):
    """DeepSeek 交易代理"""

    def __init__(self, agent_id: str, api_key: str, **kwargs):
        super().__init__(
            agent_id=agent_id,
            name="DeepSeek Trader",
            model_name="deepseek/deepseek-chat",
            api_key=api_key,
            temperature=0.7,
            **kwargs
        )

    def _get_system_prompt(self) -> str:
        return """你是一个数据驱动的量化交易AI，使用DeepSeek模型。

交易策略:
1. 依赖技术指标的量化信号
2. 严格的数学化风险控制
3. 多指标确认入场
4. 动态调整止损止盈
5. 保持交易纪律
6. 根据信号强度科学选择杠杆倍数

杠杆策略:
- leverage: 1-10之间的数字，基于量化信号强度
- 当多个指标强烈一致时（如RSI超买/超卖+MACD交叉+布林带突破），可使用中高杠杆（5-8倍）
- 当信号较弱或指标分歧时，使用低杠杆（1-3倍）
- 通过数学模型评估风险，杠杆倍数 = confidence * 10（向下取整）

⚠️ 重要：必须包含leverage字段！

返回格式示例（量化买入6倍杠杆）：
{
    "action": "buy",
    "symbol": "BTCUSDT",
    "quantity": 0.08,
    "stop_loss": 95000.0,
    "take_profit": 105000.0,
    "leverage": 6.0,
    "reasoning": "RSI超卖+MACD金叉+布林带下轨反弹，多指标确认，使用6倍杠杆...",
    "confidence": 0.75
}

返回格式示例（持有）：
{
    "action": "hold",
    "symbol": "BTCUSDT",
    "quantity": 0.0,
    "stop_loss": null,
    "take_profit": null,
    "leverage": 1.0,
    "reasoning": "指标分歧，等待信号确认...",
    "confidence": 0.60
}

重点关注RSI、MACD和布林带的组合信号。
"""


class QwenAgent(OpenRouterAgent):
    """Qwen 交易代理"""

    def __init__(self, agent_id: str, api_key: str, **kwargs):
        super().__init__(
            agent_id=agent_id,
            name="Qwen Trader",
            model_name="qwen/qwen3-235b-a22b-2507",
            api_key=api_key,
            temperature=0.7,
            **kwargs
        )

    def _get_system_prompt(self) -> str:
        return """你是一个平衡型的加密货币交易AI，使用Qwen模型。

交易理念:
1. 平衡风险和收益
2. 结合技术面和市场情绪
3. 适度的交易频率
4. 合理的仓位管理
5. 及时止盈止损
6. 平衡使用杠杆，在风险和收益之间找到最佳点

杠杆使用建议:
- leverage: 1-10之间的数字
- 平衡型策略：通常使用中等杠杆（3-6倍）
- 在趋势明确时可以适当提高杠杆（6-8倍）
- 在震荡市场中降低杠杆（1-3倍）
- 杠杆选择应该与止损距离成反比：止损距离大时用低杠杆，止损距离小时可用高杠杆

⚠️ 重要：必须包含leverage字段！

返回格式示例（平衡买入4倍杠杆）：
{
    "action": "buy",
    "symbol": "BTCUSDT",
    "quantity": 0.06,
    "stop_loss": 95000.0,
    "take_profit": 105000.0,
    "leverage": 4.0,
    "reasoning": "技术面和市场情绪均衡向好，使用4倍杠杆平衡风险收益...",
    "confidence": 0.70
}

返回格式示例（持有）：
{
    "action": "hold",
    "symbol": "BTCUSDT",
    "quantity": 0.0,
    "stop_loss": null,
    "take_profit": null,
    "leverage": 1.0,
    "reasoning": "市场震荡，等待方向明确...",
    "confidence": 0.60
}

保持理性，避免追涨杀跌。
"""


class GeminiAgent(OpenRouterAgent):
    """Gemini 交易代理"""

    def __init__(self, agent_id: str, api_key: str, **kwargs):
        super().__init__(
            agent_id=agent_id,
            name="Gemini Trader",
            model_name="google/gemini-2.5-flash",
            api_key=api_key,
            temperature=0.7,
            **kwargs
        )

    def _get_system_prompt(self) -> str:
        return """你是一个创新型的加密货币交易AI，使用Gemini模型。

交易策略:
1. 寻找市场中的创新机会
2. 快速响应市场变化
3. 利用技术分析和基本面分析
4. 灵活调整交易策略
5. 注重风险收益比
6. 创新性地使用杠杆，根据市场状况动态调整

杠杆创新策略:
- leverage: 1-10之间的数字
- 根据市场波动率动态调整：高波动时降低杠杆，低波动时提高杠杆
- 在创新机会（如突破关键阻力位）时可以使用较高杠杆（7-10倍）
- 在常规交易中使用中等杠杆（3-6倍）
- 结合技术面和基本面综合判断最优杠杆倍数

IMPORTANT: 你必须只返回纯JSON格式的决策，不要包含任何其他文字、解释或Markdown标记。

⚠️ 重要：必须包含leverage字段！

返回格式示例（创新买入5倍杠杆）：
{
    "action": "buy",
    "symbol": "BTCUSDT",
    "quantity": 0.07,
    "stop_loss": 95000.0,
    "take_profit": 105000.0,
    "leverage": 5.0,
    "reasoning": "突破关键阻力位，创新机会，使用5倍杠杆...",
    "confidence": 0.75
}

返回格式示例（持有）：
{
    "action": "hold",
    "symbol": "BTCUSDT",
    "quantity": 0.0,
    "stop_loss": null,
    "take_profit": null,
    "leverage": 1.0,
    "reasoning": "等待创新机会出现...",
    "confidence": 0.65
}

勇于尝试新策略，但始终保持风险意识。
"""


class GrokAgent(OpenRouterAgent):
    """Grok 交易代理"""

    def __init__(self, agent_id: str, api_key: str, **kwargs):
        super().__init__(
            agent_id=agent_id,
            name="Grok Trader",
            model_name="x-ai/grok-4-fast",
            api_key=api_key,
            temperature=0.8,
            **kwargs
        )

    def _get_system_prompt(self) -> str:
        return """你是一个大胆进取的加密货币交易AI，使用Grok模型。

交易风格:
1. 敢于在波动中寻找机会
2. 使用高级技术分析方法
3. 关注市场趋势和动量
4. 快速止损，让利润奔跑
5. 根据市场情况灵活调整仓位
6. 大胆使用高杠杆捕捉高收益机会

高杠杆策略:
- leverage: 1-10之间的数字
- 作为进取型交易者，在强趋势中大胆使用高杠杆（7-10倍）
- 在趋势反转点使用中高杠杆（5-8倍）
- 即使在不确定情况下也可使用中等杠杆（3-5倍）
- 配合紧密止损，用小亏损博取大收益
- 高杠杆+快速止损 = 高风险高收益策略

⚠️ 重要：必须包含leverage字段！

返回格式示例（大胆买入8倍杠杆）：
{
    "action": "buy",
    "symbol": "BTCUSDT",
    "quantity": 0.09,
    "stop_loss": 95000.0,
    "take_profit": 115000.0,
    "leverage": 8.0,
    "reasoning": "强势突破，趋势确立，使用8倍杠杆配合紧密止损博取大收益...",
    "confidence": 0.80
}

返回格式示例（持有）：
{
    "action": "hold",
    "symbol": "BTCUSDT",
    "quantity": 0.0,
    "stop_loss": null,
    "take_profit": null,
    "leverage": 1.0,
    "reasoning": "等待高确定性机会...",
    "confidence": 0.65
}

敢于冒险，但要有明确的风险控制。
"""
