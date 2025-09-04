# finance_tools/analysis/signals/__init__.py
"""
Signals module for calculating trading signals and crossovers.

This module provides comprehensive signal calculation including:
- Moving Average Crossovers (EMA, SMA)
- Price vs Moving Average Signals
- Momentum Signal Crossovers
- Volume-based Signals
- Multi-timeframe Signal Analysis
"""

from .signal_calculator import (
    SignalCalculator,
    calculate_ema_crossover_signals,
    calculate_price_ma_signals,
    calculate_momentum_signals,
    calculate_volume_signals,
    calculate_multi_timeframe_signals
)

from .signal_types import (
    SignalType,
    SignalStrength,
    SignalDirection,
    CrossoverType
)

__version__ = "1.0.0"
__author__ = "Finance Tools Team"

__all__ = [
    "SignalCalculator",
    "calculate_ema_crossover_signals",
    "calculate_price_ma_signals", 
    "calculate_momentum_signals",
    "calculate_volume_signals",
    "calculate_multi_timeframe_signals",
    "SignalType",
    "SignalStrength",
    "SignalDirection",
    "CrossoverType"
] 