from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Global references - will be set from main.py
portfolio = None
multi_portfolio = None
performance_tracker = None

def init_portfolio(portfolio_instance):
    """Initialize the portfolio reference"""
    global portfolio
    portfolio = portfolio_instance

def init_multi_portfolio(multi_portfolio_instance):
    """Initialize the multi-portfolio reference"""
    global multi_portfolio, portfolio
    multi_portfolio = multi_portfolio_instance
    # Set portfolio to first agent for backward compatibility
    if multi_portfolio and multi_portfolio.agents:
        portfolio = multi_portfolio.get_portfolio(multi_portfolio.agents[0])

def init_performance_tracker(tracker_instance):
    """Initialize the performance tracker reference"""
    global performance_tracker
    performance_tracker = tracker_instance


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "trading", "timestamp": datetime.utcnow().isoformat()}


@router.get("/api/portfolio")
async def get_portfolio():
    """
    Get current portfolio information - REAL DATA from portfolio manager
    """
    try:
        if not portfolio:
            raise HTTPException(status_code=503, detail="Portfolio manager not initialized")

        # Get real portfolio summary
        summary = portfolio.get_summary()

        # Get positions list
        positions_list = []
        for symbol, pos in portfolio.positions.items():
            quantity = pos['quantity']
            entry_price = pos['entry_price']
            current_price = pos['current_price']
            side = pos.get('side', 'long')
            leverage = pos.get('leverage', 1.0)

            # 计算盈亏（多倍ETF机制）
            if side == 'long':
                unrealized_pnl = (current_price - entry_price) * quantity * leverage
            else:  # short
                unrealized_pnl = (entry_price - current_price) * quantity * leverage

            # 盈亏百分比基于保证金（初始投入）
            initial_cost = entry_price * quantity
            unrealized_pnl_percent = (unrealized_pnl / initial_cost * 100) if initial_cost > 0 else 0

            positions_list.append({
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "entry_price": entry_price,
                "current_price": current_price,
                "leverage": leverage,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_percent": unrealized_pnl_percent,
                "stop_loss": pos.get('stop_loss'),
                "take_profit": pos.get('take_profit'),
                "reasoning": pos.get('reasoning')
            })

        return {
            "total_value": summary['total_value'],
            "cash_balance": summary['cash'],
            "positions_value": summary['positions_value'],
            "total_pnl": summary['total_pnl'],
            "total_pnl_percent": summary['total_pnl_percent'],
            "positions": positions_list,
            "updated_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/positions")
async def get_positions():
    """
    Get all open positions - REAL DATA
    """
    try:
        if not portfolio:
            raise HTTPException(status_code=503, detail="Portfolio manager not initialized")

        positions_list = []
        for symbol, pos in portfolio.positions.items():
            quantity = pos['quantity']
            entry_price = pos['entry_price']
            current_price = pos['current_price']
            side = pos.get('side', 'long')
            leverage = pos.get('leverage', 1.0)

            # 计算盈亏（多倍ETF机制）
            if side == 'long':
                unrealized_pnl = (current_price - entry_price) * quantity * leverage
            else:  # short
                unrealized_pnl = (entry_price - current_price) * quantity * leverage

            # 盈亏百分比基于初始投入
            initial_cost = entry_price * quantity
            unrealized_pnl_percent = (unrealized_pnl / initial_cost * 100) if initial_cost > 0 else 0

            positions_list.append({
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "entry_price": entry_price,
                "current_price": current_price,
                "leverage": leverage,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_percent": unrealized_pnl_percent,
                "stop_loss": pos.get('stop_loss'),
                "take_profit": pos.get('take_profit'),
                "reasoning": pos.get('reasoning')
            })

        return positions_list
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching positions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/orders")
async def place_order(order: dict):
    """
    Place and execute a new order - REAL EXECUTION
    """
    try:
        # Log the received order for debugging
        logger.info(f"Received order: {order}")

        # Validate order
        required_fields = ["symbol", "side", "quantity", "order_type"]
        for field in required_fields:
            if field not in order:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Get agent_id from order (default to 'gpt5' for backward compatibility)
        agent_id = order.get("agent_id", "gpt5")

        # Get agent's portfolio
        if multi_portfolio is None:
            raise HTTPException(status_code=500, detail="Trading system not initialized")

        portfolio = multi_portfolio.get_portfolio(agent_id)
        if portfolio is None:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        symbol = order["symbol"]
        side = order["side"].lower()
        quantity = float(order["quantity"])
        leverage = float(order.get("leverage", 1.0))  # 多倍ETF倍数，默认1倍

        # Get current market price from order or use default
        current_price = float(order.get("price", 50000.0))

        # Execute the order
        from . import main
        executor = main.executor

        if executor is None:
            raise HTTPException(status_code=500, detail="Executor not initialized")

        # Determine trade type and handle close+reverse logic
        position = portfolio.get_position(symbol)
        position_qty = position['quantity'] if position else 0
        position_side = position.get('side') if position else None

        # 用于存储可能的第二次交易（反向开仓）
        reverse_trade = None

        if side == "buy":
            # BUY操作：检查是否有空头仓位需要平仓
            if position and position_side == 'short':
                if quantity > position_qty:
                    # 数量超过现有空头仓位，需要"平空+开多"
                    trade_type = "close_short"
                    reverse_trade = {
                        'type': 'open_long',
                        'quantity': quantity - position_qty,
                        'side': 'long'
                    }
                    logger.info(f"Close+Reverse detected: Close {position_qty} SHORT, then Open {reverse_trade['quantity']} LONG")
                else:
                    # 数量不超过现有空头，只平仓
                    trade_type = "close_short"
            else:
                # 没有空头仓位，或者有多头仓位，做多开仓或加仓
                trade_type = "open_long"
                position_side = "long"

        elif side == "sell":
            # SELL操作：检查是否有多头仓位需要平仓
            if position and position_side == 'long':
                if quantity > position_qty:
                    # 数量超过现有多头仓位，需要"平多+开空"
                    trade_type = "close_long"
                    reverse_trade = {
                        'type': 'open_short',
                        'quantity': quantity - position_qty,
                        'side': 'short'
                    }
                    logger.info(f"Close+Reverse detected: Close {position_qty} LONG, then Open {reverse_trade['quantity']} SHORT")
                else:
                    # 数量不超过现有多头，只平仓
                    trade_type = "close_long"
            else:
                # 没有多头仓位，或者有空头仓位，做空开仓或加仓
                trade_type = "open_short"
                position_side = "short"

        elif side == "close":
            # 明确平仓指令
            if not position or position_qty == 0:
                raise HTTPException(status_code=400, detail=f"No position to close for {symbol}")
            trade_type = "close"
        else:
            raise HTTPException(status_code=400, detail=f"Invalid side: {side}")

        # 如果不是平仓操作，记录position_side
        if trade_type in ["open_long", "open_short"]:
            position_side = "long" if trade_type == "open_long" else "short"
        elif not position_side and position:
            position_side = position.get('side', 'long')

        # Execute trade
        if trade_type in ["open_long", "open_short"]:
            # 开仓（做多或做空）
            result = executor.execute_buy(
                symbol=symbol,
                quantity=quantity,
                current_price=current_price,
                available_balance=portfolio.cash
            )
        elif trade_type in ["close_long", "close_short", "close"]:
            # 平仓
            available_qty = position['quantity'] if position else 0
            result = executor.execute_sell(
                symbol=symbol,
                quantity=min(quantity, available_qty),  # 只能平现有仓位
                current_price=current_price,
                available_quantity=available_qty
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown trade type: {trade_type}")

        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        # Update portfolio based on trade
        if trade_type in ["open_long", "open_short"]:
            # Deduct cost from cash
            notional_cost = result.executed_quantity * result.executed_price
            portfolio.cash -= (notional_cost + result.commission)

            # Add to position
            portfolio.add_position(
                symbol=symbol,
                quantity=result.executed_quantity,
                entry_price=result.executed_price,
                side=position_side,  # 'long' or 'short'
                leverage=leverage,  # 多倍ETF倍数
                stop_loss=order.get('stop_loss'),
                take_profit=order.get('take_profit'),
                reasoning=order.get('reasoning')
            )

            # Save position to database
            try:
                import psycopg2
                from . import main

                logger.info(f"Saving position to database for {agent_id}: {symbol}")

                conn = psycopg2.connect(
                    host=main.settings.TIMESCALE_HOST,
                    port=main.settings.TIMESCALE_PORT,
                    database=main.settings.TIMESCALE_DB,
                    user=main.settings.TIMESCALE_USER,
                    password=main.settings.TIMESCALE_PASSWORD
                )

                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO positions (agent_id, symbol, quantity, entry_price, current_price,
                                             unrealized_pnl, stop_loss, take_profit,
                                             entry_time, side, leverage, is_closed)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        agent_id,
                        symbol,
                        result.executed_quantity,
                        result.executed_price,
                        result.executed_price,
                        0.0,
                        order.get('stop_loss'),
                        order.get('take_profit'),
                        datetime.utcnow(),
                        position_side,  # 'long' or 'short'
                        leverage,  # 多倍ETF倍数
                        False
                    ))
                    position_id = cursor.fetchone()[0]
                    conn.commit()

                # Update agent's current_balance in database
                    cursor.execute("""
                        UPDATE agents
                        SET current_balance = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (portfolio.cash, agent_id))
                    conn.commit()

                conn.close()
                logger.info(f"Position {position_id} saved to database with stop_loss={order.get('stop_loss')}, take_profit={order.get('take_profit')}")
                logger.info(f"Updated {agent_id} balance to ${portfolio.cash:.2f} in database")
            except Exception as e:
                logger.error(f"Failed to save position to database: {e}", exc_info=True)

        elif trade_type in ["close_long", "close_short", "close"]:
            # 平仓处理
            if not position:
                raise HTTPException(status_code=400, detail="No position to close")

            # 计算盈亏（考虑leverage）
            entry_price = position['entry_price']
            exit_price = result.executed_price
            quantity_closed = result.executed_quantity
            position_leverage = position.get('leverage', 1.0)

            # Get entry time from position
            entry_time = position.get('entry_time')
            exit_time = datetime.utcnow()

            # Calculate holding time
            holding_time = None
            if entry_time:
                if isinstance(entry_time, str):
                    from dateutil import parser
                    entry_time = parser.parse(entry_time)
                delta = exit_time - entry_time
                hours = delta.total_seconds() / 3600
                if hours < 1:
                    minutes = delta.total_seconds() / 60
                    holding_time = f"{int(minutes)}m"
                elif hours < 24:
                    holding_time = f"{int(hours)}h"
                else:
                    days = delta.days
                    holding_time = f"{days}d"

            # 根据仓位方向计算盈亏（多倍ETF机制）
            if position_side == 'long':
                pnl = (exit_price - entry_price) * quantity_closed * position_leverage
            else:  # short
                pnl = (entry_price - exit_price) * quantity_closed * position_leverage

            # 计算卖出收入
            sale_revenue = exit_price * quantity_closed

            # 更新现金：卖出收入 - 手续费
            portfolio.cash += sale_revenue - result.commission

            # 从内存中减少仓位（如果数量等于持仓数量，reduce_position会自动删除）
            portfolio.reduce_position(symbol, quantity_closed)

            # Update database: 关闭position并更新balance
            try:
                import psycopg2
                from . import main

                conn = psycopg2.connect(
                    host=main.settings.TIMESCALE_HOST,
                    port=main.settings.TIMESCALE_PORT,
                    database=main.settings.TIMESCALE_DB,
                    user=main.settings.TIMESCALE_USER,
                    password=main.settings.TIMESCALE_PASSWORD
                )

                with conn.cursor() as cursor:
                    # 关闭position
                    cursor.execute("""
                        UPDATE positions
                        SET is_closed = true,
                            closed_at = CURRENT_TIMESTAMP
                        WHERE agent_id = %s AND symbol = %s AND is_closed = false
                    """, (agent_id, symbol))

                    # 更新agent余额
                    cursor.execute("""
                        UPDATE agents
                        SET current_balance = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (portfolio.cash, agent_id))

                    conn.commit()

                conn.close()
                logger.info(f"Closed position {symbol} for {agent_id}, PnL: ${pnl:.2f}, new balance: ${portfolio.cash:.2f}")
            except Exception as e:
                logger.error(f"Failed to update database after closing position: {e}", exc_info=True)

        # Record the trade in history and database
        trade_record = {
            "symbol": symbol,
            "side": side,
            "quantity": result.executed_quantity,
            "price": result.executed_price,
            "commission": result.commission,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id
        }

        # 如果是平仓，添加pnl信息
        if trade_type in ["close_long", "close_short", "close"]:
            trade_record["pnl"] = pnl
            trade_record["exit_price"] = exit_price
            trade_record["entry_price"] = entry_price
            trade_record["holding_time"] = holding_time
            trade_record["entry_time"] = entry_time
            trade_record["exit_time"] = exit_time

        portfolio.record_trade(trade_record)

        # Save trade to database
        try:
            import psycopg2
            from . import main

            conn = psycopg2.connect(
                host=main.settings.TIMESCALE_HOST,
                port=main.settings.TIMESCALE_PORT,
                database=main.settings.TIMESCALE_DB,
                user=main.settings.TIMESCALE_USER,
                password=main.settings.TIMESCALE_PASSWORD
            )

            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO trades (agent_id, symbol, side, quantity, price, commission, pnl, leverage, executed_at,
                                        exit_price, holding_time, entry_time, exit_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    agent_id,
                    symbol,
                    side,
                    result.executed_quantity,
                    result.executed_price,
                    result.commission,
                    trade_record.get("pnl"),
                    leverage,  # 保存杠杆信息
                    datetime.utcnow(),
                    trade_record.get("exit_price"),
                    trade_record.get("holding_time"),
                    trade_record.get("entry_time"),
                    trade_record.get("exit_time")
                ))
                conn.commit()

            conn.close()
            logger.info(f"Trade recorded to database for {agent_id}")
        except Exception as e:
            logger.error(f"Failed to save trade to database: {e}", exc_info=True)

        logger.info(f"Order executed for {agent_id}: {side} {quantity} {symbol} @ ${result.executed_price:.2f}")

        # Execute reverse trade if needed (close+reverse scenario)
        reverse_result = None
        if reverse_trade:
            logger.info(f"Executing reverse trade: {reverse_trade['type']} {reverse_trade['quantity']} {symbol}")

            # Execute the reverse trade
            reverse_qty = reverse_trade['quantity']
            reverse_type = reverse_trade['type']
            reverse_side = reverse_trade['side']

            reverse_exec_result = executor.execute_buy(
                symbol=symbol,
                quantity=reverse_qty,
                current_price=current_price,
                available_balance=portfolio.cash
            )

            if reverse_exec_result.success:
                # Deduct cost from cash for reverse trade
                notional_cost = reverse_exec_result.executed_quantity * reverse_exec_result.executed_price
                portfolio.cash -= (notional_cost + reverse_exec_result.commission)

                # Add reverse position
                portfolio.add_position(
                    symbol=symbol,
                    quantity=reverse_exec_result.executed_quantity,
                    entry_price=reverse_exec_result.executed_price,
                    side=reverse_side,
                    leverage=leverage,  # 使用相同的leverage
                    stop_loss=order.get('stop_loss'),
                    take_profit=order.get('take_profit'),
                    reasoning=f"Reverse trade after closing {position_side} position"
                )

                # Save reverse position to database
                try:
                    import psycopg2
                    from . import main

                    conn = psycopg2.connect(
                        host=main.settings.TIMESCALE_HOST,
                        port=main.settings.TIMESCALE_PORT,
                        database=main.settings.TIMESCALE_DB,
                        user=main.settings.TIMESCALE_USER,
                        password=main.settings.TIMESCALE_PASSWORD
                    )

                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO positions (agent_id, symbol, quantity, entry_price, current_price,
                                                 unrealized_pnl, stop_loss, take_profit,
                                                 entry_time, side, leverage, is_closed)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            agent_id,
                            symbol,
                            reverse_exec_result.executed_quantity,
                            reverse_exec_result.executed_price,
                            reverse_exec_result.executed_price,
                            0.0,
                            order.get('stop_loss'),
                            order.get('take_profit'),
                            datetime.utcnow(),
                            reverse_side,
                            leverage,  # 多倍ETF倍数
                            False
                        ))
                        reverse_position_id = cursor.fetchone()[0]

                        # Update agent balance
                        cursor.execute("""
                            UPDATE agents
                            SET current_balance = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (portfolio.cash, agent_id))

                        conn.commit()
                    conn.close()
                    logger.info(f"Reverse position {reverse_position_id} saved: {reverse_side} {reverse_exec_result.executed_quantity} @ ${reverse_exec_result.executed_price:.2f}")
                except Exception as e:
                    logger.error(f"Failed to save reverse position: {e}", exc_info=True)

                # Record reverse trade
                reverse_trade_record = {
                    "symbol": symbol,
                    "side": "buy" if reverse_side == "long" else "sell",
                    "quantity": reverse_exec_result.executed_quantity,
                    "price": reverse_exec_result.executed_price,
                    "commission": reverse_exec_result.commission,
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_id": agent_id
                }
                portfolio.record_trade(reverse_trade_record)

                # Save reverse trade to database
                try:
                    conn = psycopg2.connect(
                        host=main.settings.TIMESCALE_HOST,
                        port=main.settings.TIMESCALE_PORT,
                        database=main.settings.TIMESCALE_DB,
                        user=main.settings.TIMESCALE_USER,
                        password=main.settings.TIMESCALE_PASSWORD
                    )

                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO trades (agent_id, symbol, side, quantity, price, commission, pnl, leverage, executed_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            agent_id,
                            symbol,
                            reverse_trade_record["side"],
                            reverse_exec_result.executed_quantity,
                            reverse_exec_result.executed_price,
                            reverse_exec_result.commission,
                            None,
                            leverage,  # 保存杠杆信息
                            datetime.utcnow()
                        ))
                        conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"Failed to save reverse trade: {e}", exc_info=True)

                reverse_result = reverse_exec_result
                logger.info(f"Reverse trade executed successfully: {reverse_side} {reverse_exec_result.executed_quantity} @ ${reverse_exec_result.executed_price:.2f}")
            else:
                logger.error(f"Reverse trade failed: {reverse_exec_result.message}")

        # Return order response
        order_id = f"ord_{datetime.utcnow().timestamp()}"
        response = {
            "id": order_id,
            "agent_id": agent_id,
            "symbol": symbol,
            "side": side,
            "order_type": order["order_type"],
            "quantity": quantity,
            "price": current_price,
            "status": "filled",
            "filled_quantity": result.executed_quantity,
            "average_price": result.executed_price,
            "commission": result.commission,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Add reverse trade info if applicable
        if reverse_result:
            response["reverse_trade"] = {
                "side": reverse_trade['side'],
                "quantity": reverse_result.executed_quantity,
                "price": reverse_result.executed_price,
                "commission": reverse_result.commission
            }

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/orders")
async def get_orders(status: Optional[str] = None):
    """
    Get all orders, optionally filtered by status - REAL DATA
    """
    try:
        # TODO: Implement real order tracking in portfolio manager
        # For now, return empty list as we don't have orders yet
        return []
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    """
    Get a specific order by ID
    """
    try:
        # Return demo order
        return {
            "id": order_id,
            "symbol": "BTC",
            "side": "buy",
            "order_type": "market",
            "quantity": 0.1,
            "status": "filled",
            "filled_quantity": 0.1,
            "average_price": 50000.00,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/orders/{order_id}/cancel")
async def cancel_order(order_id: str):
    """
    Cancel an order
    """
    try:
        return {
            "id": order_id,
            "symbol": "BTC",
            "side": "buy",
            "order_type": "limit",
            "quantity": 0.1,
            "status": "cancelled",
            "filled_quantity": 0.0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/performance")
async def get_performance_metrics():
    """
    Get performance metrics - REAL DATA from portfolio
    """
    try:
        if not portfolio:
            raise HTTPException(status_code=503, detail="Portfolio manager not initialized")

        # Get real metrics from portfolio
        total_trades = len(portfolio.trade_history)
        winning_trades = sum(1 for trade in portfolio.trade_history if trade.get('pnl', 0) > 0)
        losing_trades = sum(1 for trade in portfolio.trade_history if trade.get('pnl', 0) < 0)

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

        # Calculate average profit/loss
        winning_pnls = [trade.get('pnl', 0) for trade in portfolio.trade_history if trade.get('pnl', 0) > 0]
        losing_pnls = [abs(trade.get('pnl', 0)) for trade in portfolio.trade_history if trade.get('pnl', 0) < 0]

        average_profit = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0.0
        average_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0.0

        profit_factor = (sum(winning_pnls) / sum(losing_pnls)) if losing_pnls and sum(losing_pnls) > 0 else 0.0

        # Get total return from portfolio
        total_pnl, total_pnl_percent = portfolio.get_pnl()

        # TODO: Calculate Sharpe ratio and max drawdown from trade history
        sharpe_ratio = 0.0
        max_drawdown = 0.0

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 2),
            "average_profit": round(average_profit, 2),
            "average_loss": round(average_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 2),
            "total_return": round(total_pnl, 2),
            "total_return_percent": round(total_pnl_percent, 2)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching performance metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/trades")
async def get_trade_history(limit: int = 50):
    """
    Get trade history - REAL DATA from portfolio
    """
    try:
        if not portfolio:
            raise HTTPException(status_code=503, detail="Portfolio manager not initialized")

        # Get real trade history from portfolio, most recent first
        trades = portfolio.trade_history[-limit:][::-1]  # Last N trades, reversed
        return trades
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trade history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MULTI-AGENT ENDPOINTS
# ============================================================================

@router.get("/api/agents")
async def get_all_agents():
    """Get list of all AI agents"""
    try:
        if not multi_portfolio:
            raise HTTPException(status_code=503, detail="Multi-portfolio not initialized")

        return {
            "agents": multi_portfolio.agents,
            "total": len(multi_portfolio.agents)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/agents/leaderboard")
async def get_leaderboard():
    """Get agent leaderboard sorted by total value"""
    try:
        if not multi_portfolio:
            raise HTTPException(status_code=503, detail="Multi-portfolio not initialized")

        return multi_portfolio.get_leaderboard()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/agents/aggregate")
async def get_aggregate_stats():
    """Get aggregate statistics across all agents"""
    try:
        if not multi_portfolio:
            raise HTTPException(status_code=503, detail="Multi-portfolio not initialized")

        return multi_portfolio.get_aggregate_stats()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching aggregate stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/agents/{agent_id}/portfolio")
async def get_agent_portfolio(agent_id: str):
    """Get portfolio for specific agent - reads directly from database for accuracy"""
    try:
        if not multi_portfolio:
            raise HTTPException(status_code=503, detail="Multi-portfolio not initialized")

        # Check if agent exists
        agent_portfolio = multi_portfolio.get_portfolio(agent_id)
        if not agent_portfolio:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Read data directly from database for accuracy
        from .config import get_settings
        import psycopg2
        from psycopg2.extras import RealDictCursor

        settings = get_settings()
        conn = psycopg2.connect(
            host=settings.TIMESCALE_HOST,
            port=settings.TIMESCALE_PORT,
            database=settings.TIMESCALE_DB,
            user=settings.TIMESCALE_USER,
            password=settings.TIMESCALE_PASSWORD
        )

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get agent balances
            cursor.execute("""
                SELECT initial_balance, current_balance
                FROM agents
                WHERE id = %s
            """, (agent_id,))
            agent_data = cursor.fetchone()

            if not agent_data:
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found in database")

            initial_balance = float(agent_data['initial_balance'])
            current_balance = float(agent_data['current_balance'])

            # Get positions stats
            cursor.execute("""
                SELECT
                    COALESCE(SUM(current_price * quantity), 0) as total_positions_value,
                    COUNT(*) as position_count
                FROM positions
                WHERE agent_id = %s AND is_closed = false
            """, (agent_id,))
            pos_data = cursor.fetchone()

            positions_value = float(pos_data['total_positions_value']) if pos_data else 0
            position_count = int(pos_data['position_count']) if pos_data else 0

            # Get trade count (from memory for now, could also query DB)
            trade_count = len(agent_portfolio.trade_history)

        conn.close()

        # Calculate total account value
        # Total Value = Available Cash + Positions Value
        total_value = current_balance + positions_value
        total_pnl = total_value - initial_balance
        total_pnl_percent = (total_pnl / initial_balance * 100) if initial_balance > 0 else 0

        return {
            'total_value': total_value,
            'cash': current_balance,
            'cash_balance': initial_balance,  # For UI reference
            'positions_value': positions_value,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
            'num_positions': position_count,
            'num_trades': trade_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent portfolio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/agents/{agent_id}/trades")
async def get_agent_trades(agent_id: str, limit: int = 50):
    """Get trade history for specific agent"""
    try:
        if not multi_portfolio:
            raise HTTPException(status_code=503, detail="Multi-portfolio not initialized")

        agent_portfolio = multi_portfolio.get_portfolio(agent_id)
        if not agent_portfolio:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        trades = agent_portfolio.trade_history[-limit:][::-1]
        return trades
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent trades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/agents/performance")
async def get_all_agents_performance():
    """Get performance metrics for all agents"""
    try:
        if not multi_portfolio:
            raise HTTPException(status_code=503, detail="Multi-portfolio not initialized")

        return multi_portfolio.get_performance_by_agent()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agents performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/positions/all")
async def get_all_agents_positions():
    """Get all positions across all agents"""
    try:
        if not multi_portfolio:
            raise HTTPException(status_code=503, detail="Multi-portfolio not initialized")

        return multi_portfolio.get_all_positions()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching all positions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/trades/all")
async def get_all_agents_trades(limit: int = 100):
    """Get all trades across all agents"""
    try:
        if not multi_portfolio:
            raise HTTPException(status_code=503, detail="Multi-portfolio not initialized")

        return multi_portfolio.get_all_trades(limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching all trades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/performance/chart")
async def get_performance_chart_data(limit: int = None):
    """Get performance history for charting"""
    try:
        if not performance_tracker:
            # Return initial data point if tracker not ready
            return [{
                "date": "Now",
                "gpt5": 10000,
                "claude": 10000,
                "gemini": 10000,
                "grok": 10000,
                "deepseek": 10000,
                "qwen": 10000
            }]

        chart_data = performance_tracker.get_chart_data()

        # If no data yet, return initial point
        if not chart_data:
            return [{
                "date": "Now",
                "gpt5": 10000,
                "claude": 10000,
                "gemini": 10000,
                "grok": 10000,
                "deepseek": 10000,
                "qwen": 10000
            }]

        return chart_data if not limit else chart_data[-limit:]
    except Exception as e:
        logger.error(f"Error fetching performance chart data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
