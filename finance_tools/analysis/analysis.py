# finance_tools/analysis/analysis.py
"""
Main technical analysis module providing comprehensive financial indicators.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union, Optional, Tuple
import logging

# Configure logging
logger = logging.getLogger(__name__)


def calculate_ema(data: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA).
    
    Args:
        data: Price series (usually close prices)
        period: EMA period (default: 20)
    
    Returns:
        pd.Series: EMA values
    """
    try:
        if not isinstance(data, pd.Series):
            raise ValueError("Data must be a pandas Series")
        
        if period <= 0:
            raise ValueError("Period must be positive")
        
        # Calculate EMA
        ema = data.ewm(span=period, adjust=False).mean()
        
        logger.debug(f"Calculated EMA with period {period}")
        return ema
        
    except Exception as e:
        logger.error(f"Error calculating EMA: {str(e)}")
        raise


def calculate_sma(data: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate Simple Moving Average (SMA).
    
    Args:
        data: Price series (usually close prices)
        period: SMA period (default: 20)
    
    Returns:
        pd.Series: SMA values
    """
    try:
        if not isinstance(data, pd.Series):
            raise ValueError("Data must be a pandas Series")
        
        if period <= 0:
            raise ValueError("Period must be positive")
        
        # Calculate SMA
        sma = data.rolling(window=period).mean()
        
        logger.debug(f"Calculated SMA with period {period}")
        return sma
        
    except Exception as e:
        logger.error(f"Error calculating SMA: {str(e)}")
        raise


def calculate_wma(data: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate Weighted Moving Average (WMA).
    
    Args:
        data: Price series (usually close prices)
        period: WMA period (default: 20)
    
    Returns:
        pd.Series: WMA values
    """
    try:
        if not isinstance(data, pd.Series):
            raise ValueError("Data must be a pandas Series")
        
        if period <= 0:
            raise ValueError("Period must be positive")
        
        # Calculate weights
        weights = np.arange(1, period + 1)
        
        # Calculate WMA
        wma = data.rolling(window=period).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )
        
        logger.debug(f"Calculated WMA with period {period}")
        return wma
        
    except Exception as e:
        logger.error(f"Error calculating WMA: {str(e)}")
        raise


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        data: Price series (usually close prices)
        period: RSI period (default: 14)
    
    Returns:
        pd.Series: RSI values (0-100)
    """
    try:
        if not isinstance(data, pd.Series):
            raise ValueError("Data must be a pandas Series")
        
        if period <= 0:
            raise ValueError("Period must be positive")
        
        # Calculate price changes
        delta = data.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        logger.debug(f"Calculated RSI with period {period}")
        return rsi
        
    except Exception as e:
        logger.error(f"Error calculating RSI: {str(e)}")
        raise


def calculate_macd(data: pd.Series, fast_period: int = 12, slow_period: int = 26, 
                  signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        data: Price series (usually close prices)
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line period (default: 9)
    
    Returns:
        Tuple[pd.Series, pd.Series, pd.Series]: (MACD line, Signal line, Histogram)
    """
    try:
        if not isinstance(data, pd.Series):
            raise ValueError("Data must be a pandas Series")
        
        if fast_period <= 0 or slow_period <= 0 or signal_period <= 0:
            raise ValueError("All periods must be positive")
        
        if fast_period >= slow_period:
            raise ValueError("Fast period must be less than slow period")
        
        # Calculate EMAs
        fast_ema = calculate_ema(data, fast_period)
        slow_ema = calculate_ema(data, slow_period)
        
        # Calculate MACD line
        macd_line = fast_ema - slow_ema
        
        # Calculate signal line
        signal_line = calculate_ema(macd_line, signal_period)
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        logger.debug(f"Calculated MACD with fast={fast_period}, slow={slow_period}, signal={signal_period}")
        return macd_line, signal_line, histogram
        
    except Exception as e:
        logger.error(f"Error calculating MACD: {str(e)}")
        raise


def calculate_bollinger_bands(data: pd.Series, period: int = 20, 
                            std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Args:
        data: Price series (usually close prices)
        period: SMA period (default: 20)
        std_dev: Standard deviation multiplier (default: 2.0)
    
    Returns:
        Tuple[pd.Series, pd.Series, pd.Series]: (Upper band, Middle band, Lower band)
    """
    try:
        if not isinstance(data, pd.Series):
            raise ValueError("Data must be a pandas Series")
        
        if period <= 0:
            raise ValueError("Period must be positive")
        
        if std_dev <= 0:
            raise ValueError("Standard deviation must be positive")
        
        # Calculate middle band (SMA)
        middle_band = calculate_sma(data, period)
        
        # Calculate standard deviation
        rolling_std = data.rolling(window=period).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (rolling_std * std_dev)
        lower_band = middle_band - (rolling_std * std_dev)
        
        logger.debug(f"Calculated Bollinger Bands with period {period}, std_dev {std_dev}")
        return upper_band, middle_band, lower_band
        
    except Exception as e:
        logger.error(f"Error calculating Bollinger Bands: {str(e)}")
        raise


def calculate_momentum(data: pd.Series, period: int = 10) -> pd.Series:
    """
    Calculate Momentum indicator.
    
    Args:
        data: Price series (usually close prices)
        period: Momentum period (default: 10)
    
    Returns:
        pd.Series: Momentum values
    """
    try:
        if not isinstance(data, pd.Series):
            raise ValueError("Data must be a pandas Series")
        
        if period <= 0:
            raise ValueError("Period must be positive")
        
        # Calculate momentum
        momentum = data - data.shift(period)
        
        logger.debug(f"Calculated Momentum with period {period}")
        return momentum
        
    except Exception as e:
        logger.error(f"Error calculating Momentum: {str(e)}")
        raise


def calculate_supertrend(high: pd.Series, low: pd.Series, close: pd.Series,
                        period: int = 10, multiplier: float = 3.0) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Supertrend indicator.
    
    Args:
        high: High prices series
        low: Low prices series
        close: Close prices series
        period: ATR period (default: 10)
        multiplier: ATR multiplier (default: 3.0)
    
    Returns:
        Tuple[pd.Series, pd.Series]: (Supertrend line, Trend direction)
    """
    try:
        for series, name in [(high, 'high'), (low, 'low'), (close, 'close')]:
            if not isinstance(series, pd.Series):
                raise ValueError(f"{name} must be a pandas Series")
        
        if period <= 0 or multiplier <= 0:
            raise ValueError("Period and multiplier must be positive")
        
        # Calculate ATR
        atr = calculate_atr(high, low, close, period)
        
        # Calculate Basic Upper and Lower Bands
        basic_upper = (high + low) / 2 + (multiplier * atr)
        basic_lower = (high + low) / 2 - (multiplier * atr)
        
        # Initialize Supertrend
        supertrend = pd.Series(index=close.index, dtype=float)
        trend = pd.Series(index=close.index, dtype=int)
        
        # Calculate Supertrend
        for i in range(len(close)):
            if i == 0:
                supertrend.iloc[i] = basic_lower.iloc[i]
                trend.iloc[i] = 1  # Uptrend
            else:
                if close.iloc[i] > supertrend.iloc[i-1]:
                    supertrend.iloc[i] = basic_lower.iloc[i]
                    trend.iloc[i] = 1  # Uptrend
                elif close.iloc[i] < supertrend.iloc[i-1]:
                    supertrend.iloc[i] = basic_upper.iloc[i]
                    trend.iloc[i] = -1  # Downtrend
                else:
                    supertrend.iloc[i] = supertrend.iloc[i-1]
                    trend.iloc[i] = trend.iloc[i-1]
        
        logger.debug(f"Calculated Supertrend with period {period}, multiplier {multiplier}")
        return supertrend, trend
        
    except Exception as e:
        logger.error(f"Error calculating Supertrend: {str(e)}")
        raise


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, 
                 period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    
    Args:
        high: High prices series
        low: Low prices series
        close: Close prices series
        period: ATR period (default: 14)
    
    Returns:
        pd.Series: ATR values
    """
    try:
        for series, name in [(high, 'high'), (low, 'low'), (close, 'close')]:
            if not isinstance(series, pd.Series):
                raise ValueError(f"{name} must be a pandas Series")
        
        if period <= 0:
            raise ValueError("Period must be positive")
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR (EMA of True Range)
        atr = calculate_ema(true_range, period)
        
        logger.debug(f"Calculated ATR with period {period}")
        return atr
        
    except Exception as e:
        logger.error(f"Error calculating ATR: {str(e)}")
        raise


def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                        k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Stochastic Oscillator.
    
    Args:
        high: High prices series
        low: Low prices series
        close: Close prices series
        k_period: %K period (default: 14)
        d_period: %D period (default: 3)
    
    Returns:
        Tuple[pd.Series, pd.Series]: (%K line, %D line)
    """
    try:
        for series, name in [(high, 'high'), (low, 'low'), (close, 'close')]:
            if not isinstance(series, pd.Series):
                raise ValueError(f"{name} must be a pandas Series")
        
        if k_period <= 0 or d_period <= 0:
            raise ValueError("Periods must be positive")
        
        # Calculate highest high and lowest low
        highest_high = high.rolling(window=k_period).max()
        lowest_low = low.rolling(window=k_period).min()
        
        # Calculate %K
        k_line = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        
        # Calculate %D (SMA of %K)
        d_line = calculate_sma(k_line, d_period)
        
        logger.debug(f"Calculated Stochastic with k_period={k_period}, d_period={d_period}")
        return k_line, d_line
        
    except Exception as e:
        logger.error(f"Error calculating Stochastic: {str(e)}")
        raise


def calculate_roc(data: pd.Series, period: int = 10) -> pd.Series:
    """
    Calculate Rate of Change (ROC).
    
    Args:
        data: Price series (usually close prices)
        period: ROC period (default: 10)
    
    Returns:
        pd.Series: ROC values (percentage)
    """
    try:
        if not isinstance(data, pd.Series):
            raise ValueError("Data must be a pandas Series")
        
        if period <= 0:
            raise ValueError("Period must be positive")
        
        # Calculate ROC
        roc = ((data - data.shift(period)) / data.shift(period)) * 100
        
        logger.debug(f"Calculated ROC with period {period}")
        return roc
        
    except Exception as e:
        logger.error(f"Error calculating ROC: {str(e)}")
        raise


def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series, 
                 period: int = 20) -> pd.Series:
    """
    Calculate Commodity Channel Index (CCI).
    
    Args:
        high: High prices series
        low: Low prices series
        close: Close prices series
        period: CCI period (default: 20)
    
    Returns:
        pd.Series: CCI values
    """
    try:
        for series, name in [(high, 'high'), (low, 'low'), (close, 'close')]:
            if not isinstance(series, pd.Series):
                raise ValueError(f"{name} must be a pandas Series")
        
        if period <= 0:
            raise ValueError("Period must be positive")
        
        # Calculate Typical Price
        typical_price = (high + low + close) / 3
        
        # Calculate SMA of Typical Price
        sma_tp = calculate_sma(typical_price, period)
        
        # Calculate Mean Deviation
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - x.mean())), raw=True
        )
        
        # Calculate CCI
        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
        
        logger.debug(f"Calculated CCI with period {period}")
        return cci
        
    except Exception as e:
        logger.error(f"Error calculating CCI: {str(e)}")
        raise


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series,
                 period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Average Directional Index (ADX).
    
    Args:
        high: High prices series
        low: Low prices series
        close: Close prices series
        period: ADX period (default: 14)
    
    Returns:
        Tuple[pd.Series, pd.Series, pd.Series]: (ADX, +DI, -DI)
    """
    try:
        for series, name in [(high, 'high'), (low, 'low'), (close, 'close')]:
            if not isinstance(series, pd.Series):
                raise ValueError(f"{name} must be a pandas Series")
        
        if period <= 0:
            raise ValueError("Period must be positive")
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate Directional Movement
        dm_plus = high - high.shift(1)
        dm_minus = low.shift(1) - low
        
        dm_plus = dm_plus.where((dm_plus > dm_minus) & (dm_plus > 0), 0)
        dm_minus = dm_minus.where((dm_minus > dm_plus) & (dm_minus > 0), 0)
        
        # Calculate smoothed values
        tr_smooth = true_range.rolling(window=period).sum()
        dm_plus_smooth = dm_plus.rolling(window=period).sum()
        dm_minus_smooth = dm_minus.rolling(window=period).sum()
        
        # Calculate DI
        di_plus = 100 * (dm_plus_smooth / tr_smooth)
        di_minus = 100 * (dm_minus_smooth / tr_smooth)
        
        # Calculate DX
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        
        # Calculate ADX
        adx = calculate_ema(dx, period)
        
        logger.debug(f"Calculated ADX with period {period}")
        return adx, di_plus, di_minus
        
    except Exception as e:
        logger.error(f"Error calculating ADX: {str(e)}")
        raise


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Calculate On-Balance Volume (OBV).
    
    Args:
        close: Close prices series
        volume: Volume series
    
    Returns:
        pd.Series: OBV values
    """
    try:
        if not isinstance(close, pd.Series):
            raise ValueError("Close must be a pandas Series")
        if not isinstance(volume, pd.Series):
            raise ValueError("Volume must be a pandas Series")
        
        # Calculate OBV
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        logger.debug("Calculated OBV")
        return obv
        
    except Exception as e:
        logger.error(f"Error calculating OBV: {str(e)}")
        raise


def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series, 
                  volume: pd.Series) -> pd.Series:
    """
    Calculate Volume Weighted Average Price (VWAP).
    
    Args:
        high: High prices series
        low: Low prices series
        close: Close prices series
        volume: Volume series
    
    Returns:
        pd.Series: VWAP values
    """
    try:
        for series, name in [(high, 'high'), (low, 'low'), (close, 'close'), (volume, 'volume')]:
            if not isinstance(series, pd.Series):
                raise ValueError(f"{name} must be a pandas Series")
        
        # Calculate Typical Price
        typical_price = (high + low + close) / 3
        
        # Calculate VWAP
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        
        logger.debug("Calculated VWAP")
        return vwap
        
    except Exception as e:
        logger.error(f"Error calculating VWAP: {str(e)}")
        raise


def calculate_support_resistance(high: pd.Series, low: pd.Series, 
                               window: int = 20) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Support and Resistance levels using local minima and maxima.
    
    Args:
        high: High prices series
        low: Low prices series
        window: Window size for local extrema (default: 20)
    
    Returns:
        Tuple[pd.Series, pd.Series]: (Support levels, Resistance levels)
    """
    try:
        for series, name in [(high, 'high'), (low, 'low')]:
            if not isinstance(series, pd.Series):
                raise ValueError(f"{name} must be a pandas Series")
        
        if window <= 0:
            raise ValueError("Window must be positive")
        
        # Calculate local minima (support)
        support = low.rolling(window=window, center=True).min()
        
        # Calculate local maxima (resistance)
        resistance = high.rolling(window=window, center=True).max()
        
        logger.debug(f"Calculated Support/Resistance with window {window}")
        return support, resistance
        
    except Exception as e:
        logger.error(f"Error calculating Support/Resistance: {str(e)}")
        raise 

class TechnicalAnalysis:
    """
    Main technical analysis class providing comprehensive financial indicators.
    
    This class implements various technical analysis methods following
    the modular and maintainable approach with proper error handling.
    """
    
    def __init__(self):
        """Initialize the TechnicalAnalysis class."""
        self._validate_data = True
        self._min_data_points = 30
        
    def set_validation(self, validate: bool = True, min_points: int = 30):
        """Configure data validation settings."""
        self._validate_data = validate
        self._min_data_points = min_points
    
    def _validate_ohlcv_data(self, data: pd.DataFrame) -> bool:
        """Validate OHLCV data structure."""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame")
        
        required_columns = ['open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        if len(data) < self._min_data_points:
            raise ValueError(f"Data must have at least {self._min_data_points} data points")
        
        return True
    
    def _validate_series(self, series: pd.Series, name: str = "series") -> bool:
        """Validate pandas series data."""
        if not isinstance(series, pd.Series):
            raise ValueError(f"{name} must be a pandas Series")
        
        if series.empty:
            raise ValueError(f"{name} cannot be empty")
        
        if series.isnull().all():
            raise ValueError(f"{name} cannot contain all null values")
        
        return True
    
    def calculate_all_indicators(self, data: pd.DataFrame, 
                               indicators: List[str] = None) -> Dict[str, Any]:
        """
        Calculate all available technical indicators for the given data.
        
        Args:
            data: OHLCV DataFrame
            indicators: List of indicators to calculate (if None, calculates all)
        
        Returns:
            Dict containing all calculated indicators
        """
        if indicators is None:
            indicators = [
                'ema', 'sma', 'wma', 'rsi', 'macd', 'bollinger_bands',
                'momentum', 'supertrend', 'atr', 'stochastic', 'roc',
                'cci', 'adx', 'obv', 'vwap', 'support_resistance'
            ]
        
        self._validate_ohlcv_data(data)
        
        results = {}
        
        # Extract price series
        close = data['close']
        high = data['high']
        low = data['low']
        open_price = data['open']
        volume = data.get('volume', pd.Series(index=data.index, dtype=float))
        
        # Calculate indicators based on request
        for indicator in indicators:
            try:
                if indicator == 'ema':
                    results['ema_12'] = calculate_ema(close, 12)
                    results['ema_26'] = calculate_ema(close, 26)
                    results['ema_50'] = calculate_ema(close, 50)
                    results['ema_200'] = calculate_ema(close, 200)
                
                elif indicator == 'sma':
                    results['sma_20'] = calculate_sma(close, 20)
                    results['sma_50'] = calculate_sma(close, 50)
                    results['sma_200'] = calculate_sma(close, 200)
                
                elif indicator == 'wma':
                    results['wma_20'] = calculate_wma(close, 20)
                
                elif indicator == 'rsi':
                    results['rsi'] = calculate_rsi(close, 14)
                
                elif indicator == 'macd':
                    macd_line, signal_line, histogram = calculate_macd(close)
                    results['macd_line'] = macd_line
                    results['macd_signal'] = signal_line
                    results['macd_histogram'] = histogram
                
                elif indicator == 'bollinger_bands':
                    upper, middle, lower = calculate_bollinger_bands(close)
                    results['bb_upper'] = upper
                    results['bb_middle'] = middle
                    results['bb_lower'] = lower
                
                elif indicator == 'momentum':
                    results['momentum'] = calculate_momentum(close, 10)
                
                elif indicator == 'supertrend':
                    supertrend, trend = calculate_supertrend(high, low, close)
                    results['supertrend'] = supertrend
                    results['supertrend_trend'] = trend
                
                elif indicator == 'atr':
                    results['atr'] = calculate_atr(high, low, close)
                
                elif indicator == 'stochastic':
                    k_line, d_line = calculate_stochastic(high, low, close)
                    results['stoch_k'] = k_line
                    results['stoch_d'] = d_line
                
                elif indicator == 'roc':
                    results['roc'] = calculate_roc(close, 10)
                
                elif indicator == 'cci':
                    results['cci'] = calculate_cci(high, low, close)
                
                elif indicator == 'adx':
                    adx, di_plus, di_minus = calculate_adx(high, low, close)
                    results['adx'] = adx
                    results['di_plus'] = di_plus
                    results['di_minus'] = di_minus
                
                elif indicator == 'obv':
                    results['obv'] = calculate_obv(close, volume)
                
                elif indicator == 'vwap':
                    results['vwap'] = calculate_vwap(high, low, close, volume)
                
                elif indicator == 'support_resistance':
                    support, resistance = calculate_support_resistance(high, low)
                    results['support'] = support
                    results['resistance'] = resistance
                
                logger.info(f"Successfully calculated {indicator}")
                
            except Exception as e:
                logger.error(f"Error calculating {indicator}: {str(e)}")
                results[f'{indicator}_error'] = str(e)
        
        return results
    
    def get_trading_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on technical indicators.
        
        Args:
            data: OHLCV DataFrame
        
        Returns:
            Dict containing trading signals and analysis
        """
        indicators = self.calculate_all_indicators(data)
        signals = {}
        
        close = data['close']
        current_price = close.iloc[-1]
        
        # RSI signals
        if 'rsi' in indicators:
            rsi = indicators['rsi'].iloc[-1]
            if rsi > 70:
                signals['rsi_signal'] = 'SELL'
            elif rsi < 30:
                signals['rsi_signal'] = 'BUY'
            else:
                signals['rsi_signal'] = 'NEUTRAL'
        
        # MACD signals
        if 'macd_line' in indicators and 'macd_signal' in indicators:
            macd_line = indicators['macd_line'].iloc[-1]
            macd_signal = indicators['macd_signal'].iloc[-1]
            if macd_line > macd_signal:
                signals['macd_signal'] = 'BUY'
            else:
                signals['macd_signal'] = 'SELL'
        
        # Bollinger Bands signals
        if 'bb_upper' in indicators and 'bb_lower' in indicators:
            bb_upper = indicators['bb_upper'].iloc[-1]
            bb_lower = indicators['bb_lower'].iloc[-1]
            if current_price > bb_upper:
                signals['bb_signal'] = 'SELL'
            elif current_price < bb_lower:
                signals['bb_signal'] = 'BUY'
            else:
                signals['bb_signal'] = 'NEUTRAL'
        
        # Supertrend signals
        if 'supertrend_trend' in indicators:
            trend = indicators['supertrend_trend'].iloc[-1]
            signals['supertrend_signal'] = 'BUY' if trend == 1 else 'SELL'
        
        # Moving Average signals
        if 'ema_50' in indicators and 'ema_200' in indicators:
            ema_50 = indicators['ema_50'].iloc[-1]
            ema_200 = indicators['ema_200'].iloc[-1]
            if ema_50 > ema_200:
                signals['ma_signal'] = 'BUY'
            else:
                signals['ma_signal'] = 'SELL'
        
        return signals 