# finance_tools/analysis/portfolio/portfolio_suggester.py
"""
Portfolio suggester for allocation recommendations and risk management.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .portfolio_types import (
    PortfolioStrategy, RiskModel, AllocationSuggestion, RiskMetrics
)
from .portfolio_optimizer import PortfolioOptimizer

logger = logging.getLogger(__name__)


class PortfolioSuggester:
    """
    Portfolio suggester for allocation recommendations and risk management.
    """
    
    def __init__(self):
        """Initialize the portfolio suggester."""
        self.optimizer = PortfolioOptimizer()
    
    def suggest_portfolio_allocation(self, returns_data: pd.DataFrame,
                                   strategy: PortfolioStrategy = PortfolioStrategy.MODERATE,
                                   risk_tolerance: float = 0.5) -> Dict[str, Any]:
        """
        Suggest portfolio allocation based on strategy and risk tolerance.
        
        Args:
            returns_data: DataFrame with asset returns
            strategy: Portfolio strategy
            risk_tolerance: Risk tolerance (0-1, where 1 is highest risk)
            
        Returns:
            Dict[str, Any]: Allocation suggestions and analysis
        """
        # Calculate basic statistics
        mean_returns = returns_data.mean() * 252
        volatilities = returns_data.std() * np.sqrt(252)
        sharpe_ratios = (mean_returns - self.optimizer.risk_free_rate) / volatilities
        
        # Generate suggestions based on strategy
        if strategy == PortfolioStrategy.CONSERVATIVE:
            suggestions = self._suggest_conservative_allocation(returns_data, risk_tolerance)
        elif strategy == PortfolioStrategy.MODERATE:
            suggestions = self._suggest_moderate_allocation(returns_data, risk_tolerance)
        elif strategy == PortfolioStrategy.AGGRESSIVE:
            suggestions = self._suggest_aggressive_allocation(returns_data, risk_tolerance)
        elif strategy == PortfolioStrategy.INCOME:
            suggestions = self._suggest_income_allocation(returns_data, risk_tolerance)
        elif strategy == PortfolioStrategy.GROWTH:
            suggestions = self._suggest_growth_allocation(returns_data, risk_tolerance)
        elif strategy == PortfolioStrategy.VALUE:
            suggestions = self._suggest_value_allocation(returns_data, risk_tolerance)
        elif strategy == PortfolioStrategy.MOMENTUM:
            suggestions = self._suggest_momentum_allocation(returns_data, risk_tolerance)
        else:
            raise ValueError(f"Unknown portfolio strategy: {strategy}")
        
        # Calculate portfolio metrics
        total_weight = sum(s.suggested_weight for s in suggestions)
        if total_weight > 0:
            # Normalize weights
            for suggestion in suggestions:
                suggestion.suggested_weight /= total_weight
        
        # Calculate expected portfolio metrics
        expected_return = sum(s.suggested_weight * s.expected_return for s in suggestions)
        expected_volatility = self._calculate_portfolio_volatility(returns_data, suggestions)
        
        return {
            'strategy': strategy.value,
            'risk_tolerance': risk_tolerance,
            'suggestions': suggestions,
            'expected_return': expected_return,
            'expected_volatility': expected_volatility,
            'sharpe_ratio': (expected_return - self.optimizer.risk_free_rate) / expected_volatility if expected_volatility > 0 else 0
        }
    
    def _suggest_conservative_allocation(self, returns_data: pd.DataFrame,
                                       risk_tolerance: float) -> List[AllocationSuggestion]:
        """Suggest conservative allocation (low risk, stable returns)."""
        suggestions = []
        assets = returns_data.columns
        
        # Conservative: focus on low volatility, stable assets
        volatilities = returns_data.std() * np.sqrt(252)
        mean_returns = returns_data.mean() * 252
        
        # Sort by volatility (ascending)
        sorted_assets = sorted(zip(assets, volatilities, mean_returns), key=lambda x: x[1])
        
        for i, (asset, vol, ret) in enumerate(sorted_assets):
            # Higher weight for lower volatility assets
            weight = max(0.05, 0.15 - i * 0.02) * (1 - risk_tolerance)
            
            suggestion = AllocationSuggestion(
                symbol=asset,
                suggested_weight=weight,
                current_weight=0.0,
                target_weight=weight,
                rebalance_amount=0.0,
                risk_score=vol,
                expected_return=ret,
                reasoning=f"Conservative allocation: low volatility ({vol:.2%})"
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _suggest_moderate_allocation(self, returns_data: pd.DataFrame,
                                   risk_tolerance: float) -> List[AllocationSuggestion]:
        """Suggest moderate allocation (balanced risk/return)."""
        suggestions = []
        assets = returns_data.columns
        
        # Moderate: balance between risk and return
        sharpe_ratios = (returns_data.mean() * 252 - self.optimizer.risk_free_rate) / (returns_data.std() * np.sqrt(252))
        mean_returns = returns_data.mean() * 252
        
        # Sort by Sharpe ratio (descending)
        sorted_assets = sorted(zip(assets, sharpe_ratios, mean_returns), key=lambda x: x[1], reverse=True)
        
        for i, (asset, sharpe, ret) in enumerate(sorted_assets):
            # Balanced weight distribution
            weight = max(0.05, 0.12 - i * 0.01) * (0.5 + risk_tolerance * 0.5)
            
            suggestion = AllocationSuggestion(
                symbol=asset,
                suggested_weight=weight,
                current_weight=0.0,
                target_weight=weight,
                rebalance_amount=0.0,
                risk_score=1/sharpe if sharpe > 0 else 1.0,
                expected_return=ret,
                reasoning=f"Moderate allocation: good risk-adjusted return (Sharpe: {sharpe:.2f})"
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _suggest_aggressive_allocation(self, returns_data: pd.DataFrame,
                                    risk_tolerance: float) -> List[AllocationSuggestion]:
        """Suggest aggressive allocation (high risk, high return)."""
        suggestions = []
        assets = returns_data.columns
        
        # Aggressive: focus on high return assets
        mean_returns = returns_data.mean() * 252
        
        # Sort by return (descending)
        sorted_assets = sorted(zip(assets, mean_returns), key=lambda x: x[1], reverse=True)
        
        for i, (asset, ret) in enumerate(sorted_assets):
            # Higher weight for higher return assets
            weight = max(0.05, 0.20 - i * 0.03) * risk_tolerance
            
            suggestion = AllocationSuggestion(
                symbol=asset,
                suggested_weight=weight,
                current_weight=0.0,
                target_weight=weight,
                rebalance_amount=0.0,
                risk_score=1.0,  # High risk for aggressive
                expected_return=ret,
                reasoning=f"Aggressive allocation: high expected return ({ret:.2%})"
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _suggest_income_allocation(self, returns_data: pd.DataFrame,
                                 risk_tolerance: float) -> List[AllocationSuggestion]:
        """Suggest income-focused allocation."""
        suggestions = []
        assets = returns_data.columns
        
        # Income: focus on consistent positive returns
        mean_returns = returns_data.mean() * 252
        return_consistency = (returns_data > 0).mean()  # Percentage of positive returns
        
        # Sort by return consistency and mean return
        sorted_assets = sorted(zip(assets, return_consistency, mean_returns), 
                             key=lambda x: (x[1], x[2]), reverse=True)
        
        for i, (asset, consistency, ret) in enumerate(sorted_assets):
            weight = max(0.05, 0.15 - i * 0.02) * (1 - risk_tolerance * 0.5)
            
            suggestion = AllocationSuggestion(
                symbol=asset,
                suggested_weight=weight,
                current_weight=0.0,
                target_weight=weight,
                rebalance_amount=0.0,
                risk_score=1 - consistency,  # Lower risk for more consistent returns
                expected_return=ret,
                reasoning=f"Income allocation: consistent returns ({consistency:.1%} positive days)"
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _suggest_growth_allocation(self, returns_data: pd.DataFrame,
                                 risk_tolerance: float) -> List[AllocationSuggestion]:
        """Suggest growth-focused allocation."""
        suggestions = []
        assets = returns_data.columns
        
        # Growth: focus on high return potential
        mean_returns = returns_data.mean() * 252
        volatilities = returns_data.std() * np.sqrt(252)
        
        # Sort by return potential (high return, moderate volatility)
        growth_scores = mean_returns / (volatilities + 0.01)  # Avoid division by zero
        sorted_assets = sorted(zip(assets, growth_scores, mean_returns), 
                             key=lambda x: x[1], reverse=True)
        
        for i, (asset, growth_score, ret) in enumerate(sorted_assets):
            weight = max(0.05, 0.18 - i * 0.02) * risk_tolerance
            
            suggestion = AllocationSuggestion(
                symbol=asset,
                suggested_weight=weight,
                current_weight=0.0,
                target_weight=weight,
                rebalance_amount=0.0,
                risk_score=1.0,  # Higher risk for growth
                expected_return=ret,
                reasoning=f"Growth allocation: high growth potential (score: {growth_score:.2f})"
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _suggest_value_allocation(self, returns_data: pd.DataFrame,
                                risk_tolerance: float) -> List[AllocationSuggestion]:
        """Suggest value-focused allocation."""
        suggestions = []
        assets = returns_data.columns
        
        # Value: focus on assets with good risk-adjusted returns
        sharpe_ratios = (returns_data.mean() * 252 - self.optimizer.risk_free_rate) / (returns_data.std() * np.sqrt(252))
        mean_returns = returns_data.mean() * 252
        
        # Sort by Sharpe ratio (value = good risk-adjusted returns)
        sorted_assets = sorted(zip(assets, sharpe_ratios, mean_returns), key=lambda x: x[1], reverse=True)
        
        for i, (asset, sharpe, ret) in enumerate(sorted_assets):
            weight = max(0.05, 0.15 - i * 0.02) * (0.7 + risk_tolerance * 0.3)
            
            suggestion = AllocationSuggestion(
                symbol=asset,
                suggested_weight=weight,
                current_weight=0.0,
                target_weight=weight,
                rebalance_amount=0.0,
                risk_score=1/sharpe if sharpe > 0 else 1.0,
                expected_return=ret,
                reasoning=f"Value allocation: strong risk-adjusted returns (Sharpe: {sharpe:.2f})"
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _suggest_momentum_allocation(self, returns_data: pd.DataFrame,
                                   risk_tolerance: float) -> List[AllocationSuggestion]:
        """Suggest momentum-focused allocation."""
        suggestions = []
        assets = returns_data.columns
        
        # Momentum: focus on recent performance
        recent_returns = returns_data.tail(20).mean() * 252  # Last 20 days
        mean_returns = returns_data.mean() * 252
        
        # Sort by recent performance
        sorted_assets = sorted(zip(assets, recent_returns, mean_returns), key=lambda x: x[1], reverse=True)
        
        for i, (asset, recent_ret, avg_ret) in enumerate(sorted_assets):
            weight = max(0.05, 0.20 - i * 0.03) * risk_tolerance
            
            suggestion = AllocationSuggestion(
                symbol=asset,
                suggested_weight=weight,
                current_weight=0.0,
                target_weight=weight,
                rebalance_amount=0.0,
                risk_score=1.0,  # Higher risk for momentum
                expected_return=avg_ret,
                reasoning=f"Momentum allocation: strong recent performance ({recent_ret:.2%})"
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _calculate_portfolio_volatility(self, returns_data: pd.DataFrame,
                                      suggestions: List[AllocationSuggestion]) -> float:
        """Calculate expected portfolio volatility."""
        weights = np.array([s.suggested_weight for s in suggestions])
        cov_matrix = returns_data.cov() * 252
        
        if len(weights) == len(cov_matrix):
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return portfolio_vol
        else:
            return np.average([s.risk_score for s in suggestions], weights=weights)
    
    def suggest_rebalancing(self, current_weights: Dict[str, float],
                           target_weights: Dict[str, float],
                           portfolio_value: float,
                           threshold: float = 0.05) -> Dict[str, Any]:
        """
        Suggest rebalancing trades.
        
        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights
            portfolio_value: Total portfolio value
            threshold: Minimum rebalancing threshold
            
        Returns:
            Dict[str, Any]: Rebalancing suggestions
        """
        rebalancing_trades = {}
        total_rebalance = 0.0
        
        for asset in set(current_weights.keys()) | set(target_weights.keys()):
            current_weight = current_weights.get(asset, 0.0)
            target_weight = target_weights.get(asset, 0.0)
            
            current_value = current_weight * portfolio_value
            target_value = target_weight * portfolio_value
            trade_amount = target_value - current_value
            
            if abs(trade_amount) > threshold * portfolio_value:
                rebalancing_trades[asset] = {
                    'current_weight': current_weight,
                    'target_weight': target_weight,
                    'trade_amount': trade_amount,
                    'trade_percentage': trade_amount / portfolio_value
                }
                total_rebalance += abs(trade_amount)
        
        return {
            'rebalancing_trades': rebalancing_trades,
            'total_rebalance_amount': total_rebalance,
            'rebalancing_needed': len(rebalancing_trades) > 0
        }
    
    def suggest_risk_management(self, returns_data: pd.DataFrame,
                              current_weights: Dict[str, float],
                              risk_tolerance: float) -> Dict[str, Any]:
        """
        Suggest risk management strategies.
        
        Args:
            returns_data: Asset returns data
            current_weights: Current portfolio weights
            risk_tolerance: Risk tolerance level
            
        Returns:
            Dict[str, Any]: Risk management suggestions
        """
        # Calculate current portfolio risk
        portfolio_returns = returns_data.dot([current_weights.get(asset, 0.0) for asset in returns_data.columns])
        current_volatility = portfolio_returns.std() * np.sqrt(252)
        
        # Calculate individual asset risks
        asset_volatilities = returns_data.std() * np.sqrt(252)
        
        # Risk management suggestions
        suggestions = []
        
        # Check for concentration risk
        max_weight = max(current_weights.values()) if current_weights else 0
        if max_weight > 0.25:
            suggestions.append({
                'type': 'concentration_risk',
                'message': f'Reduce concentration in largest position (currently {max_weight:.1%})',
                'priority': 'high'
            })
        
        # Check for high volatility assets
        high_vol_assets = [asset for asset, vol in asset_volatilities.items() 
                          if vol > 0.3 and current_weights.get(asset, 0) > 0.1]
        if high_vol_assets:
            suggestions.append({
                'type': 'volatility_risk',
                'message': f'Consider reducing exposure to high volatility assets: {", ".join(high_vol_assets)}',
                'priority': 'medium'
            })
        
        # Check overall portfolio risk
        if current_volatility > 0.2 * (1 + risk_tolerance):
            suggestions.append({
                'type': 'portfolio_risk',
                'message': f'Portfolio volatility ({current_volatility:.1%}) may be too high for risk tolerance',
                'priority': 'high'
            })
        
        return {
            'current_volatility': current_volatility,
            'risk_suggestions': suggestions,
            'asset_volatilities': asset_volatilities.to_dict()
        }
    
    def generate_portfolio_report(self, returns_data: pd.DataFrame,
                                weights: Dict[str, float],
                                strategy: PortfolioStrategy = PortfolioStrategy.MODERATE) -> Dict[str, Any]:
        """
        Generate comprehensive portfolio report.
        
        Args:
            returns_data: Asset returns data
            weights: Portfolio weights
            strategy: Portfolio strategy
            
        Returns:
            Dict[str, Any]: Comprehensive portfolio report
        """
        # Calculate portfolio metrics
        portfolio_returns = returns_data.dot([weights.get(asset, 0.0) for asset in returns_data.columns])
        
        # Basic metrics
        total_return = (1 + portfolio_returns).prod() - 1
        annualized_return = portfolio_returns.mean() * 252
        annualized_volatility = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = (annualized_return - self.optimizer.risk_free_rate) / annualized_volatility if annualized_volatility > 0 else 0
        
        # Drawdown analysis
        cumulative_returns = (1 + portfolio_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Asset allocation analysis
        allocation_analysis = {}
        for asset, weight in weights.items():
            if weight > 0:
                asset_returns = returns_data[asset]
                asset_annual_return = asset_returns.mean() * 252
                asset_volatility = asset_returns.std() * np.sqrt(252)
                
                allocation_analysis[asset] = {
                    'weight': weight,
                    'annual_return': asset_annual_return,
                    'volatility': asset_volatility,
                    'contribution_to_return': weight * asset_annual_return,
                    'contribution_to_risk': weight * asset_volatility
                }
        
        return {
            'strategy': strategy.value,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'allocation_analysis': allocation_analysis,
            'risk_metrics': {
                'var_95': np.percentile(portfolio_returns, 5),
                'cvar_95': portfolio_returns[portfolio_returns <= np.percentile(portfolio_returns, 5)].mean(),
                'positive_days': (portfolio_returns > 0).mean(),
                'best_day': portfolio_returns.max(),
                'worst_day': portfolio_returns.min()
            }
        }


# Convenience functions
def suggest_portfolio_allocation(returns_data: pd.DataFrame,
                               strategy: PortfolioStrategy = PortfolioStrategy.MODERATE,
                               risk_tolerance: float = 0.5) -> Dict[str, Any]:
    """Suggest portfolio allocation."""
    suggester = PortfolioSuggester()
    return suggester.suggest_portfolio_allocation(returns_data, strategy, risk_tolerance)


def suggest_rebalancing(current_weights: Dict[str, float],
                       target_weights: Dict[str, float],
                       portfolio_value: float,
                       threshold: float = 0.05) -> Dict[str, Any]:
    """Suggest rebalancing trades."""
    suggester = PortfolioSuggester()
    return suggester.suggest_rebalancing(current_weights, target_weights, portfolio_value, threshold)


def suggest_risk_management(returns_data: pd.DataFrame,
                          current_weights: Dict[str, float],
                          risk_tolerance: float) -> Dict[str, Any]:
    """Suggest risk management strategies."""
    suggester = PortfolioSuggester()
    return suggester.suggest_risk_management(returns_data, current_weights, risk_tolerance)


def generate_portfolio_report(returns_data: pd.DataFrame,
                            weights: Dict[str, float],
                            strategy: PortfolioStrategy = PortfolioStrategy.MODERATE) -> Dict[str, Any]:
    """Generate comprehensive portfolio report."""
    suggester = PortfolioSuggester()
    return suggester.generate_portfolio_report(returns_data, weights, strategy) 