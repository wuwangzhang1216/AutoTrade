"""
Core trading engine for AutoTrade AI system
Supports multi-currency leveraged paper trading
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from utils.logger import logger, log_trade, log_success, log_error
from utils.helpers import format_currency, format_percentage, calculate_percentage_change


class PositionSide(Enum):
    """Position side enum"""
    LONG = "LONG"
    SHORT = "SHORT"


class OrderType(Enum):
    """Order type enum"""
    OPEN_LONG = "OPEN_LONG"
    OPEN_SHORT = "OPEN_SHORT"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"


@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    side: PositionSide
    amount: float
    entry_price: float
    leverage: int
    margin: float
    open_time: datetime
    commission_rate: float = 0.001  # BUG FIX: Add commission rate for accurate liquidation
    unrealized_pnl: float = 0.0
    liquidation_price: float = 0.0

    def __post_init__(self):
        """Calculate liquidation price after initialization"""
        self.liquidation_price = self._calculate_liquidation_price()

    def _calculate_liquidation_price(self) -> float:
        """
        Calculate liquidation price with improved accuracy

        BUG FIX: Now considers:
        1. Opening fee (already paid)
        2. Closing fee (will be paid at liquidation)
        3. Maintenance margin (using conservative 90% loss threshold)

        Real exchanges typically liquidate before 100% loss to cover fees and ensure
        the exchange doesn't lose money. We use 90% loss as a conservative estimate.
        """
        # Conservative threshold: liquidate when loss reaches 90% of margin
        # This accounts for closing fees and maintenance margin requirements
        MAINTENANCE_MARGIN_RATIO = 0.90  # Liquidate at 90% loss instead of 100%

        # Calculate available margin after accounting for fees
        # Opening fee already deducted, but we need to reserve for closing fee
        total_fee_buffer = 2 * self.commission_rate  # Open + close fees

        # Effective loss percentage before liquidation
        # Formula: (1 / leverage) * maintenance_ratio - fee_buffer
        effective_loss_percent = (1.0 / self.leverage) * MAINTENANCE_MARGIN_RATIO - total_fee_buffer

        if self.side == PositionSide.LONG:
            # Long: liquidation when price drops by effective_loss_percent
            liquidation_price = self.entry_price * (1 - effective_loss_percent)
        else:
            # Short: liquidation when price rises by effective_loss_percent
            liquidation_price = self.entry_price * (1 + effective_loss_percent)

        return liquidation_price

    def update_unrealized_pnl(self, current_price: float) -> float:
        """
        Update and return unrealized PnL

        Args:
            current_price: Current market price

        Returns:
            Unrealized PnL
        """
        position_value = self.entry_price * self.amount

        if self.side == PositionSide.LONG:
            price_change_percent = (current_price - self.entry_price) / self.entry_price
        else:  # SHORT
            price_change_percent = (self.entry_price - current_price) / self.entry_price

        # PnL with leverage
        self.unrealized_pnl = self.margin * price_change_percent * self.leverage
        return self.unrealized_pnl

    def is_liquidated(self, current_price: float) -> bool:
        """Check if position should be liquidated"""
        if self.side == PositionSide.LONG:
            return current_price <= self.liquidation_price
        else:
            return current_price >= self.liquidation_price


@dataclass
class Order:
    """Represents a trade order"""
    timestamp: datetime
    order_type: OrderType
    symbol: str
    amount: float
    price: float
    fee: float
    pnl: Optional[float] = None
    reason: Optional[str] = None


class TradingEngine:
    """
    Core trading engine with multi-currency support
    """

    def __init__(
        self,
        initial_capital: float,
        leverage: int = 10,
        commission_rate: float = 0.001,
        max_positions: int = 5
    ):
        """
        Initialize trading engine

        Args:
            initial_capital: Starting capital in USDT
            leverage: Default leverage multiplier
            commission_rate: Trading fee percentage
            max_positions: Maximum concurrent positions
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital  # Available capital
        self.leverage = leverage
        self.commission_rate = commission_rate
        self.max_positions = max_positions

        # Trading state
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.equity_history: List[Tuple[datetime, float]] = []

        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_fees = 0.0

        log_success(f"Trading Engine initialized with {format_currency(initial_capital)}")
        logger.info(f"Leverage: {leverage}x | Fee: {commission_rate * 100}% | Max Positions: {max_positions}")

        # BUG FIX: Validate configuration on startup
        self._validate_configuration()

        # BUG FIX: Restore capital and statistics from database BEFORE restoring positions
        # This ensures capital is correctly restored to its last known state
        self._restore_capital_from_database()

        # HEROKU FIX: Restore open positions from database after restart
        self._restore_positions_from_database()

    def _validate_trade_inputs(self, symbol: str, amount: float, price: float) -> bool:
        """
        Validate trading inputs to prevent errors

        BUG FIX: Comprehensive input validation for all trading operations

        Args:
            symbol: Trading pair
            amount: Position size
            price: Price

        Returns:
            True if inputs are valid
        """
        # Validate symbol
        if not symbol or not isinstance(symbol, str):
            log_error(f"Invalid symbol: {symbol}")
            return False

        if not symbol.strip():
            log_error("Symbol cannot be empty")
            return False

        # Validate amount
        if not isinstance(amount, (int, float)):
            log_error(f"Invalid amount type: {type(amount)}. Expected number.")
            return False

        if amount <= 0:
            log_error(f"Amount must be positive, got: {amount}")
            return False

        if amount > 1e10:  # Sanity check for extremely large amounts
            log_error(f"Amount {amount} exceeds reasonable limits")
            return False

        # Validate price
        if not isinstance(price, (int, float)):
            log_error(f"Invalid price type: {type(price)}. Expected number.")
            return False

        if price <= 0:
            log_error(f"Price must be positive, got: {price}")
            return False

        if price > 1e15:  # Sanity check for extremely large prices
            log_error(f"Price {price} exceeds reasonable limits")
            return False

        # All validations passed
        return True

    def _validate_configuration(self):
        """
        Validate trading configuration to ensure safe operation

        BUG FIX: Checks that position sizing and max positions are compatible
        to prevent capital over-allocation issues.
        """
        # BUG FIX: Import here to avoid circular dependency
        # Use specific exception types instead of bare except
        try:
            from config import TradingPairsConfig
            position_size_pct = TradingPairsConfig.POSITION_SIZE_PERCENT
        except (ImportError, AttributeError) as e:
            # If we can't import, assume reasonable defaults
            logger.warning(f"Could not load position size config: {e}. Using default 15%")
            position_size_pct = 15.0

        # Calculate maximum capital utilization if all positions are filled
        max_utilization = (self.max_positions * position_size_pct) / 100.0

        # Warning thresholds
        SAFE_UTILIZATION = 0.85  # 85%
        DANGER_UTILIZATION = 0.95  # 95%

        if max_utilization > DANGER_UTILIZATION:
            logger.error(
                f"⚠️  CONFIGURATION WARNING: Maximum capital utilization is {max_utilization*100:.1f}%!"
            )
            logger.error(
                f"   Max Positions: {self.max_positions} × Position Size: {position_size_pct}% = {max_utilization*100:.1f}%"
            )
            logger.error(
                f"   This does not leave enough buffer for fees, slippage, or unrealized losses."
            )
            logger.error(
                f"   RECOMMENDATION: Reduce position size to {SAFE_UTILIZATION*100/self.max_positions:.1f}% "
                f"or reduce max positions to {int(SAFE_UTILIZATION*100/position_size_pct)}"
            )
        elif max_utilization > SAFE_UTILIZATION:
            logger.warning(
                f"⚠️  Capital utilization is {max_utilization*100:.1f}% "
                f"({self.max_positions} × {position_size_pct}%). "
                f"Consider leaving more buffer for fees and losses."
            )
        else:
            logger.info(
                f"✓ Capital utilization is safe: {max_utilization*100:.1f}% "
                f"({self.max_positions} × {position_size_pct}%)"
            )

        # Validate leverage
        if self.leverage > 20:
            logger.warning(
                f"⚠️  High leverage detected: {self.leverage}x. "
                f"This significantly increases liquidation risk!"
            )

        # Validate commission rate
        if self.commission_rate > 0.002:  # 0.2%
            logger.warning(
                f"⚠️  High commission rate: {self.commission_rate*100}%. "
                f"This may significantly impact profitability."
            )

    def _restore_capital_from_database(self):
        """
        Restore capital and trading statistics from database after restart

        BUG FIX: Capital and stats are stored in-memory only, causing them to reset
        on restart. This method restores the last known state from AccountSnapshot table.
        """
        try:
            from database import get_session, AccountSnapshot
            session = get_session()

            # Get the most recent account snapshot
            latest_snapshot = session.query(AccountSnapshot)\
                .order_by(AccountSnapshot.timestamp.desc())\
                .first()

            if latest_snapshot:
                # Restore capital (available capital, NOT total equity)
                restored_capital = latest_snapshot.capital

                # Restore trading statistics
                restored_total_fees = latest_snapshot.total_fees
                restored_total_trades = latest_snapshot.total_trades
                restored_winning_trades = latest_snapshot.winning_trades
                restored_losing_trades = latest_snapshot.losing_trades

                # Sanity check: capital should not be negative or unreasonably high
                if restored_capital < 0:
                    logger.warning(
                        f"Database shows negative capital ({format_currency(restored_capital)}). "
                        f"Using initial capital instead."
                    )
                elif restored_capital > self.initial_capital * 100:
                    logger.warning(
                        f"Database shows unreasonably high capital ({format_currency(restored_capital)}). "
                        f"This is >100x initial capital. Using initial capital instead."
                    )
                else:
                    # Capital looks reasonable - restore it
                    self.capital = restored_capital
                    self.total_fees = restored_total_fees
                    self.total_trades = restored_total_trades
                    self.winning_trades = restored_winning_trades
                    self.losing_trades = restored_losing_trades

                    logger.info(
                        f"✓ Restored capital from database: {format_currency(self.capital)} "
                        f"(Total trades: {self.total_trades}, W/L: {self.winning_trades}/{self.losing_trades})"
                    )

                    # Calculate and log PnL
                    total_pnl = self.capital - self.initial_capital
                    pnl_percent = (total_pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0

                    if total_pnl > 0:
                        logger.info(f"✓ Current profit: {format_currency(total_pnl)} (+{format_percentage(pnl_percent)})")
                    elif total_pnl < 0:
                        logger.warning(f"⚠️  Current loss: {format_currency(total_pnl)} ({format_percentage(pnl_percent)})")
            else:
                logger.info("No previous account snapshot found. Starting with fresh capital.")

            session.close()

        except Exception as e:
            logger.error(f"Failed to restore capital from database: {e}")
            logger.info("Using initial capital instead.")

    def _restore_positions_from_database(self):
        """
        Restore open positions from database after restart

        HEROKU FIX: Positions are stored in memory, so they're lost on restart.
        This method rebuilds positions from database trades to recover state.

        BUG FIX: Capital is now restored BEFORE this method runs, so we should
        NOT deduct margin again (it was already deducted when position was opened).
        """
        try:
            from database import get_session, Trade
            session = get_session()

            # Get all OPEN trades
            open_trades = session.query(Trade).filter(
                Trade.order_type.in_(['OPEN_LONG', 'OPEN_SHORT'])
            ).all()

            restored_positions_count = 0
            total_restored_margin = 0.0

            for trade in open_trades:
                symbol = trade.symbol

                # Check if this position was closed
                close_trade = session.query(Trade).filter(
                    Trade.symbol == symbol,
                    Trade.order_type.in_(['CLOSE_LONG', 'CLOSE_SHORT']),
                    Trade.timestamp > trade.timestamp
                ).first()

                # If no close trade, position is still open - rebuild it
                if not close_trade:
                    side = PositionSide.LONG if trade.order_type == 'OPEN_LONG' else PositionSide.SHORT
                    margin = self.get_position_size(trade.price, trade.amount)

                    # BUG FIX: Handle position stacking during restore
                    # If position already exists for this symbol, we need to STACK it
                    # (same as what open_long/open_short do), not skip it
                    if symbol in self.positions:
                        existing = self.positions[symbol]

                        # Calculate new average entry price
                        total_value_old = existing.entry_price * existing.amount
                        total_value_new = trade.price * trade.amount
                        new_amount = existing.amount + trade.amount
                        new_entry_price = (total_value_old + total_value_new) / new_amount

                        # Update position
                        existing.amount = new_amount
                        existing.entry_price = new_entry_price
                        existing.margin += margin
                        existing.liquidation_price = existing._calculate_liquidation_price()

                        total_restored_margin += margin

                        logger.info(
                            f"✓ STACKED {side.value} position: {symbol} @ {format_currency(trade.price)} "
                            f"(New avg entry: {format_currency(new_entry_price)}, Total margin: {format_currency(existing.margin)})"
                        )
                    else:
                        # Create new position
                        position = Position(
                            symbol=symbol,
                            side=side,
                            amount=trade.amount,
                            entry_price=trade.price,
                            margin=margin,
                            leverage=self.leverage,
                            open_time=trade.timestamp,
                            commission_rate=self.commission_rate
                        )
                        self.positions[symbol] = position

                        # BUG FIX: Do NOT deduct capital here!
                        # Capital was already restored from database in _restore_capital_from_database()
                        # The database capital value already has margins deducted, so deducting again
                        # would incorrectly double-deduct and show wrong available capital.

                        total_restored_margin += margin
                        restored_positions_count += 1

                        logger.info(
                            f"✓ Restored {side.value} position: {symbol} @ {format_currency(trade.price)} "
                            f"(Margin: {format_currency(margin)}, Liquidation: {format_currency(position.liquidation_price)})"
                        )

            session.close()

            if restored_positions_count > 0:
                logger.info(
                    f"✓ Restored {restored_positions_count} open position(s) from database. "
                    f"Total margin locked: {format_currency(total_restored_margin)}"
                )

                # BUG FIX: Validate consistency - total equity should equal capital + margin
                # This helps catch data corruption issues
                expected_total_margin = total_restored_margin
                actual_total_margin = sum(pos.margin for pos in self.positions.values())

                if abs(expected_total_margin - actual_total_margin) > 0.01:
                    logger.warning(
                        f"⚠️  Margin inconsistency detected! "
                        f"Expected: {format_currency(expected_total_margin)}, "
                        f"Actual: {format_currency(actual_total_margin)}"
                    )

                # Verify available capital is reasonable
                if self.capital < 0:
                    logger.error(
                        f"⚠️  CRITICAL: Available capital is negative ({format_currency(self.capital)})! "
                        f"This indicates data corruption. Total margin locked: {format_currency(actual_total_margin)}"
                    )
                elif self.capital < actual_total_margin * 0.1:
                    logger.warning(
                        f"⚠️  Low available capital! Capital: {format_currency(self.capital)}, "
                        f"Locked margin: {format_currency(actual_total_margin)}. "
                        f"May not be able to open new positions."
                    )

        except Exception as e:
            logger.error(f"Failed to restore positions: {e}")

    def get_position_size(self, price: float, amount: float) -> float:
        """
        Calculate margin required for a position

        Args:
            price: Entry price
            amount: Position size

        Returns:
            Margin required
        """
        position_value = price * amount
        margin_required = position_value / self.leverage
        return margin_required

    def calculate_fee(self, price: float, amount: float) -> float:
        """Calculate trading fee"""
        return price * amount * self.commission_rate

    def can_open_position(self, symbol: str, price: float, amount: float, side: Optional[PositionSide] = None) -> Tuple[bool, str]:
        """
        Check if a new position can be opened or added to

        Args:
            symbol: Trading pair
            price: Entry price
            amount: Position size
            side: Position side (LONG/SHORT) - if provided, allows stacking same direction

        Returns:
            (can_open, reason)
        """
        # If side is provided, check if we can stack (same direction) or need to close (opposite)
        if symbol in self.positions and side is not None:
            existing_position = self.positions[symbol]
            if existing_position.side != side:
                return False, f"Cannot open {side.value} - opposite {existing_position.side.value} position exists. Close it first."
            # Same direction - allow stacking (will be handled in open_long/open_short)

        # Check max positions limit (only for new symbols)
        if symbol not in self.positions and len(self.positions) >= self.max_positions:
            return False, f"Maximum positions ({self.max_positions}) reached"

        # Check capital availability
        margin = self.get_position_size(price, amount)
        fee = self.calculate_fee(price, amount)
        total_required = margin + fee

        if total_required > self.capital:
            return False, f"Insufficient capital. Required: {format_currency(total_required)}, Available: {format_currency(self.capital)}"

        return True, "OK"

    def open_long(self, symbol: str, amount: float, price: float, reason: str = "") -> bool:
        """
        Open a long position or add to existing LONG position

        Args:
            symbol: Trading pair
            amount: Position size
            price: Entry price
            reason: Reason for opening (e.g., AI decision)

        Returns:
            Success status
        """
        # BUG FIX: Comprehensive input validation
        if not self._validate_trade_inputs(symbol, amount, price):
            return False

        can_open, message = self.can_open_position(symbol, price, amount, PositionSide.LONG)
        if not can_open:
            log_error(f"Cannot open LONG {symbol}: {message}")
            return False

        margin = self.get_position_size(price, amount)
        fee = self.calculate_fee(price, amount)

        # Check if already have LONG position - if so, add to it (stack)
        if symbol in self.positions:
            existing = self.positions[symbol]

            # Calculate new average entry price
            total_value_old = existing.entry_price * existing.amount
            total_value_new = price * amount
            new_amount = existing.amount + amount
            new_entry_price = (total_value_old + total_value_new) / new_amount

            # Update position
            existing.amount = new_amount
            existing.entry_price = new_entry_price
            existing.margin += margin
            existing.liquidation_price = existing._calculate_liquidation_price()

            # Update capital
            self.capital -= (margin + fee)
            self.total_fees += fee

            # Record order
            self.orders.append(Order(
                timestamp=datetime.now(),
                order_type=OrderType.OPEN_LONG,
                symbol=symbol,
                amount=amount,
                price=price,
                fee=fee,
                reason=f"STACK: {reason}"
            ))

            log_trade(f"STACKED LONG {symbol} | Added: {amount} | Price: {format_currency(price)} | New Avg: {format_currency(new_entry_price)}")
            logger.info(f"Total Amount: {new_amount} | Total Margin: {format_currency(existing.margin)}")
            logger.info(f"New Liquidation Price: {format_currency(existing.liquidation_price)}")

        else:
            # Create new position
            # BUG FIX: Pass commission_rate for accurate liquidation price calculation
            position = Position(
                symbol=symbol,
                side=PositionSide.LONG,
                amount=amount,
                entry_price=price,
                leverage=self.leverage,
                margin=margin,
                open_time=datetime.now(),
                commission_rate=self.commission_rate
            )

            # Update capital
            self.capital -= (margin + fee)
            self.total_fees += fee

            # Record
            self.positions[symbol] = position
            self.orders.append(Order(
                timestamp=datetime.now(),
                order_type=OrderType.OPEN_LONG,
                symbol=symbol,
                amount=amount,
                price=price,
                fee=fee,
                reason=reason
            ))

            log_trade(f"LONG {symbol} | Amount: {amount} | Price: {format_currency(price)}")
            logger.info(f"Margin: {format_currency(margin)} | Fee: {format_currency(fee)} | Available: {format_currency(self.capital)}")
            logger.info(f"Liquidation Price: {format_currency(position.liquidation_price)}")

        return True

    def open_short(self, symbol: str, amount: float, price: float, reason: str = "") -> bool:
        """
        Open a short position or add to existing SHORT position

        Args:
            symbol: Trading pair
            amount: Position size
            price: Entry price
            reason: Reason for opening

        Returns:
            Success status
        """
        # BUG FIX: Comprehensive input validation
        if not self._validate_trade_inputs(symbol, amount, price):
            return False

        can_open, message = self.can_open_position(symbol, price, amount, PositionSide.SHORT)
        if not can_open:
            log_error(f"Cannot open SHORT {symbol}: {message}")
            return False

        margin = self.get_position_size(price, amount)
        fee = self.calculate_fee(price, amount)

        # Check if already have SHORT position - if so, add to it (stack)
        if symbol in self.positions:
            existing = self.positions[symbol]

            # Calculate new average entry price
            total_value_old = existing.entry_price * existing.amount
            total_value_new = price * amount
            new_amount = existing.amount + amount
            new_entry_price = (total_value_old + total_value_new) / new_amount

            # Update position
            existing.amount = new_amount
            existing.entry_price = new_entry_price
            existing.margin += margin
            existing.liquidation_price = existing._calculate_liquidation_price()

            # Update capital
            self.capital -= (margin + fee)
            self.total_fees += fee

            # Record order
            self.orders.append(Order(
                timestamp=datetime.now(),
                order_type=OrderType.OPEN_SHORT,
                symbol=symbol,
                amount=amount,
                price=price,
                fee=fee,
                reason=f"STACK: {reason}"
            ))

            log_trade(f"STACKED SHORT {symbol} | Added: {amount} | Price: {format_currency(price)} | New Avg: {format_currency(new_entry_price)}")
            logger.info(f"Total Amount: {new_amount} | Total Margin: {format_currency(existing.margin)}")
            logger.info(f"New Liquidation Price: {format_currency(existing.liquidation_price)}")

        else:
            # Create new position
            # BUG FIX: Pass commission_rate for accurate liquidation price calculation
            position = Position(
                symbol=symbol,
                side=PositionSide.SHORT,
                amount=amount,
                entry_price=price,
                leverage=self.leverage,
                margin=margin,
                open_time=datetime.now(),
                commission_rate=self.commission_rate
            )

            # Update capital
            self.capital -= (margin + fee)
            self.total_fees += fee

            # Record
            self.positions[symbol] = position
            self.orders.append(Order(
                timestamp=datetime.now(),
                order_type=OrderType.OPEN_SHORT,
                symbol=symbol,
                amount=amount,
                price=price,
                fee=fee,
                reason=reason
            ))

            log_trade(f"SHORT {symbol} | Amount: {amount} | Price: {format_currency(price)}")
            logger.info(f"Margin: {format_currency(margin)} | Fee: {format_currency(fee)} | Available: {format_currency(self.capital)}")
            logger.info(f"Liquidation Price: {format_currency(position.liquidation_price)}")

        return True

    def close_position(self, symbol: str, price: float, reason: str = "") -> Tuple[bool, Optional[float]]:
        """
        Close a position

        Improved logic:
        - Prevents negative capital by capping losses at available margin
        - Better logging for extreme loss scenarios
        - Tracks if position was force-liquidated vs normal close

        Args:
            symbol: Trading pair
            price: Exit price
            reason: Reason for closing

        Returns:
            Tuple of (success status, pnl) - PnL is None if failed
        """
        # BUG FIX: Validate inputs
        if not symbol or not isinstance(symbol, str):
            log_error(f"Invalid symbol: {symbol}")
            return False, None

        if not isinstance(price, (int, float)) or price <= 0:
            log_error(f"Invalid price: {price}")
            return False, None

        if symbol not in self.positions:
            log_error(f"No open position for {symbol}")
            return False, None

        position = self.positions[symbol]
        fee = self.calculate_fee(price, position.amount)

        # Calculate PnL
        pnl = position.update_unrealized_pnl(price)

        # BUG FIX: Prevent negative capital
        # In paper trading, we should cap losses to prevent going below zero
        # This simulates the reality that in real trading, you'd be liquidated before losing more than your margin

        # Calculate what capital would be after closing
        capital_after_close = self.capital + position.margin + pnl - fee

        # Check if this would result in negative capital
        if capital_after_close < 0:
            # This is an extreme loss scenario (should have been liquidated earlier)
            actual_loss = position.margin + fee  # Maximum possible loss
            actual_pnl = -position.margin  # Cap PnL at -100% of margin

            logger.error(
                f"EXTREME LOSS DETECTED for {symbol}! "
                f"Calculated PnL ({format_currency(pnl)}) would cause negative capital. "
                f"Capping loss to margin amount ({format_currency(actual_pnl)})."
            )
            logger.error(
                f"This indicates liquidation should have triggered earlier at {format_currency(position.liquidation_price)}. "
                f"Current price: {format_currency(price)}"
            )

            # Cap the loss and set capital to minimum safe value
            pnl = actual_pnl
            self.capital = max(0.0, self.capital + position.margin + pnl - fee)

            # Mark this as emergency liquidation
            reason = f"Emergency liquidation (exceeded margin): {reason}" if reason else "Emergency liquidation (exceeded margin)"
        else:
            # Normal close - update capital
            self.capital = capital_after_close

        self.total_fees += fee

        # Update stats
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        elif pnl < 0:
            self.losing_trades += 1

        # Record order
        order_type = OrderType.CLOSE_LONG if position.side == PositionSide.LONG else OrderType.CLOSE_SHORT
        self.orders.append(Order(
            timestamp=datetime.now(),
            order_type=order_type,
            symbol=symbol,
            amount=position.amount,
            price=price,
            fee=fee,
            pnl=pnl,
            reason=reason
        ))

        # Log
        pnl_percent = (pnl / position.margin) * 100 if position.margin > 0 else 0
        log_trade(f"CLOSE {position.side.value} {symbol} | Entry: {format_currency(position.entry_price)} | Exit: {format_currency(price)}")
        logger.info(f"PnL: {format_currency(pnl)} ({format_percentage(pnl_percent)}) | Fee: {format_currency(fee)}")
        logger.info(f"Capital: {format_currency(self.capital)}")

        # Warning if capital is getting low
        if self.capital < self.initial_capital * 0.2:
            logger.warning(
                f"⚠️  Capital is below 20% of initial amount! "
                f"Current: {format_currency(self.capital)} / Initial: {format_currency(self.initial_capital)}"
            )

        # Remove position
        del self.positions[symbol]

        # BUG FIX: Return both success status and PnL value so caller can save it to database
        return True, pnl

    def check_liquidations(self, current_prices: Dict[str, float]) -> List[str]:
        """
        Check and execute liquidations

        Args:
            current_prices: Dict of symbol -> current price

        Returns:
            List of liquidated symbols
        """
        liquidated = []

        for symbol, position in list(self.positions.items()):
            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]

            if position.is_liquidated(current_price):
                log_error(f"LIQUIDATION {position.side.value} {symbol} at {format_currency(current_price)}")
                # BUG FIX: close_position now returns (success, pnl) tuple
                success, pnl = self.close_position(symbol, current_price, reason="Liquidation")
                if success:
                    liquidated.append(symbol)

        return liquidated

    def get_total_equity(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total account equity including unrealized PnL

        Args:
            current_prices: Dict of symbol -> current price

        Returns:
            Total equity
        """
        total_margin = sum(pos.margin for pos in self.positions.values())
        total_unrealized_pnl = sum(
            pos.update_unrealized_pnl(current_prices.get(symbol, pos.entry_price))
            for symbol, pos in self.positions.items()
        )

        return self.capital + total_margin + total_unrealized_pnl

    def get_actual_total_fees_from_db(self) -> float:
        """
        Calculate actual total fees from database instead of in-memory counter.

        This fixes the fee tracking bug where total_fees resets on restart.
        The database is the source of truth for all fees paid.

        Returns:
            Total fees from all trades in database
        """
        try:
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            total_fees = db.get_total_fees()
            return total_fees if total_fees is not None else 0.0
        except Exception as e:
            logger.error(f"Failed to get total fees from database: {e}")
            # Fallback to in-memory counter if database query fails
            return self.total_fees

    def get_account_summary(self, current_prices: Dict[str, float]) -> Dict:
        """
        Get comprehensive account summary

        Args:
            current_prices: Dict of symbol -> current price

        Returns:
            Account summary dict
        """
        total_equity = self.get_total_equity(current_prices)
        total_pnl = total_equity - self.initial_capital
        total_pnl_percent = (total_pnl / self.initial_capital) * 100

        total_margin = sum(pos.margin for pos in self.positions.values())
        total_unrealized_pnl = sum(
            pos.update_unrealized_pnl(current_prices.get(symbol, pos.entry_price))
            for symbol, pos in self.positions.items()
        )

        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        # BUG FIX: Get actual total fees from database instead of unreliable in-memory counter
        actual_total_fees = self.get_actual_total_fees_from_db()

        return {
            "capital": self.capital,
            "total_equity": total_equity,
            "total_pnl": total_pnl,
            "total_pnl_percent": total_pnl_percent,
            "total_margin": total_margin,
            "total_unrealized_pnl": total_unrealized_pnl,
            "open_positions": len(self.positions),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": win_rate,
            "total_fees": actual_total_fees,
        }

    def print_account_summary(self, current_prices: Dict[str, float]):
        """Print formatted account summary"""
        summary = self.get_account_summary(current_prices)

        logger.separator()
        logger.info("ACCOUNT SUMMARY")
        logger.separator()
        logger.info(f"Available Capital: {format_currency(summary['capital'])}")
        logger.info(f"Locked Margin: {format_currency(summary['total_margin'])}")
        logger.info(f"Unrealized PnL: {format_currency(summary['total_unrealized_pnl'])}")
        logger.info(f"Total Equity: {format_currency(summary['total_equity'])}")
        logger.info(f"Total PnL: {format_currency(summary['total_pnl'])} ({format_percentage(summary['total_pnl_percent'])})")
        logger.separator()
        logger.info(f"Open Positions: {summary['open_positions']}/{self.max_positions}")
        logger.info(f"Total Trades: {summary['total_trades']}")
        logger.info(f"Win Rate: {format_percentage(summary['win_rate'])}")
        logger.info(f"Total Fees: {format_currency(summary['total_fees'])}")
        logger.separator()

        # Print individual positions
        if self.positions:
            logger.info("OPEN POSITIONS:")
            for symbol, pos in self.positions.items():
                current_price = current_prices.get(symbol, pos.entry_price)
                pnl = pos.update_unrealized_pnl(current_price)
                pnl_percent = (pnl / pos.margin) * 100

                logger.info(f"  {symbol} {pos.side.value}")
                logger.info(f"    Amount: {pos.amount} | Entry: {format_currency(pos.entry_price)} | Current: {format_currency(current_price)}")
                logger.info(f"    PnL: {format_currency(pnl)} ({format_percentage(pnl_percent)})")
            logger.separator()


__all__ = ["TradingEngine", "Position", "Order", "PositionSide", "OrderType"]
