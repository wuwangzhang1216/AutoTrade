import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.volatility import BollingerBands
import logging
from typing import List

from ..models import TechnicalIndicators, OHLCV

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """技术指标计算器"""

    @staticmethod
    def calculate_all(ohlcv_list: List[OHLCV]) -> TechnicalIndicators:
        """计算所有技术指标

        Args:
            ohlcv_list: OHLCV数据列表，按时间正序排列

        Returns:
            TechnicalIndicators对象
        """
        if not ohlcv_list or len(ohlcv_list) < 50:
            logger.warning(f"Insufficient data for indicators: {len(ohlcv_list)} records")
            return TechnicalIndicators()

        try:
            # 转换为DataFrame
            df = pd.DataFrame([
                {
                    'timestamp': ohlcv.timestamp,
                    'open': ohlcv.open,
                    'high': ohlcv.high,
                    'low': ohlcv.low,
                    'close': ohlcv.close,
                    'volume': ohlcv.volume
                }
                for ohlcv in ohlcv_list
            ])

            # 确保按时间排序
            df = df.sort_values('timestamp')

            close_prices = pd.Series(df['close'].values)

            indicators = {}

            # RSI (14)
            try:
                rsi_indicator = RSIIndicator(close=close_prices, window=14)
                indicators['rsi'] = float(rsi_indicator.rsi().iloc[-1])
            except Exception as e:
                logger.error(f"Error calculating RSI: {e}")
                indicators['rsi'] = None

            # MACD
            try:
                macd_indicator = MACD(close=close_prices)
                indicators['macd'] = float(macd_indicator.macd().iloc[-1])
                indicators['macd_signal'] = float(macd_indicator.macd_signal().iloc[-1])
                indicators['macd_hist'] = float(macd_indicator.macd_diff().iloc[-1])
            except Exception as e:
                logger.error(f"Error calculating MACD: {e}")
                indicators['macd'] = None
                indicators['macd_signal'] = None
                indicators['macd_hist'] = None

            # 移动平均线
            try:
                sma_20 = SMAIndicator(close=close_prices, window=20).sma_indicator().iloc[-1]
                sma_50 = SMAIndicator(close=close_prices, window=50).sma_indicator().iloc[-1]
                indicators['sma_20'] = float(sma_20)
                indicators['sma_50'] = float(sma_50)
            except Exception as e:
                logger.error(f"Error calculating SMA: {e}")
                indicators['sma_20'] = None
                indicators['sma_50'] = None

            # EMA
            try:
                ema_12 = EMAIndicator(close=close_prices, window=12).ema_indicator().iloc[-1]
                ema_26 = EMAIndicator(close=close_prices, window=26).ema_indicator().iloc[-1]
                indicators['ema_12'] = float(ema_12)
                indicators['ema_26'] = float(ema_26)
            except Exception as e:
                logger.error(f"Error calculating EMA: {e}")
                indicators['ema_12'] = None
                indicators['ema_26'] = None

            # 布林带
            try:
                bollinger = BollingerBands(close=close_prices, window=20, window_dev=2)
                indicators['bollinger_upper'] = float(bollinger.bollinger_hband().iloc[-1])
                indicators['bollinger_middle'] = float(bollinger.bollinger_mavg().iloc[-1])
                indicators['bollinger_lower'] = float(bollinger.bollinger_lband().iloc[-1])
            except Exception as e:
                logger.error(f"Error calculating Bollinger Bands: {e}")
                indicators['bollinger_upper'] = None
                indicators['bollinger_middle'] = None
                indicators['bollinger_lower'] = None

            return TechnicalIndicators(**indicators)

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return TechnicalIndicators()

    @staticmethod
    def calculate_from_dataframe(df: pd.DataFrame) -> TechnicalIndicators:
        """从DataFrame计算指标（用于TimescaleDB数据）"""
        if df.empty or len(df) < 50:
            logger.warning(f"Insufficient data for indicators: {len(df)} records")
            return TechnicalIndicators()

        try:
            close_prices = pd.Series(df['close'].values)

            indicators = {}

            # RSI
            try:
                rsi_indicator = RSIIndicator(close=close_prices, window=14)
                indicators['rsi'] = float(rsi_indicator.rsi().iloc[-1])
            except:
                indicators['rsi'] = None

            # MACD
            try:
                macd_indicator = MACD(close=close_prices)
                indicators['macd'] = float(macd_indicator.macd().iloc[-1])
                indicators['macd_signal'] = float(macd_indicator.macd_signal().iloc[-1])
                indicators['macd_hist'] = float(macd_indicator.macd_diff().iloc[-1])
            except:
                indicators['macd'] = None
                indicators['macd_signal'] = None
                indicators['macd_hist'] = None

            # SMA
            try:
                sma_20 = SMAIndicator(close=close_prices, window=20).sma_indicator().iloc[-1]
                sma_50 = SMAIndicator(close=close_prices, window=50).sma_indicator().iloc[-1]
                indicators['sma_20'] = float(sma_20)
                indicators['sma_50'] = float(sma_50)
            except:
                indicators['sma_20'] = None
                indicators['sma_50'] = None

            # EMA
            try:
                ema_12 = EMAIndicator(close=close_prices, window=12).ema_indicator().iloc[-1]
                ema_26 = EMAIndicator(close=close_prices, window=26).ema_indicator().iloc[-1]
                indicators['ema_12'] = float(ema_12)
                indicators['ema_26'] = float(ema_26)
            except:
                indicators['ema_12'] = None
                indicators['ema_26'] = None

            # Bollinger Bands
            try:
                bollinger = BollingerBands(close=close_prices, window=20, window_dev=2)
                indicators['bollinger_upper'] = float(bollinger.bollinger_hband().iloc[-1])
                indicators['bollinger_middle'] = float(bollinger.bollinger_mavg().iloc[-1])
                indicators['bollinger_lower'] = float(bollinger.bollinger_lband().iloc[-1])
            except:
                indicators['bollinger_upper'] = None
                indicators['bollinger_middle'] = None
                indicators['bollinger_lower'] = None

            return TechnicalIndicators(**indicators)

        except Exception as e:
            logger.error(f"Error calculating indicators from DataFrame: {e}")
            return TechnicalIndicators()
