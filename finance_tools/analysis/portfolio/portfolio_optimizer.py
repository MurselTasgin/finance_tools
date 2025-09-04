# finance_tools/analysis/portfolio/portfolio_optimizer.py
"""
Portfolio optimizer for asset allocation and risk management.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .portfolio_types import (
    OptimizationMethod, RiskModel, PortfolioStrategy,
    PortfolioResult, RiskMetrics, AllocationSuggestion
)

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """
    Portfolio optimizer for asset allocation and risk management.
    """
    
    def __init__(self):
        """Initialize the portfolio optimizer."""
        self.risk_free_rate = 0.02  # 2% risk-free rate
    
    def optimize_portfolio(self, returns_data: pd.DataFrame,
                          method: OptimizationMethod = OptimizationMethod.MODERN_PORTFOLIO_THEORY,
                          constraints: Dict[str, Any] = None) -> PortfolioResult:
        """
        Optimize portfolio allocation.
        
        Args:
            returns_data: DataFrame with asset returns (columns are assets)
            method: Optimization method to use
            constraints: Optimization constraints
            
        Returns:
            PortfolioResult: Optimization results
        """
        if returns_data.empty:
            raise ValueError("Returns data is empty")
        
        # Calculate basic statistics
        mean_returns = returns_data.mean() * 252  # Annualized
        cov_matrix = returns_data.cov() * 252  # Annualized
        
        # Optimize based on method
        if method == OptimizationMethod.MODERN_PORTFOLIO_THEORY:
            optimal_weights = self._optimize_mpt(mean_returns, cov_matrix, constraints)
        elif method == OptimizationMethod.RISK_PARITY:
            optimal_weights = self._optimize_risk_parity(cov_matrix, constraints)
        elif method == OptimizationMethod.MAX_SHARPE_RATIO:
            optimal_weights = self._optimize_max_sharpe(mean_returns, cov_matrix, constraints)
        elif method == OptimizationMethod.MIN_VARIANCE:
            optimal_weights = self._optimize_min_variance(cov_matrix, constraints)
        elif method == OptimizationMethod.EQUAL_WEIGHT:
            optimal_weights = self._equal_weight_allocation(returns_data.columns)
        else:
            raise ValueError(f"Unknown optimization method: {method}")
        
        # Calculate portfolio metrics
        expected_return = np.sum(optimal_weights * mean_returns)
        expected_volatility = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
        sharpe_ratio = (expected_return - self.risk_free_rate) / expected_volatility if expected_volatility > 0 else 0
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(returns_data, optimal_weights)
        
        # Generate allocation suggestions
        allocation_suggestions = self._generate_allocation_suggestions(
            returns_data.columns, optimal_weights, mean_returns, cov_matrix
        )
        
        # Check if rebalancing is needed
        rebalancing_needed = self._check_rebalancing_needed(allocation_suggestions)
        total_rebalance_amount = sum(abs(s.rebalance_amount) for s in allocation_suggestions)
        
        return PortfolioResult(
            optimal_weights=dict(zip(returns_data.columns, optimal_weights)),
            expected_return=expected_return,
            expected_volatility=expected_volatility,
            sharpe_ratio=sharpe_ratio,
            risk_metrics=risk_metrics,
            allocation_suggestions=allocation_suggestions,
            rebalancing_needed=rebalancing_needed,
            total_rebalance_amount=total_rebalance_amount
        )
    
    def _optimize_mpt(self, mean_returns: pd.Series, cov_matrix: pd.DataFrame,
                      constraints: Dict[str, Any] = None) -> np.ndarray:
        """Optimize using Modern Portfolio Theory."""
        n_assets = len(mean_returns)
        
        # Simple optimization: maximize Sharpe ratio
        # In a real implementation, you would use scipy.optimize
        weights = np.ones(n_assets) / n_assets  # Equal weight as starting point
        
        # Calculate optimal weights (simplified)
        for _ in range(100):  # Simple iteration
            portfolio_return = np.sum(weights * mean_returns)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            
            if portfolio_vol > 0:
                sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
                # Simple gradient ascent (simplified)
                for i in range(n_assets):
                    weights[i] += 0.001 * (mean_returns[i] - portfolio_return) / portfolio_vol
                
                # Normalize weights
                weights = np.maximum(weights, 0)  # No short selling
                weights = weights / np.sum(weights)
        
        return weights
    
    def _optimize_risk_parity(self, cov_matrix: pd.DataFrame,
                             constraints: Dict[str, Any] = None) -> np.ndarray:
        """Optimize using Risk Parity approach."""
        n_assets = len(cov_matrix)
        
        # Risk parity: each asset contributes equally to portfolio risk
        # Simplified implementation
        asset_vols = np.sqrt(np.diag(cov_matrix))
        weights = 1 / asset_vols
        weights = weights / np.sum(weights)
        
        return weights
    
    def _optimize_max_sharpe(self, mean_returns: pd.Series, cov_matrix: pd.DataFrame,
                            constraints: Dict[str, Any] = None) -> np.ndarray:
        """Optimize for maximum Sharpe ratio."""
        n_assets = len(mean_returns)
        
        # Simplified maximum Sharpe ratio optimization
        # In practice, you would use scipy.optimize.minimize
        weights = np.ones(n_assets) / n_assets
        
        for _ in range(50):
            portfolio_return = np.sum(weights * mean_returns)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            
            if portfolio_vol > 0:
                # Maximize Sharpe ratio
                for i in range(n_assets):
                    if portfolio_vol > 0:
                        weights[i] += 0.001 * (mean_returns[i] - portfolio_return) / portfolio_vol
                
                weights = np.maximum(weights, 0)
                weights = weights / np.sum(weights)
        
        return weights
    
    def _optimize_min_variance(self, cov_matrix: pd.DataFrame,
                              constraints: Dict[str, Any] = None) -> np.ndarray:
        """Optimize for minimum variance."""
        n_assets = len(cov_matrix)
        
        # Minimum variance portfolio
        # In practice, you would use scipy.optimize.minimize
        # For now, use inverse volatility weighting
        asset_vols = np.sqrt(np.diag(cov_matrix))
        weights = 1 / (asset_vols ** 2)
        weights = weights / np.sum(weights)
        
        return weights
    
    def _equal_weight_allocation(self, assets: List[str]) -> np.ndarray:
        """Equal weight allocation."""
        n_assets = len(assets)
        return np.ones(n_assets) / n_assets
    
    def _calculate_risk_metrics(self, returns_data: pd.DataFrame,
                               weights: np.ndarray) -> RiskMetrics:
        """Calculate comprehensive risk metrics."""
        # Portfolio returns
        portfolio_returns = returns_data.dot(weights)
        
        # Basic metrics
        volatility = portfolio_returns.std() * np.sqrt(252)
        mean_return = portfolio_returns.mean() * 252
        
        # Sharpe ratio
        sharpe_ratio = (mean_return - self.risk_free_rate) / volatility if volatility > 0 else 0
        
        # Sortino ratio (using downside deviation)
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = (mean_return - self.risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
        
        # Maximum drawdown
        cumulative_returns = (1 + portfolio_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Value at Risk (95% confidence)
        var_95 = np.percentile(portfolio_returns, 5)
        
        # Conditional Value at Risk (95% confidence)
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
        
        # Beta (assuming market is first asset)
        if len(returns_data.columns) > 1:
            market_returns = returns_data.iloc[:, 0]  # First asset as market proxy
            beta = np.cov(portfolio_returns, market_returns)[0, 1] / np.var(market_returns)
        else:
            beta = 1.0
        
        # Alpha
        alpha = mean_return - (self.risk_free_rate + beta * (market_returns.mean() * 252 - self.risk_free_rate))
        
        # Tracking error (if benchmark provided)
        tracking_error = 0.0  # Would need benchmark data
        
        # Information ratio
        information_ratio = alpha / tracking_error if tracking_error > 0 else 0
        
        return RiskMetrics(
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            var_95=var_95,
            cvar_95=cvar_95,
            beta=beta,
            alpha=alpha,
            tracking_error=tracking_error,
            information_ratio=information_ratio
        )
    
    def _generate_allocation_suggestions(self, assets: List[str], optimal_weights: np.ndarray,
                                       mean_returns: pd.Series, cov_matrix: pd.DataFrame) -> List[AllocationSuggestion]:
        """Generate allocation suggestions for each asset."""
        suggestions = []
        
        for i, asset in enumerate(assets):
            current_weight = optimal_weights[i]
            target_weight = current_weight  # For now, target = current
            
            # Calculate risk score (simplified)
            asset_vol = np.sqrt(cov_matrix.iloc[i, i])
            risk_score = asset_vol / mean_returns[i] if mean_returns[i] > 0 else 1.0
            
            # Expected return
            expected_return = mean_returns[i]
            
            # Reasoning
            if current_weight > 0.1:
                reasoning = "High allocation due to strong performance"
            elif current_weight > 0.05:
                reasoning = "Moderate allocation for diversification"
            else:
                reasoning = "Low allocation for risk management"
            
            suggestion = AllocationSuggestion(
                symbol=asset,
                suggested_weight=current_weight,
                current_weight=current_weight,
                target_weight=target_weight,
                rebalance_amount=0.0,  # Would calculate based on current portfolio
                risk_score=risk_score,
                expected_return=expected_return,
                reasoning=reasoning
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _check_rebalancing_needed(self, allocation_suggestions: List[AllocationSuggestion],
                                 threshold: float = 0.05) -> bool:
        """Check if portfolio rebalancing is needed."""
        for suggestion in allocation_suggestions:
            if abs(suggestion.rebalance_amount) > threshold:
                return True
        return False


# Convenience functions
def optimize_portfolio(returns_data: pd.DataFrame,
                     method: OptimizationMethod = OptimizationMethod.MODERN_PORTFOLIO_THEORY,
                     constraints: Dict[str, Any] = None) -> PortfolioResult:
    """Optimize portfolio allocation."""
    optimizer = PortfolioOptimizer()
    return optimizer.optimize_portfolio(returns_data, method, constraints)


def calculate_optimal_weights(returns_data: pd.DataFrame,
                            method: OptimizationMethod = OptimizationMethod.MODERN_PORTFOLIO_THEORY) -> Dict[str, float]:
    """Calculate optimal portfolio weights."""
    result = optimize_portfolio(returns_data, method)
    return result.optimal_weights


def rebalance_portfolio(current_weights: Dict[str, float],
                      target_weights: Dict[str, float],
                      portfolio_value: float) -> Dict[str, float]:
    """Calculate rebalancing trades."""
    rebalance_trades = {}
    
    for asset in set(current_weights.keys()) | set(target_weights.keys()):
        current_weight = current_weights.get(asset, 0.0)
        target_weight = target_weights.get(asset, 0.0)
        
        current_value = current_weight * portfolio_value
        target_value = target_weight * portfolio_value
        trade_amount = target_value - current_value
        
        if abs(trade_amount) > 0.01:  # Minimum trade threshold
            rebalance_trades[asset] = trade_amount
    
    return rebalance_trades


def analyze_portfolio_risk(returns_data: pd.DataFrame, weights: Dict[str, float]) -> RiskMetrics:
    """Analyze portfolio risk metrics."""
    optimizer = PortfolioOptimizer()
    weight_array = np.array([weights.get(asset, 0.0) for asset in returns_data.columns])
    return optimizer._calculate_risk_metrics(returns_data, weight_array) 