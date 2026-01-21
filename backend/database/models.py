"""
Database models for AutoTrade AI system
"""
from datetime import datetime
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import settings

Base = declarative_base()


class Trade(Base):
    """Trade execution record"""
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)  # PERFORMANCE: Added index
    symbol = Column(String(20), nullable=False, index=True)
    order_type = Column(String(20), nullable=False)  # OPEN_LONG, OPEN_SHORT, CLOSE
    side = Column(String(10))  # LONG, SHORT
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    pnl = Column(Float)  # Realized PnL (for close orders)
    margin = Column(Float)
    leverage = Column(Integer)
    reason = Column(Text)  # AI decision reason

    def __repr__(self):
        return f"<Trade {self.symbol} {self.order_type} @ {self.price}>"


class AIDecision(Base):
    """AI decision log"""
    __tablename__ = 'ai_decisions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)

    # Model 1 (DeepSeek)
    model_1_name = Column(String(100))
    model_1_decision = Column(String(20))  # BUY, SELL, HOLD
    model_1_confidence = Column(Float)
    model_1_reasoning = Column(Text)
    model_1_response_time = Column(Float)  # Response time in seconds

    # Model 2 (Qwen)
    model_2_name = Column(String(100))
    model_2_decision = Column(String(20))
    model_2_confidence = Column(Float)
    model_2_reasoning = Column(Text)
    model_2_response_time = Column(Float)

    # Final decision
    final_decision = Column(String(20), nullable=False)
    decision_method = Column(String(50))  # majority, unanimous, weighted
    executed = Column(Boolean, default=False)
    execution_reason = Column(Text)

    # Input data snapshot
    technical_data = Column(JSON)
    fundamental_data = Column(JSON)
    market_data = Column(JSON)

    def __repr__(self):
        return f"<AIDecision {self.symbol} {self.final_decision} @ {self.timestamp}>"


class MarketDataCache(Base):
    """Cached market data"""
    __tablename__ = 'market_data_cache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)

    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    # Technical indicators (stored as JSON for flexibility)
    indicators = Column(JSON)

    def __repr__(self):
        return f"<MarketData {self.symbol} {self.timeframe} @ {self.timestamp}>"


class AccountSnapshot(Base):
    """Account equity snapshots for performance tracking"""
    __tablename__ = 'account_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)

    capital = Column(Float, nullable=False)
    total_margin = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    total_equity = Column(Float, nullable=False)

    open_positions = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_fees = Column(Float, default=0.0)

    # Position details (JSON)
    positions = Column(JSON)

    def __repr__(self):
        return f"<AccountSnapshot equity={self.total_equity} @ {self.timestamp}>"


class SystemLog(Base):
    """System events and errors log"""
    __tablename__ = 'system_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)
    level = Column(String(10), nullable=False)  # INFO, WARNING, ERROR
    category = Column(String(50), index=True)  # TRADING, AI, DATA, SYSTEM
    message = Column(Text, nullable=False)
    details = Column(JSON)

    def __repr__(self):
        return f"<SystemLog {self.level} {self.category} @ {self.timestamp}>"


# Global engine and session factory (singleton pattern)
_engine = None
_session_factory = None


def get_engine():
    """Get or create database engine (singleton)"""
    global _engine
    if _engine is not None:
        return _engine

    if settings:
        db_url = settings.database_url
    else:
        db_url = "sqlite:///autotrade.db"

    _engine = create_engine(db_url, echo=False)

    return _engine


def init_database():
    """Initialize database tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine


def get_session() -> Session:
    """Get database session from cached session factory"""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(bind=engine)
    return _session_factory()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Provides automatic transaction management:
    - Commits on successful completion
    - Rolls back on exception
    - Always closes the session

    Usage:
        with session_scope() as session:
            session.add(trade)
            # No need to call commit, rollback, or close

    Yields:
        SQLAlchemy Session object
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


__all__ = [
    "Base",
    "Trade",
    "AIDecision",
    "MarketDataCache",
    "AccountSnapshot",
    "SystemLog",
    "get_engine",
    "init_database",
    "get_session",
    "session_scope",
]
