# finance_tools/analysis/__init__.py
"""
Advanced technical analysis module for financial data.

This module provides comprehensive technical analysis capabilities including:
- Core Analysis: Moving averages, momentum, volatility, trend indicators
- Signals: EMA crossovers, RSI signals, MACD signals, volume signals
- Patterns: Chart patterns, candlestick patterns, breakouts, divergences
- Suggestions: Buy/sell/hold recommendations with risk assessment
- Scanner: Stock scanning for trading opportunities
- Portfolio: Optimization and risk management
"""

from .analysis import (
    calculate_ema,
    calculate_sma,
    calculate_wma,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_stochastic,
    calculate_momentum,
    calculate_roc,
    calculate_atr,
    calculate_cci,
    calculate_supertrend,
    calculate_adx,
    calculate_obv,
    calculate_vwap,
    calculate_support_resistance,
    TechnicalAnalysis
)
from .config import AnalysisConfig, get_config, IndicatorCategory, IndicatorConfig
from .utils import (
    validate_ohlcv_data,
    clean_data,
    prepare_data_for_analysis,
    format_analysis_results,
    calculate_performance_metrics,
    create_summary_report,
    export_results,
    validate_indicator_parameters,
    get_indicator_dependencies,
    check_data_completeness
)

# Signals module
from .signals import (
    SignalCalculator, calculate_ema_crossover_signals, calculate_price_ma_signals,
    calculate_momentum_signals, calculate_volume_signals, calculate_multi_timeframe_signals
)

# Patterns module
from .patterns import (
    PatternDetector, detect_chart_patterns, detect_candlestick_patterns,
    detect_breakout_patterns, detect_divergence_patterns, detect_harmonic_patterns
)

# Suggestions module
from .suggestions import (
    SuggestionEngine, generate_trading_suggestions, analyze_risk_reward,
    calculate_position_size, generate_portfolio_suggestions
)

# Scanner module
from .scanner import (
    StockScanner, scan_for_signals, scan_for_patterns, scan_for_breakouts,
    scan_for_momentum, scan_for_volume_anomalies, scan_multiple_timeframes
)

# Portfolio module
from .portfolio import (
    PortfolioOptimizer, PortfolioSuggester, optimize_portfolio,
    suggest_portfolio_allocation, suggest_rebalancing, suggest_risk_management
)

__version__ = "2.0.0"
__author__ = "Finance Tools Team"

__all__ = [
    # Core analysis
    "calculate_ema", "calculate_sma", "calculate_wma", "calculate_rsi", "calculate_macd",
    "calculate_bollinger_bands", "calculate_stochastic", "calculate_momentum", "calculate_roc",
    "calculate_atr", "calculate_cci", "calculate_supertrend", "calculate_adx",
    "calculate_obv", "calculate_vwap", "calculate_support_resistance", "TechnicalAnalysis",
    
    # Configuration
    "AnalysisConfig", "get_config", "IndicatorCategory", "IndicatorConfig",
    
    # Utilities
    "validate_ohlcv_data", "clean_data", "prepare_data_for_analysis",
    "format_analysis_results", "calculate_performance_metrics",
    "create_summary_report", "export_results", "validate_indicator_parameters",
    "get_indicator_dependencies", "check_data_completeness",
    
    # Signals
    "SignalCalculator", "calculate_ema_crossover_signals", "calculate_price_ma_signals",
    "calculate_momentum_signals", "calculate_volume_signals", "calculate_multi_timeframe_signals",
    
    # Patterns
    "PatternDetector", "detect_chart_patterns", "detect_candlestick_patterns",
    "detect_breakout_patterns", "detect_divergence_patterns", "detect_harmonic_patterns",
    
    # Suggestions
    "SuggestionEngine", "generate_trading_suggestions", "analyze_risk_reward",
    "calculate_position_size", "generate_portfolio_suggestions",
    
    # Scanner
    "StockScanner", "scan_for_signals", "scan_for_patterns", "scan_for_breakouts",
    "scan_for_momentum", "scan_for_volume_anomalies", "scan_multiple_timeframes",
    
    # Portfolio
    "PortfolioOptimizer", "PortfolioSuggester", "optimize_portfolio",
    "suggest_portfolio_allocation", "suggest_rebalancing", "suggest_risk_management"
] 