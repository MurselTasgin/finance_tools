# finance_tools/analysis/signals/signal_calculator.py
"""
Signal calculator for detecting trading signals and crossovers.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from .signal_types import (
    Signal, SignalResult, CrossoverSignal,
    SignalType, SignalStrength, SignalDirection, CrossoverType
)
from ..analysis import (
    calculate_ema, calculate_sma, calculate_rsi, calculate_macd,
    calculate_bollinger_bands, calculate_stochastic, calculate_atr
)

logger = logging.getLogger(__name__)


class SignalCalculator:
    """
    Main signal calculator for detecting trading signals and crossovers.
    """
    
    def __init__(self):
        """Initialize the signal calculator."""
        self.signals = []
        self.crossover_signals = []
    
    def calculate_all_signals(self, data: pd.DataFrame) -> SignalResult:
        """
        Calculate all available signals for the given data.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            SignalResult: Container with all signals and summary
        """
        signals = []
        
        # Calculate technical indicators
        close_prices = data['close']
        high_prices = data['high']
        low_prices = data['low']
        volume = data.get('volume', pd.Series(index=data.index, dtype=float))
        
        # EMA crossover signals
        ema_signals = self._calculate_ema_crossover_signals(data)
        signals.extend(ema_signals)
        
        # Price vs MA signals
        price_ma_signals = self._calculate_price_ma_signals(data)
        signals.extend(price_ma_signals)
        
        # RSI signals
        rsi_signals = self._calculate_rsi_signals(data)
        signals.extend(rsi_signals)
        
        # MACD signals
        macd_signals = self._calculate_macd_signals(data)
        signals.extend(macd_signals)
        
        # Bollinger Bands signals
        bb_signals = self._calculate_bollinger_bands_signals(data)
        signals.extend(bb_signals)
        
        # Volume signals
        volume_signals = self._calculate_volume_signals(data)
        signals.extend(volume_signals)
        
        # Support/Resistance signals
        sr_signals = self._calculate_support_resistance_signals(data)
        signals.extend(sr_signals)
        
        # Create summary
        summary = self._create_signal_summary(signals)
        
        return SignalResult(signals=signals, summary=summary)
    
    def _calculate_ema_crossover_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Calculate EMA crossover signals."""
        signals = []
        close_prices = data['close']
        
        # Calculate EMAs
        ema_20 = calculate_ema(close_prices, 20)
        ema_50 = calculate_ema(close_prices, 50)
        ema_200 = calculate_ema(close_prices, 200)
        
        # Check for crossovers
        for i in range(1, len(data)):
            current_price = close_prices.iloc[i]
            timestamp = data.index[i]
            
            # EMA 20 vs EMA 50 crossover
            if ema_20.iloc[i] > ema_50.iloc[i] and ema_20.iloc[i-1] <= ema_50.iloc[i-1]:
                signal = Signal(
                    signal_type=SignalType.EMA_CROSSOVER,
                    direction=SignalDirection.BUY,
                    strength=SignalStrength.STRONG,
                    timestamp=timestamp,
                    price=current_price,
                    value=ema_20.iloc[i],
                    description="EMA 20 crossed above EMA 50 (Bullish)",
                    confidence=0.8,
                    metadata={'fast_ma': 'EMA 20', 'slow_ma': 'EMA 50', 'crossover_type': 'bullish'}
                )
                signals.append(signal)
            
            elif ema_20.iloc[i] < ema_50.iloc[i] and ema_20.iloc[i-1] >= ema_50.iloc[i-1]:
                signal = Signal(
                    signal_type=SignalType.EMA_CROSSOVER,
                    direction=SignalDirection.SELL,
                    strength=SignalStrength.STRONG,
                    timestamp=timestamp,
                    price=current_price,
                    value=ema_20.iloc[i],
                    description="EMA 20 crossed below EMA 50 (Bearish)",
                    confidence=0.8,
                    metadata={'fast_ma': 'EMA 20', 'slow_ma': 'EMA 50', 'crossover_type': 'bearish'}
                )
                signals.append(signal)
            
            # Golden Cross (EMA 50 vs EMA 200)
            if ema_50.iloc[i] > ema_200.iloc[i] and ema_50.iloc[i-1] <= ema_200.iloc[i-1]:
                signal = Signal(
                    signal_type=SignalType.EMA_CROSSOVER,
                    direction=SignalDirection.STRONG_BUY,
                    strength=SignalStrength.VERY_STRONG,
                    timestamp=timestamp,
                    price=current_price,
                    value=ema_50.iloc[i],
                    description="Golden Cross: EMA 50 crossed above EMA 200",
                    confidence=0.9,
                    metadata={'fast_ma': 'EMA 50', 'slow_ma': 'EMA 200', 'crossover_type': 'golden_cross'}
                )
                signals.append(signal)
            
            # Death Cross (EMA 50 vs EMA 200)
            elif ema_50.iloc[i] < ema_200.iloc[i] and ema_50.iloc[i-1] >= ema_200.iloc[i-1]:
                signal = Signal(
                    signal_type=SignalType.EMA_CROSSOVER,
                    direction=SignalDirection.STRONG_SELL,
                    strength=SignalStrength.VERY_STRONG,
                    timestamp=timestamp,
                    price=current_price,
                    value=ema_50.iloc[i],
                    description="Death Cross: EMA 50 crossed below EMA 200",
                    confidence=0.9,
                    metadata={'fast_ma': 'EMA 50', 'slow_ma': 'EMA 200', 'crossover_type': 'death_cross'}
                )
                signals.append(signal)
        
        return signals
    
    def _calculate_price_ma_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Calculate price vs moving average signals."""
        signals = []
        close_prices = data['close']
        
        # Calculate moving averages
        ema_20 = calculate_ema(close_prices, 20)
        ema_50 = calculate_ema(close_prices, 50)
        
        for i in range(len(data)):
            current_price = close_prices.iloc[i]
            timestamp = data.index[i]
            
            # Price vs EMA 20
            if current_price > ema_20.iloc[i] * 1.02:  # 2% above EMA 20
                signal = Signal(
                    signal_type=SignalType.PRICE_MA_CROSSOVER,
                    direction=SignalDirection.BUY,
                    strength=SignalStrength.MODERATE,
                    timestamp=timestamp,
                    price=current_price,
                    value=current_price / ema_20.iloc[i] - 1,
                    description="Price 2% above EMA 20",
                    confidence=0.6,
                    metadata={'ma': 'EMA 20', 'deviation': 'above'}
                )
                signals.append(signal)
            
            elif current_price < ema_20.iloc[i] * 0.98:  # 2% below EMA 20
                signal = Signal(
                    signal_type=SignalType.PRICE_MA_CROSSOVER,
                    direction=SignalDirection.SELL,
                    strength=SignalStrength.MODERATE,
                    timestamp=timestamp,
                    price=current_price,
                    value=current_price / ema_20.iloc[i] - 1,
                    description="Price 2% below EMA 20",
                    confidence=0.6,
                    metadata={'ma': 'EMA 20', 'deviation': 'below'}
                )
                signals.append(signal)
        
        return signals
    
    def _calculate_rsi_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Calculate RSI-based signals."""
        signals = []
        close_prices = data['close']
        rsi = calculate_rsi(close_prices, 14)
        
        for i in range(len(data)):
            current_price = close_prices.iloc[i]
            timestamp = data.index[i]
            rsi_value = rsi.iloc[i]
            
            if pd.isna(rsi_value):
                continue
            
            # Oversold conditions
            if rsi_value < 30:
                signal = Signal(
                    signal_type=SignalType.RSI_SIGNAL,
                    direction=SignalDirection.BUY,
                    strength=SignalStrength.STRONG if rsi_value < 20 else SignalStrength.MODERATE,
                    timestamp=timestamp,
                    price=current_price,
                    value=rsi_value,
                    description=f"RSI oversold ({rsi_value:.1f})",
                    confidence=0.7 if rsi_value < 20 else 0.5,
                    metadata={'rsi_value': rsi_value, 'condition': 'oversold'}
                )
                signals.append(signal)
            
            # Overbought conditions
            elif rsi_value > 70:
                signal = Signal(
                    signal_type=SignalType.RSI_SIGNAL,
                    direction=SignalDirection.SELL,
                    strength=SignalStrength.STRONG if rsi_value > 80 else SignalStrength.MODERATE,
                    timestamp=timestamp,
                    price=current_price,
                    value=rsi_value,
                    description=f"RSI overbought ({rsi_value:.1f})",
                    confidence=0.7 if rsi_value > 80 else 0.5,
                    metadata={'rsi_value': rsi_value, 'condition': 'overbought'}
                )
                signals.append(signal)
        
        return signals
    
    def _calculate_macd_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Calculate MACD-based signals."""
        signals = []
        close_prices = data['close']
        macd_line, signal_line, histogram = calculate_macd(close_prices)
        
        for i in range(1, len(data)):
            current_price = close_prices.iloc[i]
            timestamp = data.index[i]
            
            # MACD line crosses above signal line
            if macd_line.iloc[i] > signal_line.iloc[i] and macd_line.iloc[i-1] <= signal_line.iloc[i-1]:
                signal = Signal(
                    signal_type=SignalType.MACD_SIGNAL,
                    direction=SignalDirection.BUY,
                    strength=SignalStrength.STRONG,
                    timestamp=timestamp,
                    price=current_price,
                    value=macd_line.iloc[i],
                    description="MACD line crossed above signal line",
                    confidence=0.8,
                    metadata={'macd_line': macd_line.iloc[i], 'signal_line': signal_line.iloc[i]}
                )
                signals.append(signal)
            
            # MACD line crosses below signal line
            elif macd_line.iloc[i] < signal_line.iloc[i] and macd_line.iloc[i-1] >= signal_line.iloc[i-1]:
                signal = Signal(
                    signal_type=SignalType.MACD_SIGNAL,
                    direction=SignalDirection.SELL,
                    strength=SignalStrength.STRONG,
                    timestamp=timestamp,
                    price=current_price,
                    value=macd_line.iloc[i],
                    description="MACD line crossed below signal line",
                    confidence=0.8,
                    metadata={'macd_line': macd_line.iloc[i], 'signal_line': signal_line.iloc[i]}
                )
                signals.append(signal)
        
        return signals
    
    def _calculate_bollinger_bands_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Calculate Bollinger Bands signals."""
        signals = []
        close_prices = data['close']
        upper, middle, lower = calculate_bollinger_bands(close_prices)
        
        for i in range(len(data)):
            current_price = close_prices.iloc[i]
            timestamp = data.index[i]
            
            # Price touches or breaks below lower band
            if current_price <= lower.iloc[i]:
                signal = Signal(
                    signal_type=SignalType.BOLLINGER_BANDS_SIGNAL,
                    direction=SignalDirection.BUY,
                    strength=SignalStrength.STRONG,
                    timestamp=timestamp,
                    price=current_price,
                    value=(current_price - lower.iloc[i]) / (upper.iloc[i] - lower.iloc[i]),
                    description="Price at or below Bollinger Bands lower band",
                    confidence=0.7,
                    metadata={'position': 'lower_band', 'bb_width': upper.iloc[i] - lower.iloc[i]}
                )
                signals.append(signal)
            
            # Price touches or breaks above upper band
            elif current_price >= upper.iloc[i]:
                signal = Signal(
                    signal_type=SignalType.BOLLINGER_BANDS_SIGNAL,
                    direction=SignalDirection.SELL,
                    strength=SignalStrength.STRONG,
                    timestamp=timestamp,
                    price=current_price,
                    value=(current_price - lower.iloc[i]) / (upper.iloc[i] - lower.iloc[i]),
                    description="Price at or above Bollinger Bands upper band",
                    confidence=0.7,
                    metadata={'position': 'upper_band', 'bb_width': upper.iloc[i] - lower.iloc[i]}
                )
                signals.append(signal)
        
        return signals
    
    def _calculate_volume_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Calculate volume-based signals."""
        signals = []
        close_prices = data['close']
        volume = data.get('volume', pd.Series(index=data.index, dtype=float))
        
        if volume.empty or volume.isna().all():
            return signals
        
        # Calculate volume moving average
        volume_ma = volume.rolling(window=20).mean()
        
        for i in range(len(data)):
            current_price = close_prices.iloc[i]
            timestamp = data.index[i]
            current_volume = volume.iloc[i]
            avg_volume = volume_ma.iloc[i]
            
            if pd.isna(current_volume) or pd.isna(avg_volume):
                continue
            
            # High volume breakout
            if current_volume > avg_volume * 2:  # 2x average volume
                price_change = (current_price - close_prices.iloc[i-1]) / close_prices.iloc[i-1] if i > 0 else 0
                
                if price_change > 0.02:  # 2% price increase
                    signal = Signal(
                        signal_type=SignalType.VOLUME_SIGNAL,
                        direction=SignalDirection.BUY,
                        strength=SignalStrength.STRONG,
                        timestamp=timestamp,
                        price=current_price,
                        value=current_volume / avg_volume,
                        description="High volume breakout",
                        confidence=0.8,
                        metadata={'volume_ratio': current_volume / avg_volume, 'price_change': price_change}
                    )
                    signals.append(signal)
        
        return signals
    
    def _calculate_support_resistance_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Calculate support/resistance signals."""
        signals = []
        close_prices = data['close']
        high_prices = data['high']
        low_prices = data['low']
        
        # Calculate support and resistance levels
        try:
            from finance_tools.analysis.analysis import calculate_support_resistance
        except ImportError:
            from ..analysis import calculate_support_resistance
        support, resistance = calculate_support_resistance(high_prices, low_prices)
        
        for i in range(len(data)):
            current_price = close_prices.iloc[i]
            timestamp = data.index[i]
            support_level = support.iloc[i]
            resistance_level = resistance.iloc[i]
            
            if pd.isna(support_level) or pd.isna(resistance_level):
                continue
            
            # Price near support level
            if current_price <= support_level * 1.02:  # Within 2% of support
                signal = Signal(
                    signal_type=SignalType.SUPPORT_RESISTANCE_SIGNAL,
                    direction=SignalDirection.BUY,
                    strength=SignalStrength.MODERATE,
                    timestamp=timestamp,
                    price=current_price,
                    value=current_price / support_level,
                    description="Price near support level",
                    confidence=0.6,
                    metadata={'support_level': support_level, 'distance': current_price / support_level}
                )
                signals.append(signal)
            
            # Price near resistance level
            elif current_price >= resistance_level * 0.98:  # Within 2% of resistance
                signal = Signal(
                    signal_type=SignalType.SUPPORT_RESISTANCE_SIGNAL,
                    direction=SignalDirection.SELL,
                    strength=SignalStrength.MODERATE,
                    timestamp=timestamp,
                    price=current_price,
                    value=current_price / resistance_level,
                    description="Price near resistance level",
                    confidence=0.6,
                    metadata={'resistance_level': resistance_level, 'distance': current_price / resistance_level}
                )
                signals.append(signal)
        
        return signals
    
    def _create_signal_summary(self, signals: List[Signal]) -> Dict[str, Any]:
        """Create a summary of all signals."""
        if not signals:
            return {'total_signals': 0, 'buy_signals': 0, 'sell_signals': 0}
        
        buy_signals = [s for s in signals if s.direction in [SignalDirection.BUY, SignalDirection.STRONG_BUY]]
        sell_signals = [s for s in signals if s.direction in [SignalDirection.SELL, SignalDirection.STRONG_SELL]]
        
        # Group by signal type
        signal_types = {}
        for signal in signals:
            signal_type = signal.signal_type.value
            if signal_type not in signal_types:
                signal_types[signal_type] = 0
            signal_types[signal_type] += 1
        
        # Calculate average confidence
        avg_confidence = sum(s.confidence for s in signals) / len(signals) if signals else 0
        
        return {
            'total_signals': len(signals),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'signal_types': signal_types,
            'average_confidence': avg_confidence,
            'strongest_signal': max(signals, key=lambda s: s.confidence).to_dict() if signals else None
        }


# Convenience functions for direct signal calculation
def calculate_ema_crossover_signals(data: pd.DataFrame) -> List[Signal]:
    """Calculate EMA crossover signals."""
    calculator = SignalCalculator()
    return calculator._calculate_ema_crossover_signals(data)


def calculate_price_ma_signals(data: pd.DataFrame) -> List[Signal]:
    """Calculate price vs moving average signals."""
    calculator = SignalCalculator()
    return calculator._calculate_price_ma_signals(data)


def calculate_momentum_signals(data: pd.DataFrame) -> List[Signal]:
    """Calculate momentum-based signals (RSI, MACD)."""
    calculator = SignalCalculator()
    signals = []
    signals.extend(calculator._calculate_rsi_signals(data))
    signals.extend(calculator._calculate_macd_signals(data))
    return signals


def calculate_volume_signals(data: pd.DataFrame) -> List[Signal]:
    """Calculate volume-based signals."""
    calculator = SignalCalculator()
    return calculator._calculate_volume_signals(data)


def calculate_multi_timeframe_signals(data: pd.DataFrame, timeframes: List[str] = None) -> Dict[str, List[Signal]]:
    """Calculate signals across multiple timeframes."""
    if timeframes is None:
        timeframes = ['1d', '1w', '1m']
    
    calculator = SignalCalculator()
    results = {}
    
    for timeframe in timeframes:
        # Resample data to timeframe
        resampled_data = data.resample(timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        if len(resampled_data) > 20:  # Need enough data
            signals = calculator.calculate_all_signals(resampled_data)
            results[timeframe] = signals.signals
    
    return results 