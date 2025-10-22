from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import pandas as pd
import logging
from typing import List, Optional

from ..models import OHLCV

logger = logging.getLogger(__name__)

Base = declarative_base()


class OHLCVRecord(Base):
    """OHLCV表模型"""
    __tablename__ = "ohlcv"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )


class TimescaleDB:
    """TimescaleDB管理"""

    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
        self._initialized = False

    def initialize(self):
        """初始化数据库"""
        if self._initialized:
            return

        try:
            # 创建表
            Base.metadata.create_all(self.engine)

            # 创建Hypertable（如果不存在）
            with self.engine.connect() as conn:
                # 检查是否已经是hypertable
                result = conn.execute("""
                    SELECT * FROM timescaledb_information.hypertables
                    WHERE hypertable_name = 'ohlcv'
                """)

                if result.rowcount == 0:
                    conn.execute("""
                        SELECT create_hypertable('ohlcv', 'timestamp',
                            if_not_exists => TRUE);
                    """)
                    logger.info("Created hypertable for ohlcv")

                conn.commit()

            self._initialized = True
            logger.info("TimescaleDB initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing TimescaleDB: {e}")
            # 如果不是TimescaleDB，继续使用普通PostgreSQL
            Base.metadata.create_all(self.engine)
            self._initialized = True
            logger.warning("Running without TimescaleDB extension")

    def save_ohlcv(self, ohlcv: OHLCV):
        """保存OHLCV数据"""
        session: Session = self.Session()
        try:
            # 检查是否已存在
            existing = session.query(OHLCVRecord).filter_by(
                symbol=ohlcv.symbol,
                timestamp=ohlcv.timestamp
            ).first()

            if existing:
                # 更新现有记录
                existing.open = ohlcv.open
                existing.high = ohlcv.high
                existing.low = ohlcv.low
                existing.close = ohlcv.close
                existing.volume = ohlcv.volume
            else:
                # 插入新记录
                record = OHLCVRecord(
                    symbol=ohlcv.symbol,
                    timestamp=ohlcv.timestamp,
                    open=ohlcv.open,
                    high=ohlcv.high,
                    low=ohlcv.low,
                    close=ohlcv.close,
                    volume=ohlcv.volume
                )
                session.add(record)

            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving OHLCV for {ohlcv.symbol}: {e}")
            raise
        finally:
            session.close()

    def save_ohlcv_batch(self, ohlcv_list: List[OHLCV]):
        """批量保存OHLCV数据"""
        session: Session = self.Session()
        try:
            for ohlcv in ohlcv_list:
                # 检查是否已存在
                existing = session.query(OHLCVRecord).filter_by(
                    symbol=ohlcv.symbol,
                    timestamp=ohlcv.timestamp
                ).first()

                if not existing:
                    record = OHLCVRecord(
                        symbol=ohlcv.symbol,
                        timestamp=ohlcv.timestamp,
                        open=ohlcv.open,
                        high=ohlcv.high,
                        low=ohlcv.low,
                        close=ohlcv.close,
                        volume=ohlcv.volume
                    )
                    session.add(record)

            session.commit()
            logger.info(f"Saved {len(ohlcv_list)} OHLCV records")

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving OHLCV batch: {e}")
            raise
        finally:
            session.close()

    def get_historical_data(
        self,
        symbol: str,
        limit: int = 100
    ) -> pd.DataFrame:
        """获取历史数据用于技术指标计算

        Args:
            symbol: 交易对
            limit: 返回记录数

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            query = f"""
                SELECT timestamp, open, high, low, close, volume
                FROM ohlcv
                WHERE symbol = '{symbol}'
                ORDER BY timestamp DESC
                LIMIT {limit}
            """
            df = pd.read_sql(query, self.engine)

            # 按时间正序排列（旧->新）用于指标计算
            df = df.sort_values('timestamp')

            return df

        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()

    def get_latest_ohlcv(self, symbol: str) -> Optional[OHLCV]:
        """获取最新的OHLCV记录"""
        session: Session = self.Session()
        try:
            record = session.query(OHLCVRecord).filter_by(
                symbol=symbol
            ).order_by(OHLCVRecord.timestamp.desc()).first()

            if record:
                return OHLCV(
                    symbol=record.symbol,
                    timestamp=record.timestamp,
                    open=record.open,
                    high=record.high,
                    low=record.low,
                    close=record.close,
                    volume=record.volume
                )
            return None

        except Exception as e:
            logger.error(f"Error getting latest OHLCV for {symbol}: {e}")
            return None
        finally:
            session.close()

    def health_check(self) -> bool:
        """健康检查"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"TimescaleDB health check failed: {e}")
            return False
