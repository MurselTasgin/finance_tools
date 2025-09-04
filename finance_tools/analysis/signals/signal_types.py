# finance_tools/analysis/signals/signal_types.py
"""
Signal types and enums for trading signals.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


class SignalType(Enum):
    """Types of trading signals."""
    EMA_CROSSOVER = "ema_crossover"
    SMA_CROSSOVER = "sma_crossover"
    PRICE_MA_CROSSOVER = "price_ma_crossover"
    RSI_SIGNAL = "rsi_signal"
    MACD_SIGNAL = "macd_signal"
    BOLLINGER_BANDS_SIGNAL = "bollinger_bands_signal"
    STOCHASTIC_SIGNAL = "stochastic_signal"
    VOLUME_SIGNAL = "volume_signal"
    SUPPORT_RESISTANCE_SIGNAL = "support_resistance_signal"
    BREAKOUT_SIGNAL = "breakout_signal"
    DIVERGENCE_SIGNAL = "divergence_signal"
    PATTERN_SIGNAL = "pattern_signal"


class SignalStrength(Enum):
    """Signal strength levels."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class SignalDirection(Enum):
    """Signal direction."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class CrossoverType(Enum):
    """Types of crossovers."""
    BULLISH_CROSSOVER = "bullish_crossover"  # Fast MA crosses above slow MA
    BEARISH_CROSSOVER = "bearish_crossover"  # Fast MA crosses below slow MA
    GOLDEN_CROSS = "golden_cross"  # 50 MA crosses above 200 MA
    DEATH_CROSS = "death_cross"    # 50 MA crosses below 200 MA


@dataclass
class Signal:
    """Represents a trading signal."""
    signal_type: SignalType
    direction: SignalDirection
    strength: SignalStrength
    timestamp: datetime
    price: float
    value: float  # The actual signal value (e.g., RSI value)
    description: str
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary."""
        return {
            'signal_type': self.signal_type.value,
            'direction': self.direction.value,
            'strength': self.strength.value,
            'timestamp': self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp),
            'price': self.price,
            'value': self.value,
            'description': self.description,
            'confidence': self.confidence,
            'metadata': self.metadata
        }


@dataclass
class CrossoverSignal:
    """Represents a crossover signal."""
    crossover_type: CrossoverType
    fast_ma: str  # Name of fast moving average
    slow_ma: str  # Name of slow moving average
    fast_value: float
    slow_value: float
    price: float
    timestamp: datetime
    strength: SignalStrength
    description: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert crossover signal to dictionary."""
        return {
            'crossover_type': self.crossover_type.value,
            'fast_ma': self.fast_ma,
            'slow_ma': self.slow_ma,
            'fast_value': self.fast_value,
            'slow_value': self.slow_value,
            'price': self.price,
            'timestamp': self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp),
            'strength': self.strength.value,
            'description': self.description,
            'metadata': self.metadata
        }


@dataclass
class SignalResult:
    """Container for signal calculation results."""
    signals: list
    summary: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def get_buy_signals(self) -> list:
        """Get all buy signals."""
        return [s for s in self.signals if s.direction in [SignalDirection.BUY, SignalDirection.STRONG_BUY]]
    
    def get_sell_signals(self) -> list:
        """Get all sell signals."""
        return [s for s in self.signals if s.direction in [SignalDirection.SELL, SignalDirection.STRONG_SELL]]
    
    def get_strongest_signal(self) -> Optional[Signal]:
        """Get the strongest signal."""
        if not self.signals:
            return None
        
        # Sort by confidence and strength
        strength_order = {
            SignalStrength.WEAK: 1,
            SignalStrength.MODERATE: 2,
            SignalStrength.STRONG: 3,
            SignalStrength.VERY_STRONG: 4
        }
        
        return max(self.signals, key=lambda s: (s.confidence, strength_order.get(s.strength, 0)))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal result to dictionary."""
        return {
            'signals': [s.to_dict() for s in self.signals],
            'summary': self.summary,
            'metadata': self.metadata
        } 