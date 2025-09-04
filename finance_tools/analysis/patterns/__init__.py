# finance_tools/analysis/patterns/__init__.py
"""
Patterns module for detecting sophisticated price patterns and breakouts.

This module provides comprehensive pattern detection including:
- Chart Patterns (Head & Shoulders, Double Tops/Bottoms, etc.)
- Candlestick Patterns (Doji, Hammer, Engulfing, etc.)
- Breakout Patterns (Triangle, Rectangle, Flag, etc.)
- Divergence Patterns (Price vs Indicator divergences)
- Harmonic Patterns (Gartley, Butterfly, etc.)
"""

from .pattern_detector import (
    PatternDetector,
    detect_chart_patterns,
    detect_candlestick_patterns,
    detect_breakout_patterns,
    detect_divergence_patterns,
    detect_harmonic_patterns
)

from .pattern_types import (
    PatternType,
    PatternDirection,
    PatternReliability,
    ChartPattern,
    CandlestickPattern,
    BreakoutPattern,
    DivergencePattern,
    HarmonicPattern
)

__version__ = "1.0.0"
__author__ = "Finance Tools Team"

__all__ = [
    "PatternDetector",
    "detect_chart_patterns",
    "detect_candlestick_patterns",
    "detect_breakout_patterns",
    "detect_divergence_patterns",
    "detect_harmonic_patterns",
    "PatternType",
    "PatternDirection",
    "PatternReliability",
    "ChartPattern",
    "CandlestickPattern",
    "BreakoutPattern",
    "DivergencePattern",
    "HarmonicPattern"
] 