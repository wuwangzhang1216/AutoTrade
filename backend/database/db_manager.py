"""
Database manager for AutoTrade AI system
"""
import json
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from utils.logger import logger, log_error
from .models import (
    Trade,
    AIDecision,
    MarketDataCache,
    AccountSnapshot,
    SystemLog,
    get_session,
    init_database
)


def serialize_for_json(obj: Any) -> Any:
    """
    Convert objects to JSON-serializable format

    Handles:
    - datetime objects -> ISO format strings
    - numpy types -> Python native types
    - nested dicts and lists

    Args:
        obj: Object to serialize

    Returns:
        JSON-serializable version of the object
    """
    if obj is None:
        return None
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj


class DatabaseManager:
    """
    Manages database operations
    """

    def __init__(self):
        """Initialize database"""
        init_database()
        logger.info("Database initialized")

    def log_trade(
        self,
        symbol: str,
        order_type: str,
        amount: float,
        price: float,
        **kwargs
    ) -> Trade:
        """
        Log a trade to database

        Args:
            symbol: Trading pair
            order_type: Order type
            amount: Position size
            price: Execution price
            **kwargs: Additional fields

        Returns:
            Trade object
        """
        session = get_session()

        try:
            trade = Trade(
                symbol=symbol,
                order_type=order_type,
                amount=amount,
                price=price,
                **kwargs
            )

            session.add(trade)
            session.commit()
            session.refresh(trade)

            logger.debug(f"Trade logged: {trade}")

            return trade

        except Exception as e:
            session.rollback()
            log_error(f"Failed to log trade: {e}")
            raise
        finally:
            # BUG FIX: Ensure session is always closed, even on exception
            session.close()

    def log_ai_decision(
        self,
        symbol: str,
        model_1_data: Dict,
        model_2_data: Dict,
        final_decision: str,
        **kwargs
    ) -> AIDecision:
        """
        Log AI decision to database

        Args:
            symbol: Trading pair
            model_1_data: Model 1 decision data
            model_2_data: Model 2 decision data
            final_decision: Final decision
            **kwargs: Additional fields (technical_data, fundamental_data, market_data, etc.)

        Returns:
            AIDecision object
        """
        session = get_session()

        try:
            # Serialize JSON fields to handle datetime and numpy types
            serialized_kwargs = {}
            for key, value in kwargs.items():
                if key in ('technical_data', 'fundamental_data', 'market_data', 'details'):
                    # These fields are JSON - serialize special types
                    serialized_kwargs[key] = serialize_for_json(value)
                else:
                    serialized_kwargs[key] = value

            decision = AIDecision(
                symbol=symbol,
                model_1_name=model_1_data.get('model'),
                model_1_decision=model_1_data.get('decision'),
                model_1_confidence=model_1_data.get('confidence'),
                model_1_reasoning=model_1_data.get('reasoning'),
                model_1_response_time=model_1_data.get('response_time'),
                model_2_name=model_2_data.get('model'),
                model_2_decision=model_2_data.get('decision'),
                model_2_confidence=model_2_data.get('confidence'),
                model_2_reasoning=model_2_data.get('reasoning'),
                model_2_response_time=model_2_data.get('response_time'),
                final_decision=final_decision,
                **serialized_kwargs
            )

            session.add(decision)
            session.commit()
            session.refresh(decision)

            logger.debug(f"AI decision logged: {decision}")

            return decision

        except Exception as e:
            session.rollback()
            log_error(f"Failed to log AI decision: {e}")
            raise
        finally:
            # BUG FIX: Ensure session is always closed, even on exception
            session.close()

    def save_account_snapshot(self, account_data: Dict) -> AccountSnapshot:
        """
        Save account snapshot with time-based deduplication

        Args:
            account_data: Account data dict (may contain positions JSON with numpy types)

        Returns:
            AccountSnapshot object (may return existing snapshot if too recent)
        """
        session = get_session()

        try:
            # BUG FIX: Prevent saving snapshots too frequently to avoid chart oscillations
            # AI decision cycle runs every 5 minutes, so use 4-minute window to prevent
            # multiple snapshots per AI cycle (before and after trade execution)
            from datetime import datetime, timedelta

            four_minutes_ago = datetime.now() - timedelta(seconds=240)
            recent_snapshot = session.query(AccountSnapshot)\
                .filter(AccountSnapshot.timestamp >= four_minutes_ago)\
                .order_by(AccountSnapshot.timestamp.desc())\
                .first()

            if recent_snapshot:
                # Snapshot already exists within last 4 minutes, don't save duplicate
                logger.debug(f"Skipping snapshot save - recent snapshot exists from {recent_snapshot.timestamp}")
                return recent_snapshot

            # BUG FIX: Calculate actual trade statistics from database, not from memory
            # Memory statistics reset on program restart, but database persists
            # Only CLOSE trades count as completed trades (not OPEN trades)
            close_trades = session.query(Trade).filter(
                Trade.order_type.in_(['CLOSE_LONG', 'CLOSE_SHORT'])
            ).all()

            # BUG FIX: total_trades should only count CLOSE trades, not all trades
            # Each completed trade has 1 OPEN + 1 CLOSE, so we only count CLOSE
            total_trades_count = len(close_trades)

            # Calculate winning/losing trades by checking PnL on CLOSE trades
            # BUG FIX: Only count trades with non-null PnL
            winning_trades_count = sum(1 for t in close_trades if t.pnl is not None and t.pnl > 0)
            losing_trades_count = sum(1 for t in close_trades if t.pnl is not None and t.pnl < 0)

            # Serialize positions field to handle numpy types
            serialized_data = dict(account_data)
            if 'positions' in serialized_data:
                serialized_data['positions'] = serialize_for_json(serialized_data['positions'])

            # Override statistics with actual database values
            serialized_data['total_trades'] = total_trades_count
            serialized_data['winning_trades'] = winning_trades_count
            serialized_data['losing_trades'] = losing_trades_count

            snapshot = AccountSnapshot(**serialized_data)

            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)

            logger.debug(f"Account snapshot saved: equity={snapshot.total_equity}, trades={total_trades_count} (W:{winning_trades_count}/L:{losing_trades_count})")

            return snapshot

        except Exception as e:
            session.rollback()
            log_error(f"Failed to save account snapshot: {e}")
            raise
        finally:
            # BUG FIX: Ensure session is always closed, even on exception
            session.close()

    def log_system_event(
        self,
        level: str,
        category: str,
        message: str,
        details: Optional[Dict] = None
    ):
        """
        Log system event

        Args:
            level: Log level (INFO, WARNING, ERROR)
            category: Event category
            message: Log message
            details: Additional details (JSON)
        """
        session = get_session()

        try:
            # Serialize details to handle datetime and numpy types
            serialized_details = serialize_for_json(details) if details else None

            log = SystemLog(
                level=level,
                category=category,
                message=message,
                details=serialized_details
            )

            session.add(log)
            session.commit()

        except Exception as e:
            session.rollback()
            log_error(f"Failed to log system event: {e}")
        finally:
            # BUG FIX: Ensure session is always closed, even on exception
            session.close()

    def get_recent_trades(self, limit: int = 50, symbol: Optional[str] = None) -> List[Trade]:
        """Get recent trades"""
        session = get_session()

        try:
            query = session.query(Trade).order_by(Trade.timestamp.desc())

            if symbol:
                query = query.filter(Trade.symbol == symbol)

            trades = query.limit(limit).all()

            return trades

        finally:
            # BUG FIX: Ensure session is always closed
            session.close()

    def get_recent_ai_decisions(self, limit: int = 50, symbol: Optional[str] = None) -> List[AIDecision]:
        """Get recent AI decisions"""
        session = get_session()

        try:
            query = session.query(AIDecision).order_by(AIDecision.timestamp.desc())

            if symbol:
                query = query.filter(AIDecision.symbol == symbol)

            decisions = query.limit(limit).all()

            return decisions

        finally:
            # BUG FIX: Ensure session is always closed
            session.close()

    def update_ai_decision_execution(
        self,
        decision_id: int,
        executed: bool = True,
        execution_reason: Optional[str] = None
    ) -> bool:
        """
        Update AI decision execution status

        Args:
            decision_id: AIDecision ID to update
            executed: Execution status
            execution_reason: Reason for execution/non-execution

        Returns:
            True if successful
        """
        session = get_session()

        try:
            decision = session.query(AIDecision).filter(AIDecision.id == decision_id).first()

            if not decision:
                log_error(f"AI decision {decision_id} not found")
                return False

            decision.executed = executed
            if execution_reason:
                decision.execution_reason = execution_reason

            session.commit()

            logger.debug(f"AI decision {decision_id} updated: executed={executed}")

            return True

        except Exception as e:
            session.rollback()
            log_error(f"Failed to update AI decision: {e}")
            return False
        finally:
            # BUG FIX: Ensure session is always closed
            session.close()

    def get_account_history(self, days: int = 30) -> List[AccountSnapshot]:
        """Get account equity history"""
        session = get_session()

        try:
            cutoff = datetime.now() - timedelta(days=days)

            snapshots = session.query(AccountSnapshot)\
                .filter(AccountSnapshot.timestamp >= cutoff)\
                .order_by(AccountSnapshot.timestamp.asc())\
                .all()

            return snapshots

        finally:
            # BUG FIX: Ensure session is always closed
            session.close()

    def get_performance_stats(self) -> Dict:
        """Get overall performance statistics"""
        session = get_session()

        try:
            # Get latest snapshot
            latest_snapshot = session.query(AccountSnapshot)\
                .order_by(AccountSnapshot.timestamp.desc())\
                .first()

            if not latest_snapshot:
                return {}

            # Get first snapshot
            first_snapshot = session.query(AccountSnapshot)\
                .order_by(AccountSnapshot.timestamp.asc())\
                .first()

            # Calculate stats
            # BUG FIX: Prevent division by zero when first_snapshot.total_equity is 0
            total_return = latest_snapshot.total_equity - first_snapshot.total_equity
            if first_snapshot.total_equity > 0:
                total_return_pct = (total_return / first_snapshot.total_equity) * 100
            else:
                total_return_pct = 0.0

            # Get all trades
            all_trades = session.query(Trade).filter(Trade.pnl.isnot(None)).all()

            winning_trades = [t for t in all_trades if t.pnl > 0]
            losing_trades = [t for t in all_trades if t.pnl < 0]

            total_wins = sum(t.pnl for t in winning_trades)
            total_losses = sum(abs(t.pnl) for t in losing_trades)

            avg_win = total_wins / len(winning_trades) if winning_trades else 0
            avg_loss = total_losses / len(losing_trades) if losing_trades else 0

            # BUG FIX: Improve profit_factor calculation
            # Return a reasonable large number instead of inf for better JSON serialization
            if total_losses > 0:
                profit_factor = total_wins / total_losses
            elif total_wins > 0:
                profit_factor = 999.99  # Large number instead of inf
            else:
                profit_factor = 0.0

            return {
                'total_return': total_return,
                'total_return_pct': total_return_pct,
                'total_trades': latest_snapshot.total_trades,
                'winning_trades': latest_snapshot.winning_trades,
                'losing_trades': latest_snapshot.losing_trades,
                'win_rate': (latest_snapshot.winning_trades / latest_snapshot.total_trades * 100) if latest_snapshot.total_trades > 0 else 0,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'total_fees': latest_snapshot.total_fees,
                'current_equity': latest_snapshot.total_equity,
            }

        finally:
            # BUG FIX: Ensure session is always closed
            session.close()


# Singleton instance
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


__all__ = ["DatabaseManager", "get_db_manager"]
