from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class RiskManager:
    """风险管理器"""

    def __init__(
        self,
        max_position_size: float = 0.3,
        max_drawdown: float = 0.2
    ):
        """
        Args:
            max_position_size: 单个持仓最大占比（例如 0.3 = 30%）
            max_drawdown: 最大回撤（例如 0.2 = 20%）
        """
        self.max_position_size = max_position_size
        self.max_drawdown = max_drawdown

        logger.info(
            f"Initialized RiskManager: max_position={max_position_size*100}%, "
            f"max_drawdown={max_drawdown*100}%"
        )

    def validate_new_position(
        self,
        quantity: float,
        price: float,
        total_equity: float
    ) -> Tuple[bool, str]:
        """验证新仓位是否符合风险规则

        Args:
            quantity: 数量
            price: 价格
            total_equity: 总资产

        Returns:
            (是否通过, 原因)
        """
        # 计算仓位价值
        position_value = quantity * price

        # 检查仓位大小
        position_ratio = position_value / total_equity
        if position_ratio > self.max_position_size:
            max_allowed = (total_equity * self.max_position_size) / price
            return False, (
                f"Position size {position_ratio*100:.1f}% exceeds maximum "
                f"{self.max_position_size*100:.1f}%. "
                f"Max allowed quantity: {max_allowed:.4f}"
            )

        return True, ""

    def calculate_position_size(
        self,
        risk_per_trade: float,
        entry_price: float,
        stop_loss: float,
        total_equity: float
    ) -> float:
        """根据风险计算仓位大小

        Args:
            risk_per_trade: 每笔交易风险比例（例如 0.02 = 2%）
            entry_price: 入场价格
            stop_loss: 止损价格
            total_equity: 总资产

        Returns:
            建议的仓位数量
        """
        # 计算风险金额
        risk_amount = total_equity * risk_per_trade

        # 计算每单位的风险
        risk_per_unit = abs(entry_price - stop_loss)

        if risk_per_unit == 0:
            logger.warning("Stop loss equals entry price, cannot calculate position size")
            return 0

        # 基于风险计算数量
        quantity = risk_amount / risk_per_unit

        # 确保仓位不超过最大仓位限制
        max_value = total_equity * self.max_position_size
        max_quantity = max_value / entry_price
        quantity = min(quantity, max_quantity)

        logger.debug(
            f"Calculated position size: {quantity:.4f} "
            f"(risk=${risk_amount:.2f}, per_unit_risk=${risk_per_unit:.2f})"
        )

        return quantity

    def check_drawdown(
        self,
        current_equity: float,
        peak_equity: float
    ) -> Tuple[bool, float]:
        """检查回撤

        Args:
            current_equity: 当前资产
            peak_equity: 峰值资产

        Returns:
            (是否超过最大回撤, 当前回撤比例)
        """
        if peak_equity <= 0:
            return False, 0.0

        drawdown = (peak_equity - current_equity) / peak_equity

        if drawdown > self.max_drawdown:
            logger.warning(
                f"Drawdown {drawdown*100:.2f}% exceeds maximum {self.max_drawdown*100:.2f}%"
            )
            return True, drawdown

        return False, drawdown

    def validate_stop_loss(
        self,
        entry_price: float,
        stop_loss: Optional[float],
        side: str = "long",
        min_distance_pct: float = 0.01
    ) -> Tuple[bool, str]:
        """验证止损设置

        Args:
            entry_price: 入场价格
            stop_loss: 止损价格
            side: 方向
            min_distance_pct: 最小距离百分比（例如 0.01 = 1%）

        Returns:
            (是否有效, 原因)
        """
        if not stop_loss:
            return False, "Stop loss must be set"

        if side == "long":
            if stop_loss >= entry_price:
                return False, "Stop loss must be below entry price for long position"

            distance_pct = (entry_price - stop_loss) / entry_price

        else:  # short
            if stop_loss <= entry_price:
                return False, "Stop loss must be above entry price for short position"

            distance_pct = (stop_loss - entry_price) / entry_price

        if distance_pct < min_distance_pct:
            return False, (
                f"Stop loss too close to entry price: {distance_pct*100:.2f}% "
                f"(minimum {min_distance_pct*100:.2f}%)"
            )

        return True, ""

    def calculate_risk_reward_ratio(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: Optional[float],
        side: str = "long"
    ) -> Optional[float]:
        """计算风险收益比

        Args:
            entry_price: 入场价格
            stop_loss: 止损价格
            take_profit: 止盈价格
            side: 方向

        Returns:
            风险收益比（例如 2.0 表示 1:2）
        """
        if not take_profit:
            return None

        if side == "long":
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:  # short
            risk = stop_loss - entry_price
            reward = entry_price - take_profit

        if risk <= 0:
            return None

        return reward / risk
