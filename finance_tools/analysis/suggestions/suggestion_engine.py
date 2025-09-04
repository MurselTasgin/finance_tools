# finance_tools/analysis/suggestions/suggestion_engine.py
"""
Suggestion engine for generating trading recommendations.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .suggestion_types import (
    TradingSuggestion, SuggestionResult, RiskAssessment, PositionRecommendation,
    SuggestionType, SuggestionStrength, RiskLevel
)
from ..signals import SignalCalculator
from ..patterns import PatternDetector
from ..analysis import TechnicalAnalysis

logger = logging.getLogger(__name__)


class SuggestionEngine:
    """
    Main suggestion engine for generating trading recommendations.
    """
    
    def __init__(self):
        """Initialize the suggestion engine."""
        self.signal_calculator = SignalCalculator()
        self.pattern_detector = PatternDetector()
        self.technical_analysis = TechnicalAnalysis()
    
    def generate_suggestions(self, data: pd.DataFrame, 
                           symbol: str,
                           portfolio_context: Dict[str, Any] = None,
                           market_context: Dict[str, Any] = None) -> SuggestionResult:
        """
        Generate comprehensive trading suggestions.
        
        Args:
            data: OHLCV DataFrame
            symbol: Stock symbol
            portfolio_context: Portfolio information (optional)
            market_context: Market conditions (optional)
            
        Returns:
            SuggestionResult: Container with all suggestions and analysis
        """
        suggestions = []
        
        # Calculate technical indicators and signals
        signals_result = self.signal_calculator.calculate_all_signals(data)
        indicators = self.technical_analysis.calculate_all_indicators(data)
        
        # Detect patterns
        patterns_result = self.pattern_detector.detect_all_patterns(data)
        
        # Generate individual suggestions
        current_price = data['close'].iloc[-1]
        timestamp = data.index[-1]
        
        # Buy suggestions
        buy_suggestions = self._generate_buy_suggestions(
            data, symbol, current_price, timestamp, signals_result, patterns_result, indicators
        )
        suggestions.extend(buy_suggestions)
        
        # Sell suggestions
        sell_suggestions = self._generate_sell_suggestions(
            data, symbol, current_price, timestamp, signals_result, patterns_result, indicators
        )
        suggestions.extend(sell_suggestions)
        
        # Hold suggestions
        hold_suggestions = self._generate_hold_suggestions(
            data, symbol, current_price, timestamp, signals_result, patterns_result, indicators
        )
        suggestions.extend(hold_suggestions)
        
        # Create summary and analysis
        summary = self._create_suggestion_summary(suggestions)
        market_analysis = self._analyze_market_context(data, market_context)
        portfolio_analysis = self._analyze_portfolio_context(suggestions, portfolio_context)
        
        return SuggestionResult(
            suggestions=suggestions,
            summary=summary,
            market_analysis=market_analysis,
            portfolio_analysis=portfolio_analysis
        )
    
    def _generate_buy_suggestions(self, data: pd.DataFrame, symbol: str, 
                                current_price: float, timestamp: datetime,
                                signals_result, patterns_result, indicators: Dict[str, Any]) -> List[TradingSuggestion]:
        """Generate buy suggestions based on signals and patterns."""
        suggestions = []
        
        # Get buy signals
        buy_signals = signals_result.get_buy_signals()
        bullish_patterns = patterns_result.get_bullish_patterns()
        
        # Strong buy conditions
        strong_buy_reasons = []
        technical_indicators = {}
        
        # Check for strong buy signals
        if len(buy_signals) >= 3:  # Multiple buy signals
            strong_buy_reasons.append("Multiple buy signals detected")
        
        # Check for golden cross
        ema_50 = indicators.get('ema_50', pd.Series())
        ema_200 = indicators.get('ema_200', pd.Series())
        if not ema_50.empty and not ema_200.empty:
            if ema_50.iloc[-1] > ema_200.iloc[-1] and ema_50.iloc[-2] <= ema_200.iloc[-2]:
                strong_buy_reasons.append("Golden Cross detected (EMA 50 crossed above EMA 200)")
        
        # Check RSI oversold
        rsi = indicators.get('rsi', pd.Series())
        if not rsi.empty and rsi.iloc[-1] < 30:
            strong_buy_reasons.append(f"RSI oversold ({rsi.iloc[-1]:.1f})")
        
        # Check for bullish patterns
        if bullish_patterns:
            pattern_names = [p.pattern_name for p in bullish_patterns]
            strong_buy_reasons.append(f"Bullish patterns detected: {', '.join(pattern_names)}")
        
        # Check for breakout patterns
        breakout_patterns = patterns_result.get_breakout_patterns()
        bullish_breakouts = [p for p in breakout_patterns if p.direction.value == 'bullish']
        if bullish_breakouts:
            strong_buy_reasons.append("Bullish breakout patterns detected")
        
        # Generate strong buy suggestion if conditions are met
        if len(strong_buy_reasons) >= 2:
            risk_assessment = self._assess_risk(data, symbol, "buy")
            position_recommendation = self._calculate_position_recommendation(
                data, current_price, "buy", risk_assessment
            )
            
            suggestion = TradingSuggestion(
                suggestion_type=SuggestionType.STRONG_BUY,
                strength=SuggestionStrength.VERY_STRONG,
                symbol=symbol,
                current_price=current_price,
                timestamp=timestamp,
                confidence=0.9,
                reasoning=strong_buy_reasons,
                technical_indicators=self._extract_key_indicators(indicators),
                patterns_detected=[p.pattern_name for p in bullish_patterns],
                signals_generated=[s.signal_type.value for s in buy_signals],
                risk_assessment=risk_assessment,
                position_recommendation=position_recommendation
            )
            suggestions.append(suggestion)
        
        # Regular buy conditions
        if len(buy_signals) >= 1:
            buy_reasons = []
            
            # Check for individual buy signals
            for signal in buy_signals:
                if signal.signal_type.value == 'ema_crossover':
                    buy_reasons.append("EMA crossover signal")
                elif signal.signal_type.value == 'rsi_signal':
                    buy_reasons.append("RSI signal")
                elif signal.signal_type.value == 'macd_signal':
                    buy_reasons.append("MACD signal")
                elif signal.signal_type.value == 'bollinger_bands_signal':
                    buy_reasons.append("Bollinger Bands signal")
            
            if buy_reasons:
                risk_assessment = self._assess_risk(data, symbol, "buy")
                position_recommendation = self._calculate_position_recommendation(
                    data, current_price, "buy", risk_assessment
                )
                
                suggestion = TradingSuggestion(
                    suggestion_type=SuggestionType.BUY,
                    strength=SuggestionStrength.STRONG,
                    symbol=symbol,
                    current_price=current_price,
                    timestamp=timestamp,
                    confidence=0.7,
                    reasoning=buy_reasons,
                    technical_indicators=self._extract_key_indicators(indicators),
                    patterns_detected=[p.pattern_name for p in bullish_patterns],
                    signals_generated=[s.signal_type.value for s in buy_signals],
                    risk_assessment=risk_assessment,
                    position_recommendation=position_recommendation
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_sell_suggestions(self, data: pd.DataFrame, symbol: str,
                                 current_price: float, timestamp: datetime,
                                 signals_result, patterns_result, indicators: Dict[str, Any]) -> List[TradingSuggestion]:
        """Generate sell suggestions based on signals and patterns."""
        suggestions = []
        
        # Get sell signals
        sell_signals = signals_result.get_sell_signals()
        bearish_patterns = patterns_result.get_bearish_patterns()
        
        # Strong sell conditions
        strong_sell_reasons = []
        
        # Check for strong sell signals
        if len(sell_signals) >= 3:  # Multiple sell signals
            strong_sell_reasons.append("Multiple sell signals detected")
        
        # Check for death cross
        ema_50 = indicators.get('ema_50', pd.Series())
        ema_200 = indicators.get('ema_200', pd.Series())
        if not ema_50.empty and not ema_200.empty:
            if ema_50.iloc[-1] < ema_200.iloc[-1] and ema_50.iloc[-2] >= ema_200.iloc[-2]:
                strong_sell_reasons.append("Death Cross detected (EMA 50 crossed below EMA 200)")
        
        # Check RSI overbought
        rsi = indicators.get('rsi', pd.Series())
        if not rsi.empty and rsi.iloc[-1] > 70:
            strong_sell_reasons.append(f"RSI overbought ({rsi.iloc[-1]:.1f})")
        
        # Check for bearish patterns
        if bearish_patterns:
            pattern_names = [p.pattern_name for p in bearish_patterns]
            strong_sell_reasons.append(f"Bearish patterns detected: {', '.join(pattern_names)}")
        
        # Generate strong sell suggestion if conditions are met
        if len(strong_sell_reasons) >= 2:
            risk_assessment = self._assess_risk(data, symbol, "sell")
            position_recommendation = self._calculate_position_recommendation(
                data, current_price, "sell", risk_assessment
            )
            
            suggestion = TradingSuggestion(
                suggestion_type=SuggestionType.STRONG_SELL,
                strength=SuggestionStrength.VERY_STRONG,
                symbol=symbol,
                current_price=current_price,
                timestamp=timestamp,
                confidence=0.9,
                reasoning=strong_sell_reasons,
                technical_indicators=self._extract_key_indicators(indicators),
                patterns_detected=[p.pattern_name for p in bearish_patterns],
                signals_generated=[s.signal_type.value for s in sell_signals],
                risk_assessment=risk_assessment,
                position_recommendation=position_recommendation
            )
            suggestions.append(suggestion)
        
        # Regular sell conditions
        if len(sell_signals) >= 1:
            sell_reasons = []
            
            for signal in sell_signals:
                if signal.signal_type.value == 'ema_crossover':
                    sell_reasons.append("EMA crossover signal")
                elif signal.signal_type.value == 'rsi_signal':
                    sell_reasons.append("RSI signal")
                elif signal.signal_type.value == 'macd_signal':
                    sell_reasons.append("MACD signal")
                elif signal.signal_type.value == 'bollinger_bands_signal':
                    sell_reasons.append("Bollinger Bands signal")
            
            if sell_reasons:
                risk_assessment = self._assess_risk(data, symbol, "sell")
                position_recommendation = self._calculate_position_recommendation(
                    data, current_price, "sell", risk_assessment
                )
                
                suggestion = TradingSuggestion(
                    suggestion_type=SuggestionType.SELL,
                    strength=SuggestionStrength.STRONG,
                    symbol=symbol,
                    current_price=current_price,
                    timestamp=timestamp,
                    confidence=0.7,
                    reasoning=sell_reasons,
                    technical_indicators=self._extract_key_indicators(indicators),
                    patterns_detected=[p.pattern_name for p in bearish_patterns],
                    signals_generated=[s.signal_type.value for s in sell_signals],
                    risk_assessment=risk_assessment,
                    position_recommendation=position_recommendation
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_hold_suggestions(self, data: pd.DataFrame, symbol: str,
                                 current_price: float, timestamp: datetime,
                                 signals_result, patterns_result, indicators: Dict[str, Any]) -> List[TradingSuggestion]:
        """Generate hold suggestions when no clear buy/sell signals."""
        suggestions = []
        
        # Check if there are conflicting signals or neutral conditions
        buy_signals = signals_result.get_buy_signals()
        sell_signals = signals_result.get_sell_signals()
        
        # Hold if conflicting signals or no clear direction
        if (len(buy_signals) == 0 and len(sell_signals) == 0) or \
           (len(buy_signals) > 0 and len(sell_signals) > 0):
            
            hold_reasons = []
            
            if len(buy_signals) == 0 and len(sell_signals) == 0:
                hold_reasons.append("No clear trading signals detected")
            else:
                hold_reasons.append("Conflicting signals detected - wait for clearer direction")
            
            # Check for neutral patterns
            neutral_patterns = [p for p in patterns_result.patterns if p.direction.value == 'neutral']
            if neutral_patterns:
                hold_reasons.append("Neutral patterns detected")
            
            # Check RSI neutral
            rsi = indicators.get('rsi', pd.Series())
            if not rsi.empty and 30 <= rsi.iloc[-1] <= 70:
                hold_reasons.append("RSI in neutral territory")
            
            risk_assessment = self._assess_risk(data, symbol, "hold")
            position_recommendation = self._calculate_position_recommendation(
                data, current_price, "hold", risk_assessment
            )
            
            suggestion = TradingSuggestion(
                suggestion_type=SuggestionType.HOLD,
                strength=SuggestionStrength.MODERATE,
                symbol=symbol,
                current_price=current_price,
                timestamp=timestamp,
                confidence=0.6,
                reasoning=hold_reasons,
                technical_indicators=self._extract_key_indicators(indicators),
                patterns_detected=[p.pattern_name for p in neutral_patterns],
                signals_generated=[],
                risk_assessment=risk_assessment,
                position_recommendation=position_recommendation
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _assess_risk(self, data: pd.DataFrame, symbol: str, action: str) -> RiskAssessment:
        """Assess risk for a trading action."""
        close_prices = data['close']
        volume = data.get('volume', pd.Series(index=data.index, dtype=float))
        
        # Calculate volatility
        returns = close_prices.pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized volatility
        
        # Calculate potential drawdown
        cumulative_max = close_prices.expanding().max()
        drawdown = (close_prices - cumulative_max) / cumulative_max
        max_drawdown = drawdown.min()
        
        # Assess liquidity risk
        avg_volume = volume.mean() if not volume.empty else 0
        liquidity_risk = 1.0 if avg_volume < 1000000 else 0.5 if avg_volume < 5000000 else 0.2
        
        # Determine risk level
        if volatility > 0.4 or max_drawdown < -0.3:
            risk_level = RiskLevel.VERY_HIGH
        elif volatility > 0.25 or max_drawdown < -0.2:
            risk_level = RiskLevel.HIGH
        elif volatility > 0.15 or max_drawdown < -0.1:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Generate mitigation strategies
        mitigation_strategies = []
        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            mitigation_strategies.append("Use smaller position sizes")
            mitigation_strategies.append("Set tighter stop losses")
        if liquidity_risk > 0.5:
            mitigation_strategies.append("Consider market orders for better execution")
        
        return RiskAssessment(
            risk_level=risk_level,
            volatility=volatility,
            drawdown_potential=abs(max_drawdown),
            correlation_with_market=0.5,  # Placeholder - would need market data
            liquidity_risk=liquidity_risk,
            concentration_risk=0.3,  # Placeholder
            description=f"Risk assessment for {action} action on {symbol}",
            mitigation_strategies=mitigation_strategies
        )
    
    def _calculate_position_recommendation(self, data: pd.DataFrame, current_price: float,
                                         action: str, risk_assessment: RiskAssessment) -> PositionRecommendation:
        """Calculate position size and entry/exit recommendations."""
        
        # Calculate ATR for stop loss
        atr = data['high'].rolling(window=14).max() - data['low'].rolling(window=14).min()
        current_atr = atr.iloc[-1] if not atr.empty else current_price * 0.02
        
        # Determine position size based on risk
        if risk_assessment.risk_level == RiskLevel.VERY_HIGH:
            position_size = 0.02  # 2% of portfolio
            stop_loss_multiplier = 1.5
        elif risk_assessment.risk_level == RiskLevel.HIGH:
            position_size = 0.05  # 5% of portfolio
            stop_loss_multiplier = 1.2
        elif risk_assessment.risk_level == RiskLevel.MEDIUM:
            position_size = 0.10  # 10% of portfolio
            stop_loss_multiplier = 1.0
        else:
            position_size = 0.15  # 15% of portfolio
            stop_loss_multiplier = 0.8
        
        # Calculate entry/exit levels
        if action == "buy":
            entry_price = current_price
            stop_loss = current_price - (current_atr * stop_loss_multiplier)
            take_profit = current_price + (current_atr * 2 * stop_loss_multiplier)
        elif action == "sell":
            entry_price = current_price
            stop_loss = current_price + (current_atr * stop_loss_multiplier)
            take_profit = current_price - (current_atr * 2 * stop_loss_multiplier)
        else:  # hold
            entry_price = current_price
            stop_loss = current_price - (current_atr * stop_loss_multiplier)
            take_profit = current_price + (current_atr * stop_loss_multiplier)
        
        # Calculate risk/reward ratio
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        return PositionRecommendation(
            suggested_position_size=position_size,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            time_horizon="medium_term",
            entry_strategy="Market order",
            exit_strategy="Stop loss and take profit",
            risk_reward_ratio=risk_reward_ratio,
            max_loss=risk,
            potential_gain=reward
        )
    
    def _extract_key_indicators(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key indicator values for suggestion."""
        key_indicators = {}
        
        for name, indicator in indicators.items():
            if isinstance(indicator, pd.Series) and not indicator.empty:
                key_indicators[name] = float(indicator.iloc[-1])
        
        return key_indicators
    
    def _create_suggestion_summary(self, suggestions: List[TradingSuggestion]) -> Dict[str, Any]:
        """Create a summary of all suggestions."""
        if not suggestions:
            return {'total_suggestions': 0, 'buy_suggestions': 0, 'sell_suggestions': 0}
        
        buy_suggestions = [s for s in suggestions if s.suggestion_type in [SuggestionType.BUY, SuggestionType.STRONG_BUY]]
        sell_suggestions = [s for s in suggestions if s.suggestion_type in [SuggestionType.SELL, SuggestionType.STRONG_SELL]]
        hold_suggestions = [s for s in suggestions if s.suggestion_type == SuggestionType.HOLD]
        
        # Calculate average confidence
        avg_confidence = sum(s.confidence for s in suggestions) / len(suggestions) if suggestions else 0
        
        return {
            'total_suggestions': len(suggestions),
            'buy_suggestions': len(buy_suggestions),
            'sell_suggestions': len(sell_suggestions),
            'hold_suggestions': len(hold_suggestions),
            'average_confidence': avg_confidence,
            'strongest_suggestion': max(suggestions, key=lambda s: s.confidence).suggestion_type.value if suggestions else None
        }
    
    def _analyze_market_context(self, data: pd.DataFrame, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market context for suggestions."""
        # This would typically include market sentiment, sector analysis, etc.
        return {
            'market_trend': 'neutral',
            'sector_performance': 'neutral',
            'market_volatility': 'medium',
            'economic_conditions': 'stable'
        }
    
    def _analyze_portfolio_context(self, suggestions: List[TradingSuggestion], 
                                 portfolio_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio context for suggestions."""
        # This would typically include portfolio diversification, risk tolerance, etc.
        return {
            'portfolio_diversification': 'adequate',
            'risk_tolerance': 'medium',
            'current_exposure': 'balanced',
            'cash_position': 'sufficient'
        }


# Convenience functions
def generate_trading_suggestions(data: pd.DataFrame, symbol: str,
                               portfolio_context: Dict[str, Any] = None,
                               market_context: Dict[str, Any] = None) -> SuggestionResult:
    """Generate trading suggestions for a symbol."""
    engine = SuggestionEngine()
    return engine.generate_suggestions(data, symbol, portfolio_context, market_context)


def analyze_risk_reward(data: pd.DataFrame, symbol: str) -> Dict[str, float]:
    """Analyze risk/reward ratio for a trade."""
    # Calculate basic risk metrics for the symbol
    close_prices = data['close']
    high_prices = data['high']
    low_prices = data['low']
    
    # Calculate volatility and potential moves
    returns = close_prices.pct_change().dropna()
    volatility = returns.std() * np.sqrt(252)  # Annualized volatility
    
    current_price = close_prices.iloc[-1]
    atr = (high_prices.rolling(window=14).max() - low_prices.rolling(window=14).min()).iloc[-1]
    
    # Estimate potential upside and downside based on recent price action
    recent_high = high_prices.tail(20).max()
    recent_low = low_prices.tail(20).min()
    
    potential_upside = ((recent_high - current_price) / current_price) * 100
    potential_downside = ((current_price - recent_low) / current_price) * 100
    
    # Calculate risk/reward ratio
    risk_reward_ratio = potential_upside / potential_downside if potential_downside > 0 else 1.0
    
    # Estimate probability of success based on technical indicators
    probability_of_success = 0.5  # Base probability
    
    # Adjust probability based on trend
    ema_20 = close_prices.ewm(span=20).mean().iloc[-1]
    ema_50 = close_prices.ewm(span=50).mean().iloc[-1]
    if ema_20 > ema_50:
        probability_of_success += 0.1  # Slight bullish bias
    elif ema_20 < ema_50:
        probability_of_success -= 0.1  # Slight bearish bias
    
    # Clamp probability between 0.1 and 0.9
    probability_of_success = max(0.1, min(0.9, probability_of_success))
    
    return {
        'potential_upside': potential_upside,
        'potential_downside': potential_downside,
        'risk_reward_ratio': risk_reward_ratio,
        'probability_of_success': probability_of_success,
        'volatility': volatility * 100,  # As percentage
        'atr': atr
    }


def calculate_position_size(data: pd.DataFrame, symbol: str, risk_tolerance: float = 0.5) -> Dict[str, float]:
    """Calculate position size based on risk management."""
    # Calculate metrics for position sizing
    close_prices = data['close']
    returns = close_prices.pct_change().dropna()
    volatility = returns.std() * np.sqrt(252)  # Annualized volatility
    
    current_price = close_prices.iloc[-1]
    
    # Calculate ATR for risk assessment
    high_prices = data['high']
    low_prices = data['low']
    atr = (high_prices.rolling(window=14).max() - low_prices.rolling(window=14).min()).iloc[-1]
    
    # Base position size based on volatility and risk tolerance
    # Higher volatility = smaller position size
    base_position_size = risk_tolerance / volatility if volatility > 0 else 0.1
    
    # Clamp position size between 1% and 20% of portfolio
    position_size = max(0.01, min(0.20, base_position_size))
    
    # Maximum position size should be conservative
    max_position_size = position_size * 1.5
    max_position_size = min(0.25, max_position_size)
    
    # Risk per trade as percentage
    risk_per_trade = (atr / current_price) * position_size * 100
    
    return {
        'position_size': position_size * 100,  # As percentage
        'max_position_size': max_position_size * 100,  # As percentage
        'risk_per_trade': risk_per_trade,
        'volatility': volatility * 100,
        'atr_ratio': (atr / current_price) * 100
    }


def generate_portfolio_suggestions(portfolio_data: Dict[str, pd.DataFrame],
                                 portfolio_context: Dict[str, Any] = None) -> Dict[str, SuggestionResult]:
    """Generate suggestions for multiple symbols in a portfolio."""
    engine = SuggestionEngine()
    results = {}
    
    for symbol, data in portfolio_data.items():
        try:
            result = engine.generate_suggestions(data, symbol, portfolio_context)
            results[symbol] = result
        except Exception as e:
            logger.error(f"Error generating suggestions for {symbol}: {e}")
    
    return results 