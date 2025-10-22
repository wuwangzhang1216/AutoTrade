"""
Multi-Agent Portfolio Manager - 跟踪多个AI代理的独立投资组合
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging
from .portfolio_manager import PortfolioManager

logger = logging.getLogger(__name__)


class MultiAgentPortfolio:
    """管理多个AI代理的独立投资组合"""

    def __init__(self, agents: List[str], initial_cash: float = 10000.0):
        """
        初始化多代理投资组合系统（从数据库恢复余额）

        Args:
            agents: AI代理ID列表
            initial_cash: 每个代理的初始现金（如果数据库中没有记录）
        """
        self.agents = agents
        self.portfolios: Dict[str, PortfolioManager] = {}

        # 从数据库加载agent的初始余额和当前余额
        agent_balances = self._load_agent_balances_from_db(agents, initial_cash)

        # 为每个代理创建独立的投资组合
        for agent_id in agents:
            balance_data = agent_balances.get(agent_id, {'initial': initial_cash, 'current': initial_cash})
            agent_initial = balance_data['initial']
            agent_current = balance_data['current']

            self.portfolios[agent_id] = PortfolioManager(
                initial_cash=agent_initial,  # 从数据库读取的初始值，用于计算盈亏
                current_cash=agent_current  # 从数据库读取的当前余额
            )
            logger.info(f"Created portfolio for agent: {agent_id} - initial=${agent_initial:.2f}, current=${agent_current:.2f}")

        # 从数据库恢复所有持仓到内存
        self._restore_positions_from_db()

        logger.info(f"Initialized MultiAgentPortfolio with {len(agents)} agents")

    def _load_agent_balances_from_db(self, agents: List[str], default_balance: float) -> Dict[str, Dict[str, float]]:
        """从数据库加载agent的初始余额和当前余额"""
        from .config import get_settings
        import psycopg2
        from psycopg2.extras import RealDictCursor

        settings = get_settings()
        balances = {}

        try:
            conn = psycopg2.connect(
                host=settings.TIMESCALE_HOST,
                port=settings.TIMESCALE_PORT,
                database=settings.TIMESCALE_DB,
                user=settings.TIMESCALE_USER,
                password=settings.TIMESCALE_PASSWORD
            )

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                for agent_id in agents:
                    cursor.execute("""
                        SELECT initial_balance, current_balance
                        FROM agents
                        WHERE id = %s
                    """, (agent_id,))
                    result = cursor.fetchone()
                    if result:
                        balances[agent_id] = {
                            'initial': float(result['initial_balance']),
                            'current': float(result['current_balance'])
                        }
                        logger.info(f"Loaded {agent_id} balances from DB: initial=${balances[agent_id]['initial']:.2f}, current=${balances[agent_id]['current']:.2f}")
                    else:
                        balances[agent_id] = {
                            'initial': default_balance,
                            'current': default_balance
                        }
                        logger.warning(f"No balance found for {agent_id} in DB, using default: ${default_balance:.2f}")

            conn.close()
        except Exception as e:
            logger.error(f"Error loading agent balances from database: {e}")
            # Fallback to default balance
            for agent_id in agents:
                balances[agent_id] = {
                    'initial': default_balance,
                    'current': default_balance
                }

        return balances

    def _restore_positions_from_db(self):
        """从数据库恢复所有持仓到内存中的portfolio对象"""
        from .config import get_settings
        import psycopg2
        from psycopg2.extras import RealDictCursor

        settings = get_settings()

        try:
            conn = psycopg2.connect(
                host=settings.TIMESCALE_HOST,
                port=settings.TIMESCALE_PORT,
                database=settings.TIMESCALE_DB,
                user=settings.TIMESCALE_USER,
                password=settings.TIMESCALE_PASSWORD
            )

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 获取所有未平仓的持仓
                cursor.execute("""
                    SELECT agent_id, symbol, quantity, entry_price, current_price,
                           side, stop_loss, take_profit, entry_time
                    FROM positions
                    WHERE is_closed = false
                    ORDER BY agent_id, entry_time
                """)
                positions = cursor.fetchall()

                for pos in positions:
                    agent_id = pos['agent_id']
                    portfolio = self.portfolios.get(agent_id)

                    if portfolio:
                        # 将持仓添加到内存中的portfolio对象
                        portfolio.positions[pos['symbol']] = {
                            'symbol': pos['symbol'],
                            'quantity': float(pos['quantity']),
                            'entry_price': float(pos['entry_price']),
                            'current_price': float(pos['current_price']),
                            'side': pos['side'],
                            'stop_loss': float(pos['stop_loss']) if pos['stop_loss'] else None,
                            'take_profit': float(pos['take_profit']) if pos['take_profit'] else None,
                            'created_at': pos['entry_time'],
                            'updated_at': pos['entry_time']
                        }
                        logger.info(f"Restored position for {agent_id}: {pos['symbol']} {pos['side']} {float(pos['quantity']):.4f} @ ${float(pos['entry_price']):.2f}")

            conn.close()
            logger.info(f"Restored {len(positions)} positions from database")

        except Exception as e:
            logger.error(f"Error restoring positions from database: {e}")

    def get_portfolio(self, agent_id: str) -> Optional[PortfolioManager]:
        """获取指定代理的投资组合"""
        return self.portfolios.get(agent_id)

    def get_all_portfolios(self) -> Dict[str, Dict]:
        """获取所有代理的投资组合摘要"""
        result = {}
        for agent_id, portfolio in self.portfolios.items():
            result[agent_id] = portfolio.get_summary()
        return result

    def get_leaderboard(self) -> List[Dict]:
        """
        获取代理排行榜（按总价值排序，从数据库读取真实数据）

        Returns:
            排序后的代理列表，包含排名和关键指标
        """
        from .config import get_settings
        import psycopg2
        from psycopg2.extras import RealDictCursor

        settings = get_settings()
        leaderboard = []

        try:
            conn = psycopg2.connect(
                host=settings.TIMESCALE_HOST,
                port=settings.TIMESCALE_PORT,
                database=settings.TIMESCALE_DB,
                user=settings.TIMESCALE_USER,
                password=settings.TIMESCALE_PASSWORD
            )

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                for agent_id, portfolio in self.portfolios.items():
                    # 获取agent的持仓市值
                    cursor.execute("""
                        SELECT COALESCE(SUM(current_price * quantity), 0) as total_positions_value,
                               COUNT(*) as position_count
                        FROM positions
                        WHERE agent_id = %s AND is_closed = false
                    """, (agent_id,))
                    result = cursor.fetchone()
                    positions_value = float(result['total_positions_value']) if result else 0
                    position_count = int(result['position_count']) if result else 0

                    # 计算总资产 = 现金 + 持仓市值
                    cash = portfolio.cash
                    total_value = cash + positions_value
                    total_pnl = total_value - portfolio.initial_cash
                    total_pnl_percent = (total_pnl / portfolio.initial_cash * 100) if portfolio.initial_cash > 0 else 0

                    # 获取交易统计数据
                    cursor.execute("""
                        SELECT
                            COUNT(*) as total_trades,
                            COALESCE(AVG(price * quantity), 0) as avg_trade_size,
                            COALESCE(SUM(commission), 0) as total_fees,
                            COALESCE(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END), 0) as winning_trades,
                            COALESCE(MAX(pnl), 0) as biggest_win,
                            COALESCE(MIN(pnl), 0) as biggest_loss,
                            COALESCE(AVG(pnl), 0) as avg_pnl
                        FROM trades
                        WHERE agent_id = %s AND pnl IS NOT NULL
                    """, (agent_id,))
                    trade_stats = cursor.fetchone()

                    total_trades = int(trade_stats['total_trades']) if trade_stats else 0
                    avg_trade_size = float(trade_stats['avg_trade_size']) if trade_stats else 0
                    total_fees = float(trade_stats['total_fees']) if trade_stats else 0
                    winning_trades = int(trade_stats['winning_trades']) if trade_stats else 0
                    biggest_win = float(trade_stats['biggest_win']) if trade_stats else 0
                    biggest_loss = float(trade_stats['biggest_loss']) if trade_stats else 0
                    avg_pnl = float(trade_stats['avg_pnl']) if trade_stats else 0

                    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

                    # 获取决策统计数据
                    cursor.execute("""
                        SELECT
                            COALESCE(AVG(confidence * 100), 0) as avg_confidence,
                            COALESCE(COUNT(CASE WHEN action IN ('buy', 'sell') THEN 1 END), 0) as action_count,
                            COALESCE(COUNT(CASE WHEN action = 'buy' THEN 1 END), 0) as long_count
                        FROM decisions
                        WHERE agent_id = %s AND confidence IS NOT NULL
                    """, (agent_id,))
                    decision_stats = cursor.fetchone()

                    avg_confidence = float(decision_stats['avg_confidence']) if decision_stats else 0
                    action_count = int(decision_stats['action_count']) if decision_stats else 0
                    long_count = int(decision_stats['long_count']) if decision_stats else 0
                    percent_long = (long_count / action_count * 100) if action_count > 0 else 0

                    leaderboard.append({
                        'agent_id': agent_id,
                        'total_value': total_value,
                        'total_pnl': total_pnl,
                        'total_pnl_percent': total_pnl_percent,
                        'cash_balance': cash,
                        'positions_count': position_count,
                        'trades_count': len(portfolio.trade_history),
                        # Analytics
                        'avg_trade_size': avg_trade_size,
                        'median_trade_size': avg_trade_size,  # Simplified, actual median would need more complex query
                        'avg_hold_time': 'N/A',  # TODO: Calculate from position data
                        'median_hold_time': 'N/A',  # TODO: Calculate from position data
                        'percent_long': percent_long,
                        'expectancy': avg_pnl,
                        'avg_confidence': avg_confidence,
                        'median_confidence': avg_confidence,  # Simplified
                        'win_rate': win_rate,
                        'biggest_win': biggest_win,
                        'biggest_loss': biggest_loss,
                        'total_fees': total_fees,
                        'sharpe_ratio': total_pnl_percent / 100 if total_pnl_percent != 0 else 0
                    })

            conn.close()
        except Exception as e:
            logger.error(f"Error getting leaderboard from database: {e}")
            # Fallback to memory-only calculation
            for agent_id, portfolio in self.portfolios.items():
                summary = portfolio.get_summary()
                leaderboard.append({
                    'agent_id': agent_id,
                    'total_value': summary['total_value'],
                    'total_pnl': summary['total_pnl'],
                    'total_pnl_percent': summary['total_pnl_percent'],
                    'cash_balance': summary['cash'],
                    'positions_count': summary['num_positions'],
                    'trades_count': summary['num_trades']
                })

        # 按总价值排序
        leaderboard.sort(key=lambda x: x['total_value'], reverse=True)

        # 添加排名
        for rank, entry in enumerate(leaderboard, 1):
            entry['rank'] = rank

        return leaderboard

    def get_aggregate_stats(self) -> Dict:
        """
        获取所有代理的聚合统计数据（从数据库读取真实数据）

        Returns:
            包含总体统计的字典
        """
        from .config import get_settings
        import psycopg2
        from psycopg2.extras import RealDictCursor

        settings = get_settings()

        total_value = 0
        total_initial = 0  # 将累加所有agent的实际初始余额
        total_positions = 0

        agent_stats = {}

        try:
            conn = psycopg2.connect(
                host=settings.TIMESCALE_HOST,
                port=settings.TIMESCALE_PORT,
                database=settings.TIMESCALE_DB,
                user=settings.TIMESCALE_USER,
                password=settings.TIMESCALE_PASSWORD
            )

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 获取每个agent的当前余额和持仓市值
                for agent_id in self.portfolios.keys():
                    # 获取agent的持仓市值
                    cursor.execute("""
                        SELECT COALESCE(SUM(current_price * quantity), 0) as total_positions_value,
                               COUNT(*) as count
                        FROM positions
                        WHERE agent_id = %s AND is_closed = false
                    """, (agent_id,))
                    result = cursor.fetchone()
                    positions_value = float(result['total_positions_value']) if result else 0
                    position_count = int(result['count']) if result else 0

                    # 计算agent总资产 = 现金 + 持仓市值
                    portfolio = self.portfolios[agent_id]
                    agent_initial = portfolio.initial_cash
                    agent_total = portfolio.cash + positions_value
                    agent_pnl_percent = ((agent_total - agent_initial) / agent_initial * 100) if agent_initial > 0 else 0

                    # 累加总初始余额
                    total_initial += agent_initial

                    agent_stats[agent_id] = {
                        'total_value': agent_total,
                        'pnl_percent': agent_pnl_percent
                    }

                    total_value += agent_total
                    total_positions += position_count

            conn.close()
        except Exception as e:
            logger.error(f"Error getting aggregate stats from database: {e}")
            # Fallback to memory-only calculation
            for agent_id, portfolio in self.portfolios.items():
                summary = portfolio.get_summary()
                total_value += summary['total_value']
                total_positions += summary['num_positions']
                agent_stats[agent_id] = {
                    'total_value': summary['total_value'],
                    'pnl_percent': summary['total_pnl_percent']
                }

        # Find best and worst performers
        best_performer = None
        worst_performer = None
        best_pnl = float('-inf')
        worst_pnl = float('inf')

        for agent_id, stats in agent_stats.items():
            if stats['pnl_percent'] > best_pnl:
                best_pnl = stats['pnl_percent']
                best_performer = {
                    'agent_id': agent_id,
                    'value': stats['total_value'],
                    'pnl_percent': stats['pnl_percent']
                }

            if stats['pnl_percent'] < worst_pnl:
                worst_pnl = stats['pnl_percent']
                worst_performer = {
                    'agent_id': agent_id,
                    'value': stats['total_value'],
                    'pnl_percent': stats['pnl_percent']
                }

        avg_pnl_percent = ((total_value - total_initial) / total_initial * 100) if total_initial > 0 else 0

        return {
            'total_agents': len(self.portfolios),
            'total_value': total_value,
            'total_initial': total_initial,
            'total_pnl': total_value - total_initial,
            'avg_pnl_percent': avg_pnl_percent,
            'total_trades': 0,  # TODO: get from database
            'total_positions': total_positions,
            'best_performer': best_performer,
            'worst_performer': worst_performer,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_all_positions(self) -> List[Dict]:
        """获取所有代理的所有持仓 - 从数据库读取完整数据"""
        from .config import get_settings
        import psycopg2
        from psycopg2.extras import RealDictCursor

        settings = get_settings()
        all_positions = []

        try:
            # 直接连接数据库查询
            conn = psycopg2.connect(
                host=settings.TIMESCALE_HOST,
                port=settings.TIMESCALE_PORT,
                database=settings.TIMESCALE_DB,
                user=settings.TIMESCALE_USER,
                password=settings.TIMESCALE_PASSWORD
            )

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT agent_id, symbol, quantity, entry_price, current_price,
                           side, leverage, stop_loss, take_profit, entry_time, unrealized_pnl
                    FROM positions
                    WHERE is_closed = false
                """)

                for row in cursor.fetchall():
                    quantity = float(row['quantity']) if row['quantity'] else 0
                    entry_price = float(row['entry_price']) if row['entry_price'] else 0
                    current_price = float(row['current_price']) if row['current_price'] else 0
                    side = row['side'] or 'long'
                    leverage = float(row['leverage']) if row['leverage'] else 1.0

                    # Calculate position value with leverage (multi-ETF mechanism)
                    if side == 'long':
                        pnl = (current_price - entry_price) * quantity * leverage
                    else:  # short
                        pnl = (entry_price - current_price) * quantity * leverage

                    position_value = entry_price * quantity + pnl
                    position_value = max(0, position_value)  # Can't go below 0

                    all_positions.append({
                        'agent_id': row['agent_id'],
                        'symbol': row['symbol'],
                        'quantity': quantity,
                        'entry_price': entry_price,
                        'current_price': current_price,
                        'side': side,
                        'leverage': leverage,
                        'stop_loss': float(row['stop_loss']) if row['stop_loss'] else None,
                        'take_profit': float(row['take_profit']) if row['take_profit'] else None,
                        'unrealized_pnl': pnl,
                        'position_value': position_value,
                        'created_at': row['entry_time'].isoformat() if row['entry_time'] else None,
                        'updated_at': datetime.utcnow().isoformat()
                    })

            conn.close()
        except Exception as e:
            logger.error(f"Error fetching positions from database: {e}")
            # Fallback to in-memory positions
            for agent_id, portfolio in self.portfolios.items():
                for symbol, position in portfolio.positions.items():
                    position_with_agent = {
                        'agent_id': agent_id,
                        'symbol': symbol,
                        **position
                    }
                    all_positions.append(position_with_agent)

        return all_positions

    def get_all_trades(self, limit: int = 100) -> List[Dict]:
        """
        获取所有代理的交易历史 - 从数据库读取

        Args:
            limit: 返回的最大交易数量

        Returns:
            按时间排序的交易列表
        """
        from .config import get_settings
        import psycopg2
        from psycopg2.extras import RealDictCursor

        settings = get_settings()
        all_trades = []

        try:
            # 从数据库读取trades
            conn = psycopg2.connect(
                host=settings.TIMESCALE_HOST,
                port=settings.TIMESCALE_PORT,
                database=settings.TIMESCALE_DB,
                user=settings.TIMESCALE_USER,
                password=settings.TIMESCALE_PASSWORD
            )

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT agent_id, symbol, side, quantity, price, commission,
                           pnl, leverage, executed_at as timestamp,
                           exit_price, holding_time, entry_time, exit_time
                    FROM trades
                    ORDER BY executed_at DESC
                    LIMIT %s
                """, (limit,))

                for row in cursor.fetchall():
                    all_trades.append({
                        'agent_id': row['agent_id'],
                        'symbol': row['symbol'],
                        'side': row['side'],
                        'quantity': float(row['quantity']) if row['quantity'] else 0,
                        'price': float(row['price']) if row['price'] else 0,
                        'commission': float(row['commission']) if row['commission'] else 0,
                        'pnl': float(row['pnl']) if row['pnl'] else None,
                        'leverage': float(row['leverage']) if row['leverage'] else 1.0,
                        'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None,
                        'exit_price': float(row['exit_price']) if row['exit_price'] else None,
                        'holding_time': row['holding_time'] if row['holding_time'] else None,
                        'entry_time': row['entry_time'].isoformat() if row['entry_time'] else None,
                        'exit_time': row['exit_time'].isoformat() if row['exit_time'] else None,
                    })

            conn.close()
        except Exception as e:
            logger.error(f"Error fetching trades from database: {e}")
            # Fallback to in-memory trades
            for agent_id, portfolio in self.portfolios.items():
                for trade in portfolio.trade_history:
                    trade_with_agent = trade.copy()
                    trade_with_agent['agent_id'] = agent_id
                    all_trades.append(trade_with_agent)

            # 按时间戳排序（最新的在前）
            all_trades.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            all_trades = all_trades[:limit]

        return all_trades

    def get_performance_by_agent(self) -> Dict[str, Dict]:
        """
        获取每个代理的性能指标

        Returns:
            代理ID -> 性能指标的字典
        """
        performance = {}

        for agent_id, portfolio in self.portfolios.items():
            trades = portfolio.trade_history

            if not trades:
                performance[agent_id] = {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'avg_profit': 0.0,
                    'avg_loss': 0.0
                }
                continue

            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
            losing_trades = sum(1 for t in trades if t.get('pnl', 0) < 0)

            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

            winning_pnls = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0]
            losing_pnls = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0]

            avg_profit = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0.0
            avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0.0

            total_pnl, _ = portfolio.get_pnl()

            performance[agent_id] = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_profit': round(avg_profit, 2),
                'avg_loss': round(avg_loss, 2)
            }

        return performance

    def update_all_prices(self, prices: Dict[str, float]):
        """
        更新所有代理投资组合中的持仓价格（包括内存和数据库）

        Args:
            prices: symbol -> price 的字典
        """
        # 更新内存中的持仓价格
        for symbol, price in prices.items():
            for portfolio in self.portfolios.values():
                if portfolio.has_position(symbol):
                    portfolio.update_position_price(symbol, price)

        # 更新数据库中的持仓价格和未实现盈亏
        try:
            from .config import get_settings
            import psycopg2

            settings = get_settings()
            conn = psycopg2.connect(
                host=settings.TIMESCALE_HOST,
                port=settings.TIMESCALE_PORT,
                database=settings.TIMESCALE_DB,
                user=settings.TIMESCALE_USER,
                password=settings.TIMESCALE_PASSWORD
            )

            with conn.cursor() as cursor:
                for symbol, current_price in prices.items():
                    # 计算未实现盈亏，根据side（做多/做空）不同计算方式不同
                    # 做多（long）: (current_price - entry_price) * quantity
                    # 做空（short）: (entry_price - current_price) * quantity
                    # 注意：杠杆不会放大绝对收益，只减少保证金需求
                    cursor.execute("""
                        UPDATE positions
                        SET current_price = %s,
                            unrealized_pnl = CASE
                                WHEN side = 'long' THEN ((%s - entry_price) * quantity)
                                WHEN side = 'short' THEN ((entry_price - %s) * quantity)
                                ELSE 0
                            END
                        WHERE symbol = %s AND is_closed = false
                    """, (current_price, current_price, current_price, symbol))

                conn.commit()

            conn.close()
            logger.debug(f"Updated database prices for {len(prices)} symbols")

        except Exception as e:
            logger.error(f"Error updating prices in database: {e}")
