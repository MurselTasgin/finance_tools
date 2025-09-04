# finance_tools/analysis/suggestions/suggestion_types.py
"""
Suggestion types and enums for trading recommendations.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime


class SuggestionType(Enum):
    """Types of trading suggestions."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"
    WAIT = "wait"


class SuggestionStrength(Enum):
    """Suggestion strength levels."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class RiskLevel(Enum):
    """Risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class RiskAssessment:
    """Risk assessment for a trading suggestion."""
    risk_level: RiskLevel
    volatility: float
    drawdown_potential: float
    correlation_with_market: float
    liquidity_risk: float
    concentration_risk: float
    description: str
    mitigation_strategies: List[str] = None
    
    def __post_init__(self):
        if self.mitigation_strategies is None:
            self.mitigation_strategies = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert risk assessment to dictionary."""
        return {
            'risk_level': self.risk_level.value,
            'volatility': self.volatility,
            'drawdown_potential': self.drawdown_potential,
            'correlation_with_market': self.correlation_with_market,
            'liquidity_risk': self.liquidity_risk,
            'concentration_risk': self.concentration_risk,
            'description': self.description,
            'mitigation_strategies': self.mitigation_strategies
        }


@dataclass
class PositionRecommendation:
    """Position size and entry/exit recommendations."""
    suggested_position_size: float  # Percentage of portfolio
    entry_price: float
    stop_loss: float
    take_profit: float
    time_horizon: str  # "short_term", "medium_term", "long_term"
    entry_strategy: str
    exit_strategy: str
    risk_reward_ratio: float
    max_loss: float
    potential_gain: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position recommendation to dictionary."""
        return {
            'suggested_position_size': self.suggested_position_size,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'time_horizon': self.time_horizon,
            'entry_strategy': self.entry_strategy,
            'exit_strategy': self.exit_strategy,
            'risk_reward_ratio': self.risk_reward_ratio,
            'max_loss': self.max_loss,
            'potential_gain': self.potential_gain
        }


@dataclass
class TradingSuggestion:
    """Represents a trading suggestion."""
    suggestion_type: SuggestionType
    strength: SuggestionStrength
    symbol: str
    current_price: float
    timestamp: datetime
    confidence: float  # 0.0 to 1.0
    reasoning: List[str]
    technical_indicators: Dict[str, Any]
    patterns_detected: List[str]
    signals_generated: List[str]
    risk_assessment: RiskAssessment
    position_recommendation: PositionRecommendation
    market_context: Dict[str, Any] = None
    portfolio_context: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.market_context is None:
            self.market_context = {}
        if self.portfolio_context is None:
            self.portfolio_context = {}
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trading suggestion to dictionary."""
        return {
            'suggestion_type': self.suggestion_type.value,
            'strength': self.strength.value,
            'symbol': self.symbol,
            'current_price': self.current_price,
            'timestamp': self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp),
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'technical_indicators': self.technical_indicators,
            'patterns_detected': self.patterns_detected,
            'signals_generated': self.signals_generated,
            'risk_assessment': self.risk_assessment.to_dict(),
            'position_recommendation': self.position_recommendation.to_dict(),
            'market_context': self.market_context,
            'portfolio_context': self.portfolio_context,
            'metadata': self.metadata
        }


@dataclass
class SuggestionResult:
    """Container for suggestion results."""
    suggestions: List[TradingSuggestion]
    summary: Dict[str, Any]
    market_analysis: Dict[str, Any]
    portfolio_analysis: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def get_buy_suggestions(self) -> List[TradingSuggestion]:
        """Get all buy suggestions."""
        return [s for s in self.suggestions if s.suggestion_type in [SuggestionType.BUY, SuggestionType.STRONG_BUY]]
    
    def get_sell_suggestions(self) -> List[TradingSuggestion]:
        """Get all sell suggestions."""
        return [s for s in self.suggestions if s.suggestion_type in [SuggestionType.SELL, SuggestionType.STRONG_SELL]]
    
    def get_strongest_suggestion(self) -> Optional[TradingSuggestion]:
        """Get the strongest suggestion."""
        if not self.suggestions:
            return None
        
        # Sort by confidence and strength
        strength_order = {
            SuggestionStrength.WEAK: 1,
            SuggestionStrength.MODERATE: 2,
            SuggestionStrength.STRONG: 3,
            SuggestionStrength.VERY_STRONG: 4
        }
        
        return max(self.suggestions, key=lambda s: (s.confidence, strength_order.get(s.strength, 0)))
    
    def get_low_risk_suggestions(self) -> List[TradingSuggestion]:
        """Get suggestions with low risk."""
        return [s for s in self.suggestions if s.risk_assessment.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert suggestion result to dictionary."""
        return {
            'suggestions': [s.to_dict() for s in self.suggestions],
            'summary': self.summary,
            'market_analysis': self.market_analysis,
            'portfolio_analysis': self.portfolio_analysis,
            'metadata': self.metadata
        } 