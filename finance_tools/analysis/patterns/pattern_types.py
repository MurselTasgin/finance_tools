# finance_tools/analysis/patterns/pattern_types.py
"""
Pattern types and enums for pattern detection.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime


class PatternType(Enum):
    """Types of price patterns."""
    CHART_PATTERN = "chart_pattern"
    CANDLESTICK_PATTERN = "candlestick_pattern"
    BREAKOUT_PATTERN = "breakout_pattern"
    DIVERGENCE_PATTERN = "divergence_pattern"
    HARMONIC_PATTERN = "harmonic_pattern"


class PatternDirection(Enum):
    """Pattern direction."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class PatternReliability(Enum):
    """Pattern reliability levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ChartPattern(Enum):
    """Chart pattern types."""
    HEAD_AND_SHOULDERS = "head_and_shoulders"
    INVERSE_HEAD_AND_SHOULDERS = "inverse_head_and_shoulders"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    TRIPLE_TOP = "triple_top"
    TRIPLE_BOTTOM = "triple_bottom"
    ASCENDING_TRIANGLE = "ascending_triangle"
    DESCENDING_TRIANGLE = "descending_triangle"
    SYMMETRICAL_TRIANGLE = "symmetrical_triangle"
    RECTANGLE = "rectangle"
    FLAG = "flag"
    PENNANT = "pennant"
    WEDGE = "wedge"
    CHANNEL = "channel"


class CandlestickPattern(Enum):
    """Candlestick pattern types."""
    DOJI = "doji"
    HAMMER = "hammer"
    HANGING_MAN = "hanging_man"
    SHOOTING_STAR = "shooting_star"
    BULLISH_ENGULFING = "bullish_engulfing"
    BEARISH_ENGULFING = "bearish_engulfing"
    MORNING_STAR = "morning_star"
    EVENING_STAR = "evening_star"
    THREE_WHITE_SOLDIERS = "three_white_soldiers"
    THREE_BLACK_CROWS = "three_black_crows"
    INV_HAMMER = "inverted_hammer"
    SPINNING_TOP = "spinning_top"
    MARUBOZU = "marubozu"


class BreakoutPattern(Enum):
    """Breakout pattern types."""
    RESISTANCE_BREAKOUT = "resistance_breakout"
    SUPPORT_BREAKDOWN = "support_breakdown"
    TRIANGLE_BREAKOUT = "triangle_breakout"
    RECTANGLE_BREAKOUT = "rectangle_breakout"
    FLAG_BREAKOUT = "flag_breakout"
    PENNANT_BREAKOUT = "pennant_breakout"
    CHANNEL_BREAKOUT = "channel_breakout"
    GAP_BREAKOUT = "gap_breakout"


class DivergencePattern(Enum):
    """Divergence pattern types."""
    BULLISH_DIVERGENCE = "bullish_divergence"
    BEARISH_DIVERGENCE = "bearish_divergence"
    HIDDEN_BULLISH_DIVERGENCE = "hidden_bullish_divergence"
    HIDDEN_BEARISH_DIVERGENCE = "hidden_bearish_divergence"


class HarmonicPattern(Enum):
    """Harmonic pattern types."""
    GARTLEY = "gartley"
    BUTTERFLY = "butterfly"
    BAT = "bat"
    CRAB = "crab"
    CYPHER = "cypher"
    SHARK = "shark"


class Pattern:
    """Represents a detected price pattern."""
    
    def __init__(self, pattern_type: PatternType, pattern_name: str, direction: PatternDirection,
                 reliability: PatternReliability, start_date: datetime, end_date: datetime,
                 breakout_price: Optional[float] = None, target_price: Optional[float] = None,
                 stop_loss: Optional[float] = None, confidence: float = 0.0,
                 description: str = "", metadata: Dict[str, Any] = None, **kwargs):
        self.pattern_type = pattern_type
        self.pattern_name = pattern_name
        self.direction = direction
        self.reliability = reliability
        self.start_date = start_date
        self.end_date = end_date
        self.breakout_price = breakout_price
        self.target_price = target_price
        self.stop_loss = stop_loss
        self.confidence = confidence
        self.description = description
        self.metadata = metadata if metadata is not None else {}
        
        # Set any additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary."""
        return {
            'pattern_type': self.pattern_type.value,
            'pattern_name': self.pattern_name,
            'direction': self.direction.value,
            'reliability': self.reliability.value,
            'start_date': self.start_date.isoformat() if hasattr(self.start_date, 'isoformat') else str(self.start_date),
            'end_date': self.end_date.isoformat() if hasattr(self.end_date, 'isoformat') else str(self.end_date),
            'breakout_price': self.breakout_price,
            'target_price': self.target_price,
            'stop_loss': self.stop_loss,
            'confidence': self.confidence,
            'description': self.description,
            'metadata': self.metadata
        }




class ChartPatternData(Pattern):
    """Represents a chart pattern."""
    
    def __init__(self, pattern_type: PatternType, pattern_name: str, direction: PatternDirection,
                 reliability: PatternReliability, start_date: datetime, end_date: datetime,
                 chart_pattern_type: 'ChartPattern', **kwargs):
        super().__init__(pattern_type, pattern_name, direction, reliability, start_date, end_date, **kwargs)
        self.chart_pattern_type = chart_pattern_type
        self.key_levels = kwargs.get('key_levels', [])
        self.volume_profile = kwargs.get('volume_profile', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chart pattern to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'chart_pattern_type': self.chart_pattern_type.value,
            'key_levels': self.key_levels,
            'volume_profile': self.volume_profile
        })
        return base_dict


class CandlestickPatternData(Pattern):
    """Represents a candlestick pattern."""
    
    def __init__(self, pattern_type: PatternType, pattern_name: str, direction: PatternDirection,
                 reliability: PatternReliability, start_date: datetime, end_date: datetime,
                 candlestick_pattern_type: 'CandlestickPattern', **kwargs):
        super().__init__(pattern_type, pattern_name, direction, reliability, start_date, end_date, **kwargs)
        self.candlestick_pattern_type = candlestick_pattern_type
        self.body_size = kwargs.get('body_size', 0.0)
        self.upper_shadow = kwargs.get('upper_shadow', 0.0)
        self.lower_shadow = kwargs.get('lower_shadow', 0.0)
        self.color = kwargs.get('color', 'unknown')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert candlestick pattern to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'candlestick_pattern_type': self.candlestick_pattern_type.value,
            'body_size': self.body_size,
            'upper_shadow': self.upper_shadow,
            'lower_shadow': self.lower_shadow,
            'color': self.color
        })
        return base_dict


class BreakoutPatternData(Pattern):
    """Represents a breakout pattern."""
    
    def __init__(self, pattern_type: PatternType, pattern_name: str, direction: PatternDirection,
                 reliability: PatternReliability, start_date: datetime, end_date: datetime,
                 breakout_pattern_type: 'BreakoutPattern', **kwargs):
        super().__init__(pattern_type, pattern_name, direction, reliability, start_date, end_date, **kwargs)
        self.breakout_pattern_type = breakout_pattern_type
        self.breakout_volume = kwargs.get('breakout_volume')
        self.breakout_strength = kwargs.get('breakout_strength', 0.0)
        self.consolidation_period = kwargs.get('consolidation_period', 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert breakout pattern to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'breakout_pattern_type': self.breakout_pattern_type.value,
            'breakout_volume': self.breakout_volume,
            'breakout_strength': self.breakout_strength,
            'consolidation_period': self.consolidation_period
        })
        return base_dict


class DivergencePatternData(Pattern):
    """Represents a divergence pattern."""
    
    def __init__(self, pattern_type: PatternType, pattern_name: str, direction: PatternDirection,
                 reliability: PatternReliability, start_date: datetime, end_date: datetime,
                 divergence_pattern_type: 'DivergencePattern', **kwargs):
        super().__init__(pattern_type, pattern_name, direction, reliability, start_date, end_date, **kwargs)
        self.divergence_pattern_type = divergence_pattern_type
        self.indicator_name = kwargs.get('indicator_name', '')
        self.price_highs = kwargs.get('price_highs', [])
        self.price_lows = kwargs.get('price_lows', [])
        self.indicator_highs = kwargs.get('indicator_highs', [])
        self.indicator_lows = kwargs.get('indicator_lows', [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert divergence pattern to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'divergence_pattern_type': self.divergence_pattern_type.value,
            'indicator_name': self.indicator_name,
            'price_highs': self.price_highs,
            'price_lows': self.price_lows,
            'indicator_highs': self.indicator_highs,
            'indicator_lows': self.indicator_lows
        })
        return base_dict


class HarmonicPatternData(Pattern):
    """Represents a harmonic pattern."""
    
    def __init__(self, pattern_type: PatternType, pattern_name: str, direction: PatternDirection,
                 reliability: PatternReliability, start_date: datetime, end_date: datetime,
                 harmonic_pattern_type: 'HarmonicPattern', **kwargs):
        super().__init__(pattern_type, pattern_name, direction, reliability, start_date, end_date, **kwargs)
        self.harmonic_pattern_type = harmonic_pattern_type
        self.fibonacci_levels = kwargs.get('fibonacci_levels', {})
        self.completion_ratio = kwargs.get('completion_ratio', 0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert harmonic pattern to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'harmonic_pattern_type': self.harmonic_pattern_type.value,
            'fibonacci_levels': self.fibonacci_levels,
            'completion_ratio': self.completion_ratio
        })
        return base_dict


@dataclass
class PatternResult:
    """Container for pattern detection results."""
    patterns: List[Pattern]
    summary: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def get_bullish_patterns(self) -> List[Pattern]:
        """Get all bullish patterns."""
        return [p for p in self.patterns if p.direction == PatternDirection.BULLISH]
    
    def get_bearish_patterns(self) -> List[Pattern]:
        """Get all bearish patterns."""
        return [p for p in self.patterns if p.direction == PatternDirection.BEARISH]
    
    def get_high_reliability_patterns(self) -> List[Pattern]:
        """Get patterns with high reliability."""
        return [p for p in self.patterns if p.reliability in [PatternReliability.HIGH, PatternReliability.VERY_HIGH]]
    
    def get_breakout_patterns(self) -> List[BreakoutPatternData]:
        """Get all breakout patterns."""
        return [p for p in self.patterns if isinstance(p, BreakoutPatternData)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern result to dictionary."""
        return {
            'patterns': [p.to_dict() for p in self.patterns],
            'summary': self.summary,
            'metadata': self.metadata
        } 