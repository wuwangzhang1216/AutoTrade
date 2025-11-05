"""
Technical analysis indicators using pandas-ta
"""
import pandas as pd
import pandas_ta as ta
from typing import Dict, List, Optional
from utils.logger import logger
from config import TechnicalIndicatorsConfig


class TechnicalAnalyzer:
    """
    Calculates technical indicators for trading analysis
    """

    def __init__(self):
        logger.info("Technical Analyzer initialized")

    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all configured technical indicators

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added indicator columns
        """
        if df is None or df.empty:
            logger.warning("Empty dataframe provided for technical analysis")
            return df

        # Make a copy to avoid modifying original
        df = df.copy()

        # Moving Averages
        for period in TechnicalIndicatorsConfig.MA_PERIODS:
            df[f'MA_{period}'] = ta.sma(df['close'], length=period)

        # Exponential Moving Averages
        for period in TechnicalIndicatorsConfig.EMA_PERIODS:
            df[f'EMA_{period}'] = ta.ema(df['close'], length=period)

        # MACD
        macd = ta.macd(
            df['close'],
            fast=TechnicalIndicatorsConfig.MACD_FAST,
            slow=TechnicalIndicatorsConfig.MACD_SLOW,
            signal=TechnicalIndicatorsConfig.MACD_SIGNAL
        )
        if macd is not None:
            df = pd.concat([df, macd], axis=1)

        # RSI
        df['RSI'] = ta.rsi(df['close'], length=TechnicalIndicatorsConfig.RSI_PERIOD)

        # Bollinger Bands
        bbands = ta.bbands(
            df['close'],
            length=TechnicalIndicatorsConfig.BB_PERIOD,
            std=TechnicalIndicatorsConfig.BB_STD
        )
        if bbands is not None:
            df = pd.concat([df, bbands], axis=1)

        # ATR (Average True Range)
        df['ATR'] = ta.atr(
            df['high'],
            df['low'],
            df['close'],
            length=TechnicalIndicatorsConfig.ATR_PERIOD
        )

        # Stochastic Oscillator
        stoch = ta.stoch(df['high'], df['low'], df['close'])
        if stoch is not None:
            df = pd.concat([df, stoch], axis=1)

        # Volume indicators
        df['OBV'] = ta.obv(df['close'], df['volume'])  # On-Balance Volume

        # Momentum
        df['MOM'] = ta.mom(df['close'], length=10)

        # ADX (Average Directional Index)
        adx = ta.adx(df['high'], df['low'], df['close'])
        if adx is not None:
            df = pd.concat([df, adx], axis=1)

        logger.debug(f"Calculated technical indicators for {len(df)} candles")

        return df

    def get_trend_signals(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Get trend signals from indicators

        Args:
            df: DataFrame with calculated indicators

        Returns:
            Dict with trend signals
        """
        if df is None or df.empty or len(df) < 2:
            return {}

        latest = df.iloc[-1]
        previous = df.iloc[-2]

        signals = {}

        # MA Crossover
        if 'MA_10' in df.columns and 'MA_30' in df.columns:
            ma10 = latest['MA_10']
            ma30 = latest['MA_30']
            prev_ma10 = previous['MA_10']
            prev_ma30 = previous['MA_30']

            if pd.notna(ma10) and pd.notna(ma30):
                if ma10 > ma30 and prev_ma10 <= prev_ma30:
                    signals['ma_cross'] = 'golden_cross'  # Bullish
                elif ma10 < ma30 and prev_ma10 >= prev_ma30:
                    signals['ma_cross'] = 'death_cross'  # Bearish
                elif ma10 > ma30:
                    signals['ma_cross'] = 'bullish'
                else:
                    signals['ma_cross'] = 'bearish'

        # MACD Signal
        if 'MACD_12_26_9' in df.columns and 'MACDs_12_26_9' in df.columns:
            macd = latest['MACD_12_26_9']
            signal = latest['MACDs_12_26_9']

            if pd.notna(macd) and pd.notna(signal):
                if macd > signal:
                    signals['macd'] = 'bullish'
                else:
                    signals['macd'] = 'bearish'

        # RSI Signal
        if 'RSI' in df.columns:
            rsi = latest['RSI']

            if pd.notna(rsi):
                if rsi > TechnicalIndicatorsConfig.RSI_OVERBOUGHT:
                    signals['rsi'] = 'overbought'
                elif rsi < TechnicalIndicatorsConfig.RSI_OVERSOLD:
                    signals['rsi'] = 'oversold'
                elif rsi > 50:
                    signals['rsi'] = 'bullish'
                else:
                    signals['rsi'] = 'bearish'

        # Bollinger Bands
        if 'BBL_20_2.0' in df.columns and 'BBU_20_2.0' in df.columns:
            price = latest['close']
            bb_lower = latest['BBL_20_2.0']
            bb_upper = latest['BBU_20_2.0']

            if pd.notna(bb_lower) and pd.notna(bb_upper):
                if price <= bb_lower:
                    signals['bb'] = 'oversold'
                elif price >= bb_upper:
                    signals['bb'] = 'overbought'
                else:
                    signals['bb'] = 'neutral'

        # Stochastic
        if 'STOCHk_14_3_3' in df.columns:
            stoch_k = latest['STOCHk_14_3_3']

            if pd.notna(stoch_k):
                if stoch_k > 80:
                    signals['stoch'] = 'overbought'
                elif stoch_k < 20:
                    signals['stoch'] = 'oversold'
                else:
                    signals['stoch'] = 'neutral'

        # ADX Trend Strength
        if 'ADX_14' in df.columns:
            adx = latest['ADX_14']

            if pd.notna(adx):
                if adx > 25:
                    signals['trend_strength'] = 'strong'
                elif adx > 20:
                    signals['trend_strength'] = 'moderate'
                else:
                    signals['trend_strength'] = 'weak'

        return signals

    def get_support_resistance(self, df: pd.DataFrame, lookback: int = 20) -> Dict:
        """
        Calculate support and resistance levels

        Args:
            df: DataFrame with OHLCV data
            lookback: Number of candles to look back

        Returns:
            Dict with support/resistance levels
        """
        if df is None or df.empty or len(df) < lookback:
            return {}

        recent_df = df.tail(lookback)

        support = recent_df['low'].min()
        resistance = recent_df['high'].max()
        current_price = df.iloc[-1]['close']

        return {
            'support': support,
            'resistance': resistance,
            'current': current_price,
            'distance_to_support': ((current_price - support) / current_price) * 100,
            'distance_to_resistance': ((resistance - current_price) / current_price) * 100,
        }

    def get_trading_summary(self, df: pd.DataFrame, symbol: str = "") -> Dict:
        """
        Get comprehensive trading summary

        Args:
            df: DataFrame with calculated indicators
            symbol: Trading pair symbol

        Returns:
            Dict with trading summary
        """
        if df is None or df.empty:
            return {}

        latest = df.iloc[-1]
        signals = self.get_trend_signals(df)
        sr_levels = self.get_support_resistance(df)

        # Count bullish vs bearish signals
        bullish_signals = sum(
            1 for signal in signals.values()
            if signal in ['bullish', 'golden_cross', 'oversold']
        )

        bearish_signals = sum(
            1 for signal in signals.values()
            if signal in ['bearish', 'death_cross', 'overbought']
        )

        total_signals = bullish_signals + bearish_signals
        if total_signals > 0:
            bullish_percent = (bullish_signals / total_signals) * 100
        else:
            bullish_percent = 50

        # Overall recommendation
        if bullish_percent >= 70:
            recommendation = 'STRONG_BUY'
        elif bullish_percent >= 55:
            recommendation = 'BUY'
        elif bullish_percent >= 45:
            recommendation = 'HOLD'
        elif bullish_percent >= 30:
            recommendation = 'SELL'
        else:
            recommendation = 'STRONG_SELL'

        summary = {
            'symbol': symbol,
            'current_price': latest['close'],
            'volume': latest['volume'],
            'recommendation': recommendation,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'bullish_percent': round(bullish_percent, 2),
            'signals': signals,
            'support_resistance': sr_levels,
            'key_indicators': {
                'rsi': latest.get('RSI'),
                'macd': latest.get('MACD_12_26_9'),
                'adx': latest.get('ADX_14'),
            }
        }

        return summary


__all__ = ["TechnicalAnalyzer"]
