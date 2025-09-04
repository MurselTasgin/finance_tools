# finance_tools/analysis/scanner/__init__.py
"""
Scanner module for identifying stocks with potential breakouts and opportunities.

This module provides comprehensive stock scanning capabilities including:
- Technical Scanner (based on indicators and signals)
- Pattern Scanner (based on chart patterns)
- Breakout Scanner (based on price breakouts)
- Momentum Scanner (based on momentum indicators)
- Volume Scanner (based on volume analysis)
- Multi-timeframe Scanner
"""

from .stock_scanner import (
    StockScanner,
    scan_for_signals,
    scan_for_patterns,
    scan_for_breakouts,
    scan_for_momentum,
    scan_for_volume_anomalies,
    scan_multiple_timeframes
)

from .scanner_types import (
    ScannerType,
    ScanResult,
    ScannerFilter,
    ScannerCriteria,
    ScanSummary
)

__version__ = "1.0.0"
__author__ = "Finance Tools Team"

__all__ = [
    "StockScanner",
    "scan_for_signals",
    "scan_for_patterns",
    "scan_for_breakouts",
    "scan_for_momentum",
    "scan_for_volume_anomalies",
    "scan_multiple_timeframes",
    "ScannerType",
    "ScanResult",
    "ScannerFilter",
    "ScannerCriteria",
    "ScanSummary"
] 