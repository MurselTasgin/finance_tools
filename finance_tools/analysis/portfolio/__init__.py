# finance_tools/analysis/portfolio/__init__.py
"""
Portfolio module for optimization and suggestions.

This module provides comprehensive portfolio management capabilities including:
- Portfolio Optimizer (Modern Portfolio Theory, Risk Parity, etc.)
- Portfolio Suggester (Asset allocation recommendations)
- Risk Management (Position sizing, stop losses, etc.)
- Performance Analysis (Returns, Sharpe ratio, drawdown, etc.)
- Rebalancing Strategies (Time-based, threshold-based, etc.)
"""

from .portfolio_optimizer import (
    PortfolioOptimizer,
    optimize_portfolio,
    calculate_optimal_weights,
    rebalance_portfolio,
    analyze_portfolio_risk
)

from .portfolio_suggester import (
    PortfolioSuggester,
    suggest_portfolio_allocation,
    suggest_rebalancing,
    suggest_risk_management,
    generate_portfolio_report
)

from .portfolio_types import (
    OptimizationMethod,
    RiskModel,
    PortfolioStrategy,
    PortfolioResult,
    AllocationSuggestion,
    RiskMetrics
)

__version__ = "1.0.0"
__author__ = "Finance Tools Team"

__all__ = [
    "PortfolioOptimizer",
    "optimize_portfolio",
    "calculate_optimal_weights",
    "rebalance_portfolio",
    "analyze_portfolio_risk",
    "PortfolioSuggester",
    "suggest_portfolio_allocation",
    "suggest_rebalancing",
    "suggest_risk_management",
    "generate_portfolio_report",
    "OptimizationMethod",
    "RiskModel",
    "PortfolioStrategy",
    "PortfolioResult",
    "AllocationSuggestion",
    "RiskMetrics"
] 