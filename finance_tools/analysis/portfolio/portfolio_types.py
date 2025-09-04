# finance_tools/analysis/portfolio/portfolio_types.py
"""
Portfolio types and enums for portfolio optimization and management.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime


class OptimizationMethod(Enum):
    """Portfolio optimization methods."""
    MODERN_PORTFOLIO_THEORY = "modern_portfolio_theory"
    RISK_PARITY = "risk_parity"
    MAX_SHARPE_RATIO = "max_sharpe_ratio"
    MIN_VARIANCE = "min_variance"
    MAX_DIVERSIFICATION = "max_diversification"
    EQUAL_WEIGHT = "equal_weight"


class RiskModel(Enum):
    """Risk models for portfolio optimization."""
    HISTORICAL_VOLATILITY = "historical_volatility"
    EXPONENTIAL_WEIGHTED = "exponential_weighted"
    GARCH = "garch"
    CONDITIONAL_VAR = "conditional_var"
    EXPECTED_SHORTFALL = "expected_shortfall"


class PortfolioStrategy(Enum):
    """Portfolio strategies."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    INCOME = "income"
    GROWTH = "growth"
    VALUE = "value"
    MOMENTUM = "momentum"


@dataclass
class RiskMetrics:
    """Risk metrics for portfolio analysis."""
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    var_95: float  # Value at Risk at 95% confidence
    cvar_95: float  # Conditional Value at Risk at 95% confidence
    beta: float
    alpha: float
    tracking_error: float
    information_ratio: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert risk metrics to dictionary."""
        return {
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
            'beta': self.beta,
            'alpha': self.alpha,
            'tracking_error': self.tracking_error,
            'information_ratio': self.information_ratio
        }


@dataclass
class AllocationSuggestion:
    """Portfolio allocation suggestion."""
    symbol: str
    suggested_weight: float
    current_weight: float
    target_weight: float
    rebalance_amount: float
    risk_score: float
    expected_return: float
    reasoning: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert allocation suggestion to dictionary."""
        return {
            'symbol': self.symbol,
            'suggested_weight': self.suggested_weight,
            'current_weight': self.current_weight,
            'target_weight': self.target_weight,
            'rebalance_amount': self.rebalance_amount,
            'risk_score': self.risk_score,
            'expected_return': self.expected_return,
            'reasoning': self.reasoning,
            'metadata': self.metadata
        }


@dataclass
class PortfolioResult:
    """Result of portfolio optimization."""
    optimal_weights: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    risk_metrics: RiskMetrics
    allocation_suggestions: List[AllocationSuggestion]
    rebalancing_needed: bool
    total_rebalance_amount: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert portfolio result to dictionary."""
        return {
            'optimal_weights': self.optimal_weights,
            'expected_return': self.expected_return,
            'expected_volatility': self.expected_volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'risk_metrics': self.risk_metrics.to_dict(),
            'allocation_suggestions': [s.to_dict() for s in self.allocation_suggestions],
            'rebalancing_needed': self.rebalancing_needed,
            'total_rebalance_amount': self.total_rebalance_amount,
            'metadata': self.metadata
        } 