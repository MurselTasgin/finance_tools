# finance_tools/analysis/suggestions/__init__.py
"""
Suggestions module for generating buy, sell, hold recommendations.

This module provides comprehensive trading suggestions based on:
- Technical indicators and signals
- Pattern analysis
- Risk assessment
- Market conditions
- Portfolio context
"""

from .suggestion_engine import (
    SuggestionEngine,
    generate_trading_suggestions,
    analyze_risk_reward,
    calculate_position_size,
    generate_portfolio_suggestions
)

from .suggestion_types import (
    SuggestionType,
    SuggestionStrength,
    RiskLevel,
    TradingSuggestion,
    RiskAssessment,
    PositionRecommendation,
    SuggestionResult
)

__version__ = "1.0.0"
__author__ = "Finance Tools Team"

__all__ = [
    "SuggestionEngine",
    "generate_trading_suggestions",
    "analyze_risk_reward",
    "calculate_position_size",
    "generate_portfolio_suggestions",
    "SuggestionType",
    "SuggestionStrength",
    "RiskLevel",
    "TradingSuggestion",
    "RiskAssessment",
    "PositionRecommendation",
    "SuggestionResult"
] 