# finance_tools/analysis/indicators/implementations/stock/sentiment.py
from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

from finance_tools.analysis.indicators.base import (
    BaseIndicator,
    IndicatorConfig,
    IndicatorSnapshot,
    IndicatorScore,
)
from finance_tools.analysis.indicators.registry import registry


class SentimentIndicator(BaseIndicator):
    """
    Market Sentiment Indicator - Analyzes multiple factors to gauge bullish/bearish sentiment

    Components:
    1. Higher Highs/Lower Lows Pattern: Tracks price structure trends
    2. Volume Surge Analysis: Detects unusual volume activity
    3. Breakthrough Detection: Identifies support/resistance breaks
    4. Price Momentum: Multi-period rate of change analysis
    5. Volume-Price Correlation: Validates price moves with volume
    6. Range Expansion/Contraction: Identifies breakout vs consolidation phases
    """

    def __init__(self):
        # Register on instantiation
        registry.register(self)

    def get_id(self) -> str:
        return "sentiment"

    def get_name(self) -> str:
        return "Market Sentiment"

    def get_description(self) -> str:
        return "Analyzes price patterns, volume, breakthroughs, and momentum to determine market sentiment"

    def get_required_columns(self) -> List[str]:
        return ['high', 'low', 'close', 'volume']

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'lookback_period': {
                'type': 'integer',
                'default': 20,
                'min': 5,
                'max': 100,
                'description': 'Period for pattern analysis'
            },
            'volume_threshold': {
                'type': 'float',
                'default': 1.5,
                'min': 1.0,
                'max': 5.0,
                'description': 'Volume surge multiplier threshold'
            },
            'momentum_periods': {
                'type': 'array',
                'items': {'type': 'integer'},
                'default': [5, 10, 20],
                'description': 'Periods for momentum calculation'
            },
            'breakthrough_sensitivity': {
                'type': 'float',
                'default': 0.02,
                'min': 0.01,
                'max': 0.10,
                'description': 'Sensitivity for breakthrough detection (as percentage)'
            }
        }

    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        """Calculate all sentiment components"""
        params = config.parameters
        lookback = int(params.get('lookback_period', 20))
        volume_threshold = float(params.get('volume_threshold', 1.5))
        momentum_periods = params.get('momentum_periods', [5, 10, 20])
        breakthrough_sens = float(params.get('breakthrough_sensitivity', 0.02))

        result = df.copy()

        # 1. Higher Highs / Lower Lows Pattern
        result = self._calculate_price_structure(result, lookback)

        # 2. Volume Analysis
        result = self._calculate_volume_surge(result, lookback, volume_threshold)

        # 3. Breakthrough Detection
        result = self._calculate_breakthroughs(result, lookback, breakthrough_sens)

        # 4. Price Momentum
        result = self._calculate_momentum(result, column, momentum_periods)

        # 5. Volume-Price Correlation
        result = self._calculate_volume_price_correlation(result, column, lookback)

        # 6. Range Expansion/Contraction
        result = self._calculate_range_expansion(result, lookback)

        # 7. Composite Sentiment Score (-1 to +1)
        result = self._calculate_composite_sentiment(result)

        return result

    def _calculate_price_structure(self, df: pd.DataFrame, lookback: int) -> pd.DataFrame:
        """Detect higher highs/lower lows pattern"""
        df = df.copy()

        # Rolling highs and lows
        rolling_high = df['high'].rolling(window=lookback, min_periods=1).max()
        rolling_low = df['low'].rolling(window=lookback, min_periods=1).min()

        # Current high/low vs previous period
        prev_rolling_high = rolling_high.shift(1)
        prev_rolling_low = rolling_low.shift(1)

        # Higher high: current rolling high > previous rolling high
        higher_high = (rolling_high > prev_rolling_high).astype(int)
        # Higher low: current rolling low > previous rolling low
        higher_low = (rolling_low > prev_rolling_low).astype(int)

        # Lower high
        lower_high = (rolling_high < prev_rolling_high).astype(int)
        # Lower low
        lower_low = (rolling_low < prev_rolling_low).astype(int)

        df['sentiment_higher_high'] = higher_high
        df['sentiment_higher_low'] = higher_low
        df['sentiment_lower_high'] = lower_high
        df['sentiment_lower_low'] = lower_low

        # Pattern score: +1 for bullish (HH+HL), -1 for bearish (LH+LL)
        bullish_pattern = (higher_high & higher_low).astype(int)
        bearish_pattern = (lower_high & lower_low).astype(int)
        df['sentiment_pattern_score'] = bullish_pattern - bearish_pattern

        return df

    def _calculate_volume_surge(self, df: pd.DataFrame, lookback: int, threshold: float) -> pd.DataFrame:
        """Detect volume surges"""
        df = df.copy()

        # Average volume over lookback period
        avg_volume = df['volume'].rolling(window=lookback, min_periods=1).mean()

        # Volume surge: current volume > threshold * average volume
        volume_surge = (df['volume'] > (avg_volume * threshold)).astype(int)

        df['sentiment_avg_volume'] = avg_volume
        df['sentiment_volume_surge'] = volume_surge
        df['sentiment_volume_ratio'] = df['volume'] / avg_volume.replace(0, np.nan)

        return df

    def _calculate_breakthroughs(self, df: pd.DataFrame, lookback: int, sensitivity: float) -> pd.DataFrame:
        """Detect support/resistance breakthroughs"""
        df = df.copy()

        # Resistance: highest high in lookback period (excluding current)
        resistance = df['high'].shift(1).rolling(window=lookback, min_periods=1).max()
        # Support: lowest low in lookback period (excluding current)
        support = df['low'].shift(1).rolling(window=lookback, min_periods=1).min()

        # Breakthrough detection with sensitivity
        resistance_break = (df['close'] > resistance * (1 + sensitivity)).astype(int)
        support_break = (df['close'] < support * (1 - sensitivity)).astype(int)

        df['sentiment_resistance'] = resistance
        df['sentiment_support'] = support
        df['sentiment_resistance_break'] = resistance_break
        df['sentiment_support_break'] = support_break

        # Breakthrough score: +1 for resistance break, -1 for support break
        df['sentiment_breakthrough_score'] = resistance_break - support_break

        return df

    def _calculate_momentum(self, df: pd.DataFrame, column: str, periods: List[int]) -> pd.DataFrame:
        """Calculate multi-period momentum"""
        df = df.copy()

        momentum_scores = []

        for period in periods:
            # Rate of change
            roc = ((df[column] - df[column].shift(period)) / df[column].shift(period).replace(0, np.nan)) * 100
            df[f'sentiment_momentum_{period}'] = roc

            # Normalize to -1 to +1 range (clip at +/- 20%)
            normalized = roc.clip(-20, 20) / 20
            momentum_scores.append(normalized)

        # Average momentum across all periods
        if momentum_scores:
            df['sentiment_avg_momentum'] = pd.concat(momentum_scores, axis=1).mean(axis=1)
        else:
            df['sentiment_avg_momentum'] = 0

        return df

    def _calculate_volume_price_correlation(self, df: pd.DataFrame, column: str, lookback: int) -> pd.DataFrame:
        """Calculate correlation between volume and price changes"""
        df = df.copy()

        # Price change
        price_change = df[column].diff()
        # Volume change
        volume_change = df['volume'].diff()

        # Rolling correlation
        correlation = price_change.rolling(window=lookback, min_periods=5).corr(volume_change)

        df['sentiment_volume_price_corr'] = correlation

        # Positive correlation with volume surge is bullish
        # Negative correlation with volume surge is bearish
        avg_volume = df['volume'].rolling(window=lookback, min_periods=1).mean()
        volume_above_avg = (df['volume'] > avg_volume).astype(int)

        # Correlation score
        correlation_score = correlation.fillna(0) * volume_above_avg
        df['sentiment_correlation_score'] = correlation_score

        return df

    def _calculate_range_expansion(self, df: pd.DataFrame, lookback: int) -> pd.DataFrame:
        """Detect range expansion (breakout) vs contraction (consolidation)"""
        df = df.copy()

        # True Range
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # Average True Range
        atr = true_range.rolling(window=lookback, min_periods=1).mean()

        # Range expansion: current TR > ATR
        range_expansion = (true_range > atr).astype(int)

        df['sentiment_atr'] = atr
        df['sentiment_true_range'] = true_range
        df['sentiment_range_expansion'] = range_expansion

        # Expansion score: +1 for expansion with upward price, -1 for expansion with downward price
        price_up = (df['close'] > df['close'].shift(1)).astype(int)
        price_down = (df['close'] < df['close'].shift(1)).astype(int)

        df['sentiment_expansion_score'] = (range_expansion * price_up) - (range_expansion * price_down)

        return df

    def _calculate_composite_sentiment(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate final composite sentiment score"""
        df = df.copy()

        # Weight each component
        components = {
            'sentiment_pattern_score': 0.25,           # Price structure
            'sentiment_breakthrough_score': 0.20,      # Support/resistance breaks
            'sentiment_avg_momentum': 0.20,            # Price momentum
            'sentiment_correlation_score': 0.15,       # Volume-price correlation
            'sentiment_expansion_score': 0.20          # Range expansion
        }

        # Calculate weighted sentiment
        sentiment_score = pd.Series(0.0, index=df.index)

        for component, weight in components.items():
            if component in df.columns:
                # Normalize component to -1 to +1 if not already
                component_values = df[component].fillna(0)
                if component == 'sentiment_avg_momentum':
                    # Already normalized
                    normalized = component_values
                elif component == 'sentiment_correlation_score':
                    # Already normalized
                    normalized = component_values.clip(-1, 1)
                else:
                    # Discrete scores (-1, 0, 1)
                    normalized = component_values

                sentiment_score += normalized * weight

        # Clip final score to -1 to +1 range
        df['sentiment_score'] = sentiment_score.clip(-1, 1)

        # Sentiment strength (absolute value)
        df['sentiment_strength'] = np.abs(df['sentiment_score'])

        # Sentiment direction
        df['sentiment_direction'] = pd.cut(
            df['sentiment_score'],
            bins=[-np.inf, -0.3, 0.3, np.inf],
            labels=['bearish', 'neutral', 'bullish']
        )

        return df

    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        """Extract current sentiment values"""
        last_row = df.iloc[-1]

        # Extract values with proper type handling
        sentiment_score_val = last_row.get('sentiment_score', 0)
        sentiment_strength_val = last_row.get('sentiment_strength', 0)
        pattern_score_val = last_row.get('sentiment_pattern_score', 0)
        breakthrough_score_val = last_row.get('sentiment_breakthrough_score', 0)
        avg_momentum_val = last_row.get('sentiment_avg_momentum', 0)
        volume_ratio_val = last_row.get('sentiment_volume_ratio', 1)
        range_expansion_val = last_row.get('sentiment_range_expansion', 0)

        # Convert to appropriate types, handling NaN values
        snapshot = {
            'sentiment_score': float(sentiment_score_val) if pd.notnull(sentiment_score_val) else 0.0,
            'sentiment_strength': float(sentiment_strength_val) if pd.notnull(sentiment_strength_val) else 0.0,
            'pattern_score': float(pattern_score_val) if pd.notnull(pattern_score_val) else 0.0,
            'breakthrough_score': float(breakthrough_score_val) if pd.notnull(breakthrough_score_val) else 0.0,
            'avg_momentum': float(avg_momentum_val) if pd.notnull(avg_momentum_val) else 0.0,
            'volume_ratio': float(volume_ratio_val) if pd.notnull(volume_ratio_val) else 1.0,
            'range_expansion': float(range_expansion_val) if pd.notnull(range_expansion_val) else 0.0,
        }

        return IndicatorSnapshot(values=snapshot)

    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        """Calculate score contribution from sentiment"""
        if config.weight <= 0:
            return None

        last_row = df.iloc[-1]
        sentiment_score = last_row.get('sentiment_score', 0)

        if pd.isnull(sentiment_score):
            sentiment_score = 0

        # Raw score is the sentiment score (-1 to +1)
        raw = float(sentiment_score)
        contribution = raw * config.weight

        explanation = f"Sentiment: {raw:.3f}, Strength: {last_row.get('sentiment_strength', 0):.3f}"

        # Detailed calculation steps
        pattern_score = float(last_row.get('sentiment_pattern_score', 0)) if pd.notnull(last_row.get('sentiment_pattern_score', 0)) else 0.0
        breakthrough_score = float(last_row.get('sentiment_breakthrough_score', 0)) if pd.notnull(last_row.get('sentiment_breakthrough_score', 0)) else 0.0
        avg_momentum = float(last_row.get('sentiment_avg_momentum', 0)) if pd.notnull(last_row.get('sentiment_avg_momentum', 0)) else 0.0
        correlation_score = float(last_row.get('sentiment_correlation_score', 0)) if pd.notnull(last_row.get('sentiment_correlation_score', 0)) else 0.0
        expansion_score = float(last_row.get('sentiment_expansion_score', 0)) if pd.notnull(last_row.get('sentiment_expansion_score', 0)) else 0.0

        calculation_details = [
            "Composite Sentiment Score Calculation:",
            "",
            f"Step 1: Component Scores",
            f"  • Price Pattern Score:       {pattern_score:+.4f} (weight: 0.25)",
            f"  • Breakthrough Score:         {breakthrough_score:+.4f} (weight: 0.20)",
            f"  • Momentum Score:             {avg_momentum:+.4f} (weight: 0.20)",
            f"  • Volume-Price Correlation:   {correlation_score:+.4f} (weight: 0.15)",
            f"  • Range Expansion Score:      {expansion_score:+.4f} (weight: 0.20)",
            "",
            f"Step 2: Weighted Sentiment Score",
            f"        = (Pattern × 0.25) + (Breakthrough × 0.20) + (Momentum × 0.20)",
            f"          + (Correlation × 0.15) + (Expansion × 0.20)",
            f"        = ({pattern_score:+.4f} × 0.25) + ({breakthrough_score:+.4f} × 0.20) + ({avg_momentum:+.4f} × 0.20)",
            f"          + ({correlation_score:+.4f} × 0.15) + ({expansion_score:+.4f} × 0.20)",
            f"        = {raw:+.4f} (clipped to [-1, +1])",
            "",
            f"Step 3: Final Contribution = Sentiment Score × Weight",
            f"        = {raw:+.4f} × {config.weight:.2f}",
            f"        = {contribution:+.4f}"
        ]

        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=explanation,
            calculation_details=calculation_details
        )

    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        """Generate human-readable explanation"""
        last_row = df.iloc[-1]

        sentiment_score = last_row.get('sentiment_score', 0)
        sentiment_strength = last_row.get('sentiment_strength', 0)

        lines = []
        lines.append(f"📊 Market Sentiment Analysis:")

        # Overall sentiment
        if pd.isnull(sentiment_score):
            lines.append("  ⚠️ Insufficient data for sentiment analysis")
            return lines

        sentiment_score = float(sentiment_score)
        sentiment_strength = float(sentiment_strength) if pd.notnull(sentiment_strength) else 0

        # Sentiment emoji and description
        if sentiment_score > 0.5:
            emoji = "🚀"
            desc = "STRONGLY BULLISH"
        elif sentiment_score > 0.2:
            emoji = "📈"
            desc = "BULLISH"
        elif sentiment_score > -0.2:
            emoji = "➖"
            desc = "NEUTRAL"
        elif sentiment_score > -0.5:
            emoji = "📉"
            desc = "BEARISH"
        else:
            emoji = "⚠️"
            desc = "STRONGLY BEARISH"

        lines.append(f"  {emoji} Overall Sentiment: {desc} (Score: {sentiment_score:.3f}, Strength: {sentiment_strength:.3f})")

        # Component breakdown
        lines.append(f"  📋 Component Analysis:")

        # 1. Price Pattern
        pattern_score = last_row.get('sentiment_pattern_score', 0)
        if pattern_score > 0:
            lines.append(f"    ✅ Price Structure: Higher Highs & Higher Lows detected")
        elif pattern_score < 0:
            lines.append(f"    ❌ Price Structure: Lower Highs & Lower Lows detected")
        else:
            lines.append(f"    ➖ Price Structure: Mixed or neutral pattern")

        # 2. Volume
        volume_ratio = last_row.get('sentiment_volume_ratio', 1)
        volume_surge = last_row.get('sentiment_volume_surge', 0)
        if pd.notnull(volume_ratio):
            volume_ratio = float(volume_ratio)
            if volume_surge == 1:
                lines.append(f"    🔊 Volume: SURGE detected ({volume_ratio:.2f}x average)")
            else:
                lines.append(f"    🔉 Volume: Normal ({volume_ratio:.2f}x average)")

        # 3. Breakthroughs
        resistance_break = last_row.get('sentiment_resistance_break', 0)
        support_break = last_row.get('sentiment_support_break', 0)
        if resistance_break == 1:
            lines.append(f"    🚀 Breakthrough: Resistance BROKEN (bullish)")
        elif support_break == 1:
            lines.append(f"    ⚠️ Breakthrough: Support BROKEN (bearish)")
        else:
            lines.append(f"    ➖ Breakthrough: No significant breaks")

        # 4. Momentum
        avg_momentum = last_row.get('sentiment_avg_momentum', 0)
        if pd.notnull(avg_momentum):
            avg_momentum = float(avg_momentum)
            if avg_momentum > 0.3:
                lines.append(f"    📈 Momentum: Strong upward ({avg_momentum:.3f})")
            elif avg_momentum < -0.3:
                lines.append(f"    📉 Momentum: Strong downward ({avg_momentum:.3f})")
            else:
                lines.append(f"    ➖ Momentum: Weak or neutral ({avg_momentum:.3f})")

        # 5. Range Expansion
        range_expansion = last_row.get('sentiment_range_expansion', 0)
        expansion_score = last_row.get('sentiment_expansion_score', 0)
        if range_expansion == 1:
            if expansion_score > 0:
                lines.append(f"    💥 Range: EXPANDING with upward price (breakout)")
            elif expansion_score < 0:
                lines.append(f"    💥 Range: EXPANDING with downward price (breakdown)")
            else:
                lines.append(f"    💥 Range: EXPANDING (unclear direction)")
        else:
            lines.append(f"    📦 Range: Consolidating")

        return lines

    def get_capabilities(self) -> List[str]:
        return [
            'provides_buy_signal',
            'provides_sell_signal',
            'provides_trend_direction',
            'provides_sentiment_analysis',
            'provides_volume_analysis'
        ]

    def get_suggestions(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[str]:
        """Return buy/sell/hold suggestion based on sentiment"""
        last_row = df.iloc[-1]
        sentiment_score = last_row.get('sentiment_score', 0)

        if pd.isnull(sentiment_score):
            return 'hold'

        sentiment_score = float(sentiment_score)

        if sentiment_score > 0.3:
            return 'buy'
        elif sentiment_score < -0.3:
            return 'sell'
        return 'hold'


# Instantiate to register
_ = SentimentIndicator()
