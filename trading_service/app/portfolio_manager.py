"""
Portfolio Manager - 跟踪投资组合状态
"""
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PortfolioManager:
    """投资组合管理器 - 跟踪现金和持仓"""

    def __init__(self, initial_cash: float = 10000.0, current_cash: float = None):
        """
        初始化投资组合

        Args:
            initial_cash: 初始现金余额（用于计算盈亏）
            current_cash: 当前现金余额（如果从数据库恢复，可能与initial不同）
        """
        self.initial_cash = initial_cash
        self.cash = current_cash if current_cash is not None else initial_cash
        self.positions: Dict[str, Dict] = {}  # symbol -> position_info
        self.trade_history = []
        self.created_at = datetime.utcnow()

        logger.info(f"Initialized Portfolio: initial=${initial_cash:,.2f}, current=${self.cash:,.2f}")

    def get_portfolio(self) -> Dict:
        """获取完整的投资组合信息"""
        return {
            'cash': self.cash,
            'positions': self.positions,
            'initial_cash': self.initial_cash,
            'created_at': self.created_at.isoformat()
        }

    def get_position(self, symbol: str) -> Optional[Dict]:
        """获取特定交易对的持仓"""
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """检查是否有持仓"""
        return symbol in self.positions and self.positions[symbol]['quantity'] > 0

    def add_position(
        self,
        symbol: str,
        quantity: float,
        entry_price: float,
        side: str = 'long',
        leverage: float = 1.0,
        stop_loss: float = None,
        take_profit: float = None,
        reasoning: str = None
    ):
        """
        添加或增加持仓

        Args:
            symbol: 交易对
            quantity: 数量
            entry_price: 入场价格
            side: 方向 (long/short)
            leverage: 杠杆倍数（多倍ETF倍数）
            stop_loss: 止损价格
            take_profit: 止盈价格
            reasoning: 决策理由
        """
        if symbol in self.positions:
            # 已有持仓，检查方向和杠杆是否一致
            pos = self.positions[symbol]
            old_side = pos.get('side', 'long')
            old_leverage = pos.get('leverage', 1.0)

            if old_side != side:
                raise ValueError(
                    f"Cannot add {side} position to existing {old_side} position for {symbol}. "
                    f"Please close the {old_side} position first."
                )

            if old_leverage != leverage:
                raise ValueError(
                    f"Cannot add {leverage}x position to existing {old_leverage}x position for {symbol}. "
                    f"Please close the existing position first or use the same leverage."
                )

            old_qty = pos['quantity']
            old_price = pos['entry_price']

            # 计算新的平均价格
            new_qty = old_qty + quantity
            new_avg_price = (old_qty * old_price + quantity * entry_price) / new_qty

            pos['quantity'] = new_qty
            pos['entry_price'] = new_avg_price
            pos['updated_at'] = datetime.utcnow()

            # Update exit plan fields if provided
            if stop_loss is not None:
                pos['stop_loss'] = stop_loss
            if take_profit is not None:
                pos['take_profit'] = take_profit
            if reasoning is not None:
                pos['reasoning'] = reasoning

            logger.info(f"Updated position {symbol}: {old_qty} @ ${old_price:.2f} + {quantity} @ ${entry_price:.2f} = {new_qty} @ ${new_avg_price:.2f} (leverage: {leverage}x)")
        else:
            # 新持仓
            self.positions[symbol] = {
                'symbol': symbol,
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': entry_price,
                'side': side,
                'leverage': leverage,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reasoning': reasoning,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            logger.info(f"New position {symbol}: {quantity} @ ${entry_price:.2f} (side: {side}, leverage: {leverage}x)")

    def reduce_position(self, symbol: str, quantity: float) -> bool:
        """
        减少或关闭持仓

        Args:
            symbol: 交易对
            quantity: 要减少的数量

        Returns:
            是否成功
        """
        if symbol not in self.positions:
            logger.warning(f"No position found for {symbol}")
            return False

        pos = self.positions[symbol]
        if quantity > pos['quantity']:
            logger.warning(f"Cannot reduce {quantity}, only have {pos['quantity']}")
            return False

        pos['quantity'] -= quantity
        pos['updated_at'] = datetime.utcnow()

        # 如果持仓归零，删除
        if pos['quantity'] == 0:
            del self.positions[symbol]
            logger.info(f"Closed position {symbol}")
        else:
            logger.info(f"Reduced position {symbol}: {quantity} (remaining: {pos['quantity']})")

        return True

    def update_position_price(self, symbol: str, current_price: float):
        """
        更新持仓的当前价格

        Args:
            symbol: 交易对
            current_price: 当前价格
        """
        if symbol in self.positions:
            self.positions[symbol]['current_price'] = current_price
            self.positions[symbol]['updated_at'] = datetime.utcnow()

    def add_cash(self, amount: float):
        """增加现金（比如卖出收入）"""
        self.cash += amount
        logger.debug(f"Added cash: ${amount:,.2f}, new balance: ${self.cash:,.2f}")

    def deduct_cash(self, amount: float) -> bool:
        """
        扣除现金（比如买入）

        Returns:
            是否成功（余额是否足够）
        """
        if amount > self.cash:
            logger.warning(f"Insufficient cash: need ${amount:,.2f}, have ${self.cash:,.2f}")
            return False

        self.cash -= amount
        logger.debug(f"Deducted cash: ${amount:,.2f}, new balance: ${self.cash:,.2f}")
        return True

    def record_trade(self, trade_info: Dict):
        """记录交易历史"""
        trade_info['timestamp'] = datetime.utcnow()
        self.trade_history.append(trade_info)
        logger.info(f"Recorded trade: {trade_info}")

    def get_total_value(self) -> float:
        """
        获取总资产价值（现金 + 持仓市值）
        支持多倍ETF机制
        """
        # 计算所有持仓的当前市值（考虑leverage）
        positions_value = 0.0
        for pos in self.positions.values():
            entry_price = pos['entry_price']
            current_price = pos['current_price']
            quantity = pos['quantity']
            side = pos.get('side', 'long')
            leverage = pos.get('leverage', 1.0)

            # 多倍ETF机制：当前市值 = 初始成本 + 杠杆化盈亏
            if side == 'long':
                pnl = (current_price - entry_price) * quantity * leverage
            else:  # short
                pnl = (entry_price - current_price) * quantity * leverage

            position_value = entry_price * quantity + pnl
            # 防止市值为负（最多亏完本金）
            position_value = max(0, position_value)
            positions_value += position_value

        # 总资产 = 现金余额 + 持仓市值
        return self.cash + positions_value

    def get_pnl(self) -> tuple:
        """
        获取盈亏

        Returns:
            (total_pnl, total_pnl_percent)
        """
        total_value = self.get_total_value()
        total_pnl = total_value - self.initial_cash
        total_pnl_percent = (total_pnl / self.initial_cash * 100) if self.initial_cash > 0 else 0
        return total_pnl, total_pnl_percent

    def get_summary(self) -> Dict:
        """获取投资组合摘要"""
        total_value = self.get_total_value()
        total_pnl, total_pnl_percent = self.get_pnl()

        # 计算持仓市值（考虑leverage）
        positions_value = 0.0
        for pos in self.positions.values():
            entry_price = pos['entry_price']
            current_price = pos['current_price']
            quantity = pos['quantity']
            side = pos.get('side', 'long')
            leverage = pos.get('leverage', 1.0)

            # 多倍ETF机制
            if side == 'long':
                pnl = (current_price - entry_price) * quantity * leverage
            else:  # short
                pnl = (entry_price - current_price) * quantity * leverage

            position_value = entry_price * quantity + pnl
            position_value = max(0, position_value)
            positions_value += position_value

        return {
            'total_value': total_value,
            'cash': self.cash,
            'positions_value': positions_value,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
            'num_positions': len(self.positions),
            'num_trades': len(self.trade_history)
        }
