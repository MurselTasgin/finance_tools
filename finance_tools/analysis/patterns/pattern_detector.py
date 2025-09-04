# finance_tools/analysis/patterns/pattern_detector.py
"""
Pattern detector for identifying sophisticated price patterns and breakouts.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from scipy.signal import find_peaks
from scipy.optimize import curve_fit

from .pattern_types import (
    Pattern, PatternResult,
    PatternType, PatternDirection, PatternReliability
)
from .pattern_types import (
    ChartPattern as ChartPatternEnum, CandlestickPattern as CandlestickPatternEnum,
    BreakoutPattern as BreakoutPatternEnum, DivergencePattern as DivergencePatternEnum,
    HarmonicPattern as HarmonicPatternEnum,
    ChartPatternData, CandlestickPatternData, BreakoutPatternData, 
    DivergencePatternData, HarmonicPatternData
)
from ..analysis import (
    calculate_ema, calculate_sma, calculate_rsi, calculate_macd,
    calculate_bollinger_bands, calculate_stochastic, calculate_atr
)

logger = logging.getLogger(__name__)


class PatternDetector:
    """
    Main pattern detector for identifying sophisticated price patterns.
    """
    
    def __init__(self):
        """Initialize the pattern detector."""
        self.patterns = []
    
    def detect_all_patterns(self, data: pd.DataFrame) -> PatternResult:
        """
        Detect all available patterns in the given data.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            PatternResult: Container with all patterns and summary
        """
        patterns = []
        
        # Detect chart patterns
        chart_patterns = self._detect_chart_patterns(data)
        patterns.extend(chart_patterns)
        
        # Detect candlestick patterns
        candlestick_patterns = self._detect_candlestick_patterns(data)
        patterns.extend(candlestick_patterns)
        
        # Detect breakout patterns
        breakout_patterns = self._detect_breakout_patterns(data)
        patterns.extend(breakout_patterns)
        
        # Detect divergence patterns
        divergence_patterns = self._detect_divergence_patterns(data)
        patterns.extend(divergence_patterns)
        
        # Detect harmonic patterns
        harmonic_patterns = self._detect_harmonic_patterns(data)
        patterns.extend(harmonic_patterns)
        
        # Create summary
        summary = self._create_pattern_summary(patterns)
        
        return PatternResult(patterns=patterns, summary=summary)
    
    def _detect_chart_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect chart patterns like Head & Shoulders, Double Tops, etc."""
        patterns = []
        close_prices = data['close']
        high_prices = data['high']
        low_prices = data['low']
        
        # Find peaks and troughs
        peaks, _ = find_peaks(high_prices.values, distance=5)
        troughs, _ = find_peaks(-low_prices.values, distance=5)
        
        # Head and Shoulders pattern
        head_shoulders = self._detect_head_and_shoulders(data, peaks, troughs)
        patterns.extend(head_shoulders)
        
        # Double Top/Bottom patterns
        double_patterns = self._detect_double_patterns(data, peaks, troughs)
        patterns.extend(double_patterns)
        
        # Triangle patterns
        triangle_patterns = self._detect_triangle_patterns(data)
        patterns.extend(triangle_patterns)
        
        # Rectangle patterns
        rectangle_patterns = self._detect_rectangle_patterns(data)
        patterns.extend(rectangle_patterns)
        
        return patterns
    
    def _detect_head_and_shoulders(self, data: pd.DataFrame, peaks: np.ndarray, troughs: np.ndarray) -> List[Pattern]:
        """Detect Head and Shoulders pattern."""
        patterns = []
        close_prices = data['close']
        
        if len(peaks) < 3:
            return patterns
        
        for i in range(len(peaks) - 2):
            left_shoulder = peaks[i]
            head = peaks[i + 1]
            right_shoulder = peaks[i + 2]
            
            # Check if peaks are reasonably spaced
            if right_shoulder - left_shoulder > 50:  # Too far apart
                continue
            
            left_price = close_prices.iloc[left_shoulder]
            head_price = close_prices.iloc[head]
            right_price = close_prices.iloc[right_shoulder]
            
            # Head should be higher than shoulders
            if head_price > left_price and head_price > right_price:
                # Shoulders should be roughly at same level
                shoulder_diff = abs(left_price - right_price) / left_price
                if shoulder_diff < 0.05:  # Within 5%
                    # Convert index to datetime if it's a string
                    start_date = data.index[left_shoulder]
                    end_date = data.index[right_shoulder]
                    
                    if isinstance(start_date, str):
                        start_date = pd.to_datetime(start_date)
                    if isinstance(end_date, str):
                        end_date = pd.to_datetime(end_date)
                    
                    pattern = ChartPatternData(
                        pattern_type=PatternType.CHART_PATTERN,
                        pattern_name="Head and Shoulders",
                        direction=PatternDirection.BEARISH,
                        reliability=PatternReliability.HIGH,
                        start_date=start_date,
                        end_date=end_date,
                        breakout_price=min(left_price, right_price),
                        target_price=min(left_price, right_price) - (head_price - min(left_price, right_price)),
                        stop_loss=head_price,
                        confidence=0.8,
                        description="Bearish reversal pattern with three peaks",
                        chart_pattern_type=ChartPatternEnum.HEAD_AND_SHOULDERS,
                        key_levels=[
                            (data.index[left_shoulder], left_price),
                            (data.index[head], head_price),
                            (data.index[right_shoulder], right_price)
                        ]
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_double_patterns(self, data: pd.DataFrame, peaks: np.ndarray, troughs: np.ndarray) -> List[Pattern]:
        """Detect Double Top and Double Bottom patterns."""
        patterns = []
        close_prices = data['close']
        
        # Double Top
        for i in range(len(peaks) - 1):
            peak1 = peaks[i]
            peak2 = peaks[i + 1]
            
            if peak2 - peak1 > 30:  # Too far apart
                continue
            
            price1 = close_prices.iloc[peak1]
            price2 = close_prices.iloc[peak2]
            
            # Peaks should be roughly at same level
            price_diff = abs(price1 - price2) / price1
            if price_diff < 0.03:  # Within 3%
                # Convert index to datetime if it's a string
                start_date = data.index[peak1]
                end_date = data.index[peak2]
                
                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date)
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date)
                
                pattern = ChartPatternData(
                    pattern_type=PatternType.CHART_PATTERN,
                    pattern_name="Double Top",
                    direction=PatternDirection.BEARISH,
                    reliability=PatternReliability.MEDIUM,
                    start_date=start_date,
                    end_date=end_date,
                    breakout_price=min(price1, price2),
                    target_price=min(price1, price2) - (max(price1, price2) - min(price1, price2)),
                    stop_loss=max(price1, price2),
                    confidence=0.7,
                    description="Bearish reversal pattern with two peaks",
                    chart_pattern_type=ChartPatternEnum.DOUBLE_TOP,
                    key_levels=[
                        (data.index[peak1], price1),
                        (data.index[peak2], price2)
                    ]
                )
                patterns.append(pattern)
        
        # Double Bottom
        for i in range(len(troughs) - 1):
            trough1 = troughs[i]
            trough2 = troughs[i + 1]
            
            if trough2 - trough1 > 30:  # Too far apart
                continue
            
            price1 = close_prices.iloc[trough1]
            price2 = close_prices.iloc[trough2]
            
            # Troughs should be roughly at same level
            price_diff = abs(price1 - price2) / price1
            if price_diff < 0.03:  # Within 3%
                # Convert index to datetime if it's a string
                start_date = data.index[trough1]
                end_date = data.index[trough2]
                
                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date)
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date)
                
                pattern = ChartPatternData(
                    pattern_type=PatternType.CHART_PATTERN,
                    pattern_name="Double Bottom",
                    direction=PatternDirection.BULLISH,
                    reliability=PatternReliability.MEDIUM,
                    start_date=start_date,
                    end_date=end_date,
                    breakout_price=max(price1, price2),
                    target_price=max(price1, price2) + (max(price1, price2) - min(price1, price2)),
                    stop_loss=min(price1, price2),
                    confidence=0.7,
                    description="Bullish reversal pattern with two troughs",
                    chart_pattern_type=ChartPatternEnum.DOUBLE_BOTTOM,
                    key_levels=[
                        (data.index[trough1], price1),
                        (data.index[trough2], price2)
                    ]
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_triangle_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect triangle patterns (ascending, descending, symmetrical)."""
        patterns = []
        close_prices = data['close']
        high_prices = data['high']
        low_prices = data['low']
        
        # Look for triangle patterns in recent data (last 50 periods)
        recent_data = data.tail(50)
        if len(recent_data) < 20:
            return patterns
        
        # Find highs and lows in recent data
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        
        # Fit trend lines
        try:
            # High trend line
            high_indices = np.arange(len(highs))
            high_slope, high_intercept = np.polyfit(high_indices, highs, 1)
            
            # Low trend line
            low_indices = np.arange(len(lows))
            low_slope, low_intercept = np.polyfit(low_indices, lows, 1)
            
            # Determine triangle type
            if high_slope < -0.001 and low_slope > 0.001:
                # Descending triangle (bearish)
                # Convert index to datetime if it's a string
                start_date = recent_data.index[0]
                end_date = recent_data.index[-1]
                
                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date)
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date)
                
                pattern = ChartPatternData(
                    pattern_type=PatternType.CHART_PATTERN,
                    pattern_name="Descending Triangle",
                    direction=PatternDirection.BEARISH,
                    reliability=PatternReliability.MEDIUM,
                    start_date=start_date,
                    end_date=end_date,
                    breakout_price=low_intercept + low_slope * len(lows),
                    target_price=low_intercept + low_slope * len(lows) - (high_intercept - low_intercept),
                    stop_loss=high_intercept + high_slope * len(highs),
                    confidence=0.6,
                    description="Bearish continuation pattern with descending highs and flat lows",
                    chart_pattern_type=ChartPatternEnum.DESCENDING_TRIANGLE
                )
                patterns.append(pattern)
            
            elif high_slope > 0.001 and low_slope < -0.001:
                # Ascending triangle (bullish)
                # Convert index to datetime if it's a string
                start_date = recent_data.index[0]
                end_date = recent_data.index[-1]
                
                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date)
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date)
                
                pattern = ChartPatternData(
                    pattern_type=PatternType.CHART_PATTERN,
                    pattern_name="Ascending Triangle",
                    direction=PatternDirection.BULLISH,
                    reliability=PatternReliability.MEDIUM,
                    start_date=start_date,
                    end_date=end_date,
                    breakout_price=high_intercept + high_slope * len(highs),
                    target_price=high_intercept + high_slope * len(highs) + (high_intercept - low_intercept),
                    stop_loss=low_intercept + low_slope * len(lows),
                    confidence=0.6,
                    description="Bullish continuation pattern with ascending lows and flat highs",
                    chart_pattern_type=ChartPatternEnum.ASCENDING_TRIANGLE
                )
                patterns.append(pattern)
            
            elif abs(high_slope - low_slope) < 0.001:
                # Symmetrical triangle
                # Convert index to datetime if it's a string
                start_date = recent_data.index[0]
                end_date = recent_data.index[-1]
                
                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date)
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date)
                
                pattern = Pattern(
                    pattern_type=PatternType.CHART_PATTERN,
                    pattern_name="Symmetrical Triangle",
                    direction=PatternDirection.NEUTRAL,
                    reliability=PatternReliability.LOW,
                    start_date=start_date,
                    end_date=end_date,
                    breakout_price=None,
                    target_price=None,
                    stop_loss=None,
                    confidence=0.5,
                    description="Neutral continuation pattern with converging trend lines"
                )
                pattern.chart_pattern_type = ChartPatternEnum.SYMMETRICAL_TRIANGLE
                patterns.append(pattern)
        
        except:
            pass
        
        return patterns
    
    def _detect_rectangle_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect rectangle patterns."""
        patterns = []
        close_prices = data['close']
        
        # Look for rectangle in recent data
        recent_data = data.tail(30)
        if len(recent_data) < 15:
            return patterns
        
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        
        # Check if highs and lows are relatively flat
        high_std = np.std(highs)
        low_std = np.std(lows)
        price_range = np.mean(highs) - np.mean(lows)
        
        if high_std / price_range < 0.1 and low_std / price_range < 0.1:
            # Rectangle pattern detected
            resistance = np.mean(highs)
            support = np.mean(lows)
            
            # Convert index to datetime if it's a string
            start_date = recent_data.index[0]
            end_date = recent_data.index[-1]
            
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            
            pattern = Pattern(
                pattern_type=PatternType.CHART_PATTERN,
                pattern_name="Rectangle",
                direction=PatternDirection.NEUTRAL,
                reliability=PatternReliability.MEDIUM,
                start_date=start_date,
                end_date=end_date,
                breakout_price=resistance,
                target_price=resistance + price_range,
                stop_loss=support,
                confidence=0.6,
                description="Neutral continuation pattern with horizontal support and resistance"
            )
            pattern.chart_pattern_type = ChartPatternEnum.RECTANGLE
            patterns.append(pattern)
        
        return patterns
    
    def _detect_candlestick_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect candlestick patterns."""
        patterns = []
        
        for i in range(len(data)):
            if i < 2:  # Need at least 3 candles for patterns
                continue
            
            current = data.iloc[i]
            prev = data.iloc[i-1]
            prev2 = data.iloc[i-2]
            
            # Doji pattern
            if self._is_doji(current):
                # Convert index to datetime if it's a string
                start_date = data.index[i]
                end_date = data.index[i]
                
                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date)
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date)
                
                pattern = CandlestickPatternData(
                    pattern_type=PatternType.CANDLESTICK_PATTERN,
                    pattern_name="Doji",
                    direction=PatternDirection.NEUTRAL,
                    reliability=PatternReliability.MEDIUM,
                    start_date=start_date,
                    end_date=end_date,
                    confidence=0.6,
                    description="Indecision pattern with small body",
                    candlestick_pattern_type=CandlestickPatternEnum.DOJI,
                    body_size=abs(current['close'] - current['open']),
                    upper_shadow=current['high'] - max(current['open'], current['close']),
                    lower_shadow=min(current['open'], current['close']) - current['low'],
                    color="neutral"
                )
                patterns.append(pattern)
            
            # Hammer pattern
            elif self._is_hammer(current):
                # Convert index to datetime if it's a string
                start_date = data.index[i]
                end_date = data.index[i]
                
                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date)
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date)
                
                pattern = CandlestickPatternData(
                    pattern_type=PatternType.CANDLESTICK_PATTERN,
                    pattern_name="Hammer",
                    direction=PatternDirection.BULLISH,
                    reliability=PatternReliability.MEDIUM,
                    start_date=start_date,
                    end_date=end_date,
                    confidence=0.7,
                    description="Bullish reversal pattern with long lower shadow",
                    candlestick_pattern_type=CandlestickPatternEnum.HAMMER,
                    body_size=abs(current['close'] - current['open']),
                    upper_shadow=current['high'] - max(current['open'], current['close']),
                    lower_shadow=min(current['open'], current['close']) - current['low'],
                    color="bullish" if current['close'] > current['open'] else "bearish"
                )
                patterns.append(pattern)
            
            # Engulfing patterns
            elif self._is_bullish_engulfing(current, prev):
                # Convert index to datetime if it's a string
                start_date = data.index[i-1]
                end_date = data.index[i]
                
                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date)
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date)
                
                pattern = CandlestickPatternData(
                    pattern_type=PatternType.CANDLESTICK_PATTERN,
                    pattern_name="Bullish Engulfing",
                    direction=PatternDirection.BULLISH,
                    reliability=PatternReliability.HIGH,
                    start_date=start_date,
                    end_date=end_date,
                    confidence=0.8,
                    description="Bullish reversal pattern with current candle engulfing previous",
                    candlestick_pattern_type=CandlestickPatternEnum.BULLISH_ENGULFING,
                    body_size=abs(current['close'] - current['open']),
                    upper_shadow=current['high'] - max(current['open'], current['close']),
                    lower_shadow=min(current['open'], current['close']) - current['low'],
                    color="bullish"
                )
                patterns.append(pattern)
            
            elif self._is_bearish_engulfing(current, prev):
                # Convert index to datetime if it's a string
                start_date = data.index[i-1]
                end_date = data.index[i]
                
                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date)
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date)
                
                pattern = CandlestickPatternData(
                    pattern_type=PatternType.CANDLESTICK_PATTERN,
                    pattern_name="Bearish Engulfing",
                    direction=PatternDirection.BEARISH,
                    reliability=PatternReliability.HIGH,
                    start_date=start_date,
                    end_date=end_date,
                    confidence=0.8,
                    description="Bearish reversal pattern with current candle engulfing previous",
                    candlestick_pattern_type=CandlestickPatternEnum.BEARISH_ENGULFING,
                    body_size=abs(current['close'] - current['open']),
                    upper_shadow=current['high'] - max(current['open'], current['close']),
                    lower_shadow=min(current['open'], current['close']) - current['low'],
                    color="bearish"
                )
                patterns.append(pattern)
        
        return patterns
    
    def _is_doji(self, candle: pd.Series) -> bool:
        """Check if candle is a doji pattern."""
        body_size = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        return body_size / total_range < 0.1 if total_range > 0 else False
    
    def _is_hammer(self, candle: pd.Series) -> bool:
        """Check if candle is a hammer pattern."""
        body_size = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        return (lower_shadow > 2 * body_size and 
                upper_shadow < body_size and
                body_size > 0)
    
    def _is_bullish_engulfing(self, current: pd.Series, prev: pd.Series) -> bool:
        """Check if current and previous candles form bullish engulfing."""
        return (prev['close'] < prev['open'] and  # Previous bearish
                current['close'] > current['open'] and  # Current bullish
                current['open'] < prev['close'] and  # Current opens below previous close
                current['close'] > prev['open'])  # Current closes above previous open
    
    def _is_bearish_engulfing(self, current: pd.Series, prev: pd.Series) -> bool:
        """Check if current and previous candles form bearish engulfing."""
        return (prev['close'] > prev['open'] and  # Previous bullish
                current['close'] < current['open'] and  # Current bearish
                current['open'] > prev['close'] and  # Current opens above previous close
                current['close'] < prev['open'])  # Current closes below previous open
    
    def _detect_breakout_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect breakout patterns."""
        patterns = []
        close_prices = data['close']
        volume = data.get('volume', pd.Series(index=data.index, dtype=float))
        
        # Resistance breakout
        recent_highs = close_prices.rolling(window=20).max()
        current_price = close_prices.iloc[-1]
        resistance_level = recent_highs.iloc[-2]  # Previous high
        
        if current_price > resistance_level * 1.02:  # 2% breakout
            volume_ratio = volume.iloc[-1] / volume.rolling(window=20).mean().iloc[-1] if not volume.empty else 1
            
            # Convert index to datetime if it's a string
            start_date = data.index[-20]
            end_date = data.index[-1]
            
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            
            pattern = BreakoutPatternData(
                pattern_type=PatternType.BREAKOUT_PATTERN,
                pattern_name="Resistance Breakout",
                direction=PatternDirection.BULLISH,
                reliability=PatternReliability.HIGH,
                start_date=start_date,
                end_date=end_date,
                breakout_price=resistance_level,
                target_price=resistance_level + (current_price - resistance_level),
                stop_loss=resistance_level * 0.98,
                confidence=0.8 if volume_ratio > 1.5 else 0.6,
                description="Bullish breakout above resistance level",
                breakout_pattern_type=BreakoutPatternEnum.RESISTANCE_BREAKOUT,
                breakout_volume=volume.iloc[-1] if not volume.empty else None,
                breakout_strength=current_price / resistance_level - 1,
                consolidation_period=20
            )
            patterns.append(pattern)
        
        # Support breakdown
        recent_lows = close_prices.rolling(window=20).min()
        support_level = recent_lows.iloc[-2]  # Previous low
        
        if current_price < support_level * 0.98:  # 2% breakdown
            volume_ratio = volume.iloc[-1] / volume.rolling(window=20).mean().iloc[-1] if not volume.empty else 1
            
            # Convert index to datetime if it's a string
            start_date = data.index[-20]
            end_date = data.index[-1]
            
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            
            pattern = BreakoutPatternData(
                pattern_type=PatternType.BREAKOUT_PATTERN,
                pattern_name="Support Breakdown",
                direction=PatternDirection.BEARISH,
                reliability=PatternReliability.HIGH,
                start_date=start_date,
                end_date=end_date,
                breakout_price=support_level,
                target_price=support_level - (support_level - current_price),
                stop_loss=support_level * 1.02,
                confidence=0.8 if volume_ratio > 1.5 else 0.6,
                description="Bearish breakdown below support level",
                breakout_pattern_type=BreakoutPatternEnum.SUPPORT_BREAKDOWN,
                breakout_volume=volume.iloc[-1] if not volume.empty else None,
                breakout_strength=support_level / current_price - 1,
                consolidation_period=20
            )
            patterns.append(pattern)
        
        return patterns
    
    def _detect_divergence_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect divergence patterns between price and indicators."""
        patterns = []
        close_prices = data['close']
        
        # RSI divergence
        rsi = calculate_rsi(close_prices, 14)
        rsi_divergence = self._detect_rsi_divergence(close_prices, rsi)
        patterns.extend(rsi_divergence)
        
        # MACD divergence
        macd_line, signal_line, histogram = calculate_macd(close_prices)
        macd_divergence = self._detect_macd_divergence(close_prices, macd_line)
        patterns.extend(macd_divergence)
        
        return patterns
    
    def _detect_rsi_divergence(self, prices: pd.Series, rsi: pd.Series) -> List[Pattern]:
        """Detect RSI divergence patterns."""
        patterns = []
        
        # Find peaks and troughs in price and RSI
        price_peaks, _ = find_peaks(prices.values, distance=10)
        price_troughs, _ = find_peaks(-prices.values, distance=10)
        rsi_peaks, _ = find_peaks(rsi.values, distance=10)
        rsi_troughs, _ = find_peaks(-rsi.values, distance=10)
        
        # Bearish divergence: Price makes higher highs, RSI makes lower highs
        if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
            if (prices.iloc[price_peaks[-1]] > prices.iloc[price_peaks[-2]] and
                rsi.iloc[rsi_peaks[-1]] < rsi.iloc[rsi_peaks[-2]]):
                
                # Convert index to datetime if it's a string
                start_date = prices.index[price_peaks[-2]]
                end_date = prices.index[price_peaks[-1]]
                
                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date)
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date)
                
                pattern = DivergencePatternData(
                    pattern_type=PatternType.DIVERGENCE_PATTERN,
                    pattern_name="Bearish RSI Divergence",
                    direction=PatternDirection.BEARISH,
                    reliability=PatternReliability.HIGH,
                    start_date=start_date,
                    end_date=end_date,
                    confidence=0.8,
                    description="Price making higher highs while RSI making lower highs",
                    divergence_pattern_type=DivergencePatternEnum.BEARISH_DIVERGENCE,
                    indicator_name="RSI",
                    price_highs=[prices.iloc[p] for p in price_peaks[-2:]],
                    indicator_highs=[rsi.iloc[p] for p in rsi_peaks[-2:]]
                )
                patterns.append(pattern)
        
        # Bullish divergence: Price makes lower lows, RSI makes higher lows
        if len(price_troughs) >= 2 and len(rsi_troughs) >= 2:
            if (prices.iloc[price_troughs[-1]] < prices.iloc[price_troughs[-2]] and
                rsi.iloc[rsi_troughs[-1]] > rsi.iloc[rsi_troughs[-2]]):
                
                pattern = DivergencePatternData(
                    pattern_type=PatternType.DIVERGENCE_PATTERN,
                    pattern_name="Bullish RSI Divergence",
                    direction=PatternDirection.BULLISH,
                    reliability=PatternReliability.HIGH,
                    start_date=prices.index[price_troughs[-2]],
                    end_date=prices.index[price_troughs[-1]],
                    confidence=0.8,
                    description="Price making lower lows while RSI making higher lows",
                    divergence_pattern_type=DivergencePatternEnum.BULLISH_DIVERGENCE,
                    indicator_name="RSI",
                    price_lows=[prices.iloc[p] for p in price_troughs[-2:]],
                    indicator_lows=[rsi.iloc[p] for p in rsi_troughs[-2:]]
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_macd_divergence(self, prices: pd.Series, macd: pd.Series) -> List[Pattern]:
        """Detect MACD divergence patterns."""
        patterns = []
        
        # Find peaks and troughs in price and MACD
        price_peaks, _ = find_peaks(prices.values, distance=10)
        price_troughs, _ = find_peaks(-prices.values, distance=10)
        macd_peaks, _ = find_peaks(macd.values, distance=10)
        macd_troughs, _ = find_peaks(-macd.values, distance=10)
        
        # Bearish divergence: Price makes higher highs, MACD makes lower highs
        if len(price_peaks) >= 2 and len(macd_peaks) >= 2:
            if (prices.iloc[price_peaks[-1]] > prices.iloc[price_peaks[-2]] and
                macd.iloc[macd_peaks[-1]] < macd.iloc[macd_peaks[-2]]):
                
                pattern = DivergencePatternData(
                    pattern_type=PatternType.DIVERGENCE_PATTERN,
                    pattern_name="Bearish MACD Divergence",
                    direction=PatternDirection.BEARISH,
                    reliability=PatternReliability.HIGH,
                    start_date=prices.index[price_peaks[-2]],
                    end_date=prices.index[price_peaks[-1]],
                    confidence=0.8,
                    description="Price making higher highs while MACD making lower highs",
                    divergence_pattern_type=DivergencePatternEnum.BEARISH_DIVERGENCE,
                    indicator_name="MACD",
                    price_highs=[prices.iloc[p] for p in price_peaks[-2:]],
                    indicator_highs=[macd.iloc[p] for p in macd_peaks[-2:]]
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_harmonic_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect harmonic patterns (Gartley, Butterfly, etc.)."""
        patterns = []
        # This is a simplified implementation
        # Full harmonic pattern detection requires complex Fibonacci calculations
        
        return patterns
    
    def _create_pattern_summary(self, patterns: List[Pattern]) -> Dict[str, Any]:
        """Create a summary of all patterns."""
        if not patterns:
            return {'total_patterns': 0, 'bullish_patterns': 0, 'bearish_patterns': 0}
        
        bullish_patterns = [p for p in patterns if p.direction == PatternDirection.BULLISH]
        bearish_patterns = [p for p in patterns if p.direction == PatternDirection.BEARISH]
        
        # Group by pattern type
        pattern_types = {}
        for pattern in patterns:
            pattern_type = pattern.pattern_type.value
            if pattern_type not in pattern_types:
                pattern_types[pattern_type] = 0
            pattern_types[pattern_type] += 1
        
        # Calculate average confidence
        avg_confidence = sum(p.confidence for p in patterns) / len(patterns) if patterns else 0
        
        return {
            'total_patterns': len(patterns),
            'bullish_patterns': len(bullish_patterns),
            'bearish_patterns': len(bearish_patterns),
            'pattern_types': pattern_types,
            'average_confidence': avg_confidence,
            'high_reliability_patterns': len([p for p in patterns if p.reliability in [PatternReliability.HIGH, PatternReliability.VERY_HIGH]])
        }


# Convenience functions for direct pattern detection
def detect_chart_patterns(data: pd.DataFrame) -> List[Pattern]:
    """Detect chart patterns."""
    detector = PatternDetector()
    return detector._detect_chart_patterns(data)


def detect_candlestick_patterns(data: pd.DataFrame) -> List[Pattern]:
    """Detect candlestick patterns."""
    detector = PatternDetector()
    return detector._detect_candlestick_patterns(data)


def detect_breakout_patterns(data: pd.DataFrame) -> List[Pattern]:
    """Detect breakout patterns."""
    detector = PatternDetector()
    return detector._detect_breakout_patterns(data)


def detect_divergence_patterns(data: pd.DataFrame) -> List[Pattern]:
    """Detect divergence patterns."""
    detector = PatternDetector()
    return detector._detect_divergence_patterns(data)


def detect_harmonic_patterns(data: pd.DataFrame) -> List[Pattern]:
    """Detect harmonic patterns."""
    detector = PatternDetector()
    return detector._detect_harmonic_patterns(data) 