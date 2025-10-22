from typing import Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExecutionResult:
    """交易执行结果"""

    def __init__(
        self,
        success: bool,
        message: str,
        executed_price: Optional[float] = None,
        executed_quantity: Optional[float] = None,
        commission: Optional[float] = None,
        slippage: Optional[float] = None
    ):
        self.success = success
        self.message = message
        self.executed_price = executed_price
        self.executed_quantity = executed_quantity
        self.commission = commission
        self.slippage = slippage


class SimulatedExecutor:
    """模拟交易执行器"""

    def __init__(
        self,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005
    ):
        """
        Args:
            commission_rate: 手续费率（例如 0.001 = 0.1%）
            slippage_rate: 滑点率（例如 0.0005 = 0.05%）
        """
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate

        logger.info(
            f"Initialized SimulatedExecutor: "
            f"commission={commission_rate*100}%, slippage={slippage_rate*100}%"
        )

    def execute_buy(
        self,
        symbol: str,
        quantity: float,
        current_price: float,
        available_balance: float
    ) -> ExecutionResult:
        """执行买入订单

        Args:
            symbol: 交易对
            quantity: 数量
            current_price: 当前价格
            available_balance: 可用余额

        Returns:
            ExecutionResult对象
        """
        # 模拟滑点（买入时价格更高）
        slippage = current_price * self.slippage_rate
        executed_price = current_price * (1 + self.slippage_rate)

        # 计算成本
        notional_cost = executed_price * quantity
        commission = notional_cost * self.commission_rate
        total_cost = notional_cost + commission

        # 检查余额
        if total_cost > available_balance:
            return ExecutionResult(
                success=False,
                message=f"Insufficient balance: need ${total_cost:.2f}, have ${available_balance:.2f}"
            )

        logger.info(
            f"Simulated BUY: {quantity} {symbol} @ ${executed_price:.2f}, "
            f"cost=${total_cost:.2f}, commission=${commission:.2f}"
        )

        return ExecutionResult(
            success=True,
            message=f"Successfully bought {quantity} {symbol}",
            executed_price=executed_price,
            executed_quantity=quantity,
            commission=commission,
            slippage=slippage
        )

    def execute_sell(
        self,
        symbol: str,
        quantity: float,
        current_price: float,
        available_quantity: float
    ) -> ExecutionResult:
        """执行卖出订单

        Args:
            symbol: 交易对
            quantity: 数量
            current_price: 当前价格
            available_quantity: 可用数量

        Returns:
            ExecutionResult对象
        """
        # 检查持仓
        if quantity > available_quantity:
            return ExecutionResult(
                success=False,
                message=f"Insufficient position: need {quantity}, have {available_quantity}"
            )

        # 模拟滑点（卖出时价格更低）
        slippage = current_price * self.slippage_rate
        executed_price = current_price * (1 - self.slippage_rate)

        # 计算收入
        notional_revenue = executed_price * quantity
        commission = notional_revenue * self.commission_rate
        net_revenue = notional_revenue - commission

        logger.info(
            f"Simulated SELL: {quantity} {symbol} @ ${executed_price:.2f}, "
            f"revenue=${notional_revenue:.2f}, net=${net_revenue:.2f}, "
            f"commission=${commission:.2f}"
        )

        return ExecutionResult(
            success=True,
            message=f"Successfully sold {quantity} {symbol}",
            executed_price=executed_price,
            executed_quantity=quantity,
            commission=commission,
            slippage=slippage
        )

    def calculate_position_value(
        self,
        entry_price: float,
        current_price: float,
        quantity: float,
        side: str = "long",
        leverage: float = 1.0
    ) -> Tuple[float, float]:
        """计算持仓价值和盈亏（多倍ETF机制）

        Args:
            entry_price: 入场价格
            current_price: 当前价格
            quantity: 数量
            side: 方向（long/short）
            leverage: 杠杆倍数（多倍ETF倍数）

        Returns:
            (当前市值, 未实现盈亏)
        """
        # 多倍ETF机制：盈亏按照leverage倍数放大
        # 例如：10倍做多ETF，BTC涨1%，持仓盈利10%
        if side == "long":
            # 做多ETF：价格变化 * 数量 * 杠杆倍数
            pnl = (current_price - entry_price) * quantity * leverage
            # 当前市值 = 初始成本 + 盈亏
            current_value = entry_price * quantity + pnl
        else:  # short
            # 做空ETF：价格下跌赚钱，价格上涨亏钱
            pnl = (entry_price - current_price) * quantity * leverage
            # 当前市值 = 初始成本 + 盈亏
            current_value = entry_price * quantity + pnl

        # 防止市值为负（最多亏完本金）
        if current_value < 0:
            current_value = 0
            pnl = -entry_price * quantity

        return current_value, pnl

    def check_stop_loss_take_profit(
        self,
        current_price: float,
        entry_price: float,
        stop_loss: Optional[float],
        take_profit: Optional[float],
        side: str = "long"
    ) -> Optional[str]:
        """检查是否触发止损或止盈

        Args:
            current_price: 当前价格
            entry_price: 入场价格
            stop_loss: 止损价格
            take_profit: 止盈价格
            side: 方向

        Returns:
            "stop_loss" | "take_profit" | None
        """
        if side == "long":
            # 做多：价格下跌触发止损，上涨触发止盈
            if stop_loss and current_price <= stop_loss:
                return "stop_loss"
            if take_profit and current_price >= take_profit:
                return "take_profit"
        else:  # short
            # 做空：价格上涨触发止损，下跌触发止盈
            if stop_loss and current_price >= stop_loss:
                return "stop_loss"
            if take_profit and current_price <= take_profit:
                return "take_profit"

        return None

    def validate_order(
        self,
        action: str,
        symbol: str,
        quantity: Optional[float],
        price: float,
        balance: float
    ) -> Tuple[bool, str]:
        """验证订单

        Args:
            action: 动作（buy/sell/close）
            symbol: 交易对
            quantity: 数量
            price: 价格
            balance: 余额

        Returns:
            (是否有效, 错误消息)
        """
        if action not in ["buy", "sell", "close", "hold"]:
            return False, f"Invalid action: {action}"

        if action in ["buy", "sell"]:
            if not quantity or quantity <= 0:
                return False, "Quantity must be positive"

            if action == "buy":
                estimated_cost = price * quantity * (1 + self.commission_rate + self.slippage_rate)
                if estimated_cost > balance:
                    return False, f"Insufficient balance: need ${estimated_cost:.2f}"

        return True, ""
