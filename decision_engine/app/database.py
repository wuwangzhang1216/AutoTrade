from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Text, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import logging
from typing import List, Optional

from .models.trading import (
    Position, AccountState, TradingDecision,
    Trade, ActionType
)

logger = logging.getLogger(__name__)

Base = declarative_base()


class AgentRecord(Base):
    """代理记录表"""
    __tablename__ = "agents"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)
    initial_balance = Column(Float, nullable=False)
    current_balance = Column(Float, nullable=False)
    total_pnl = Column(Float, default=0)
    trade_count = Column(Integer, default=0)
    win_count = Column(Integer, default=0)
    loss_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class PositionRecord(Base):
    """持仓记录表"""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    unrealized_pnl = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    entry_time = Column(DateTime, nullable=False)
    side = Column(String(10), default="long")
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime)


class DecisionRecord(Base):
    """决策记录表"""
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    action = Column(String(20), nullable=False)
    symbol = Column(String(20))
    quantity = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    reasoning = Column(Text, nullable=False)
    confidence = Column(Float)
    raw_response = Column(Text)
    current_price = Column(Float)
    created_at = Column(DateTime, default=datetime.now)


class TradeRecord(Base):
    """交易执行记录表"""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), nullable=False, index=True)
    decision_id = Column(Integer)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    pnl = Column(Float)
    executed_at = Column(DateTime, nullable=False, index=True)
    is_simulated = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


class Database:
    """数据库管理"""

    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
        self._initialized = False

    def initialize(self):
        """初始化数据库"""
        if self._initialized:
            return

        Base.metadata.create_all(self.engine)
        self._initialized = True
        logger.info("Database initialized successfully")

    # Agent操作
    def create_agent(
        self,
        agent_id: str,
        name: str,
        model_type: str,
        initial_balance: float
    ):
        """创建代理记录"""
        session: Session = self.Session()
        try:
            # 检查是否已存在
            existing = session.query(AgentRecord).filter_by(id=agent_id).first()

            if existing:
                logger.info(f"Agent {agent_id} already exists")
                return

            agent = AgentRecord(
                id=agent_id,
                name=name,
                model_type=model_type,
                initial_balance=initial_balance,
                current_balance=initial_balance
            )
            session.add(agent)
            session.commit()
            logger.info(f"Created agent record: {agent_id}")

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating agent: {e}")
            raise
        finally:
            session.close()

    def get_agent(self, agent_id: str) -> Optional[AgentRecord]:
        """获取代理记录"""
        session: Session = self.Session()
        try:
            return session.query(AgentRecord).filter_by(id=agent_id).first()
        finally:
            session.close()

    def update_agent_balance(self, agent_id: str, balance: float, pnl: float):
        """更新代理余额"""
        session: Session = self.Session()
        try:
            agent = session.query(AgentRecord).filter_by(id=agent_id).first()
            if agent:
                agent.current_balance = balance
                agent.total_pnl = pnl
                agent.updated_at = datetime.now()
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating agent balance: {e}")
        finally:
            session.close()

    # 决策操作
    def save_decision(self, decision: TradingDecision) -> int:
        """保存决策记录"""
        session: Session = self.Session()
        try:
            # Since TradingDecision has use_enum_values=True, action is already a string
            # Handle both enum and string types for compatibility
            action_value = decision.action.value if hasattr(decision.action, 'value') else decision.action

            record = DecisionRecord(
                agent_id=decision.agent_id,
                timestamp=decision.timestamp,
                action=action_value,
                symbol=decision.symbol,
                quantity=decision.quantity,
                stop_loss=decision.stop_loss,
                take_profit=decision.take_profit,
                reasoning=decision.reasoning,
                confidence=decision.confidence,
                raw_response=decision.raw_response,
                current_price=decision.current_price
            )
            session.add(record)
            session.commit()

            decision_id = record.id
            logger.info(f"Saved decision {decision_id} for agent {decision.agent_id}: {action_value} {decision.symbol}")
            return decision_id

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving decision: {e}")
            raise
        finally:
            session.close()

    def get_recent_decisions(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[DecisionRecord]:
        """获取最近的决策记录"""
        session: Session = self.Session()
        try:
            return session.query(DecisionRecord).filter_by(
                agent_id=agent_id
            ).order_by(DecisionRecord.timestamp.desc()).limit(limit).all()
        finally:
            session.close()

    # 持仓操作
    def create_position(self, position: Position, agent_id: str) -> int:
        """创建持仓记录"""
        session: Session = self.Session()
        try:
            record = PositionRecord(
                agent_id=agent_id,
                symbol=position.symbol,
                quantity=position.quantity,
                entry_price=position.entry_price,
                current_price=position.current_price,
                unrealized_pnl=position.unrealized_pnl,
                stop_loss=position.stop_loss,
                take_profit=position.take_profit,
                entry_time=position.entry_time,
                side=position.side
            )
            session.add(record)
            session.commit()

            position_id = record.id
            logger.info(f"Created position {position_id} for agent {agent_id}")
            return position_id

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating position: {e}")
            raise
        finally:
            session.close()

    def update_position(self, position_id: int, current_price: float, unrealized_pnl: float):
        """更新持仓"""
        session: Session = self.Session()
        try:
            position = session.query(PositionRecord).filter_by(id=position_id).first()
            if position:
                position.current_price = current_price
                position.unrealized_pnl = unrealized_pnl
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating position: {e}")
        finally:
            session.close()

    def close_position(self, position_id: int):
        """关闭持仓"""
        session: Session = self.Session()
        try:
            position = session.query(PositionRecord).filter_by(id=position_id).first()
            if position:
                position.is_closed = True
                position.closed_at = datetime.now()
                session.commit()
                logger.info(f"Closed position {position_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error closing position: {e}")
        finally:
            session.close()

    def get_open_positions(self, agent_id: str) -> List[PositionRecord]:
        """获取未平仓持仓"""
        session: Session = self.Session()
        try:
            return session.query(PositionRecord).filter_by(
                agent_id=agent_id,
                is_closed=False
            ).all()
        finally:
            session.close()

    # 交易操作
    def save_trade(self, trade: Trade) -> int:
        """保存交易记录"""
        session: Session = self.Session()
        try:
            record = TradeRecord(
                agent_id=trade.agent_id,
                decision_id=trade.decision_id,
                symbol=trade.symbol,
                side=trade.side,
                quantity=trade.quantity,
                price=trade.price,
                commission=trade.commission,
                pnl=trade.pnl,
                executed_at=trade.executed_at,
                is_simulated=trade.is_simulated
            )
            session.add(record)
            session.commit()

            # 更新代理交易计数
            agent = session.query(AgentRecord).filter_by(id=trade.agent_id).first()
            if agent:
                agent.trade_count += 1
                if trade.pnl and trade.pnl > 0:
                    agent.win_count += 1
                elif trade.pnl and trade.pnl < 0:
                    agent.loss_count += 1
                session.commit()

            trade_id = record.id
            logger.info(f"Saved trade {trade_id} for agent {trade.agent_id}")
            return trade_id

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving trade: {e}")
            raise
        finally:
            session.close()

    def get_account_state(self, agent_id: str) -> Optional[AccountState]:
        """获取账户状态"""
        session: Session = self.Session()
        try:
            agent = session.query(AgentRecord).filter_by(id=agent_id).first()
            if not agent:
                return None

            # 获取未平仓持仓
            position_records = session.query(PositionRecord).filter_by(
                agent_id=agent_id,
                is_closed=False
            ).all()

            positions = [
                Position(
                    id=p.id,
                    symbol=p.symbol,
                    quantity=p.quantity,
                    entry_price=p.entry_price,
                    current_price=p.current_price,
                    unrealized_pnl=p.unrealized_pnl,
                    stop_loss=p.stop_loss,
                    take_profit=p.take_profit,
                    entry_time=p.entry_time,
                    side=p.side
                )
                for p in position_records
            ]

            # 计算总价值
            total_value = agent.current_balance + sum(p.unrealized_pnl for p in positions)

            return AccountState(
                agent_id=agent_id,
                balance=agent.current_balance,
                total_value=total_value,
                positions=positions,
                total_pnl=agent.total_pnl,
                trade_count=agent.trade_count,
                win_count=agent.win_count,
                loss_count=agent.loss_count
            )

        finally:
            session.close()

    def health_check(self) -> bool:
        """健康检查"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
