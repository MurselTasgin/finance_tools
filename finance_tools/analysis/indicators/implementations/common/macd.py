# finance_tools/analysis/indicators/implementations/common/macd.py
"""
MACD (Moving Average Convergence Divergence) indicator - Universal for both stocks and ETFs.

MACD is a trend-following momentum indicator that uses only price data,
making it universal for any asset type.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
from ta.trend import MACD

from finance_tools.analysis.indicators.base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
from finance_tools.analysis.indicators.registry import registry


class MACDIndicatorImpl(BaseIndicator):
    """MACD indicator - works for both stocks and ETFs"""
    
    def __init__(self):
        registry.register(self)
    
    def get_id(self) -> str:
        return "macd"
    
    def get_name(self) -> str:
        return "MACD (Moving Average Convergence Divergence)"
    
    def get_description(self) -> str:
        return "Trend-following momentum indicator showing relationship between two moving averages of price"
    
    def get_required_columns(self) -> List[str]:
        # Works with either 'close' (stocks) or 'price' (ETFs)
        return ['close', 'price']
    
    def get_asset_types(self) -> List[str]:
        """MACD works for both asset types"""
        return ['stock', 'etf']
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'window_fast': {
                'type': 'integer',
                'default': 12,
                'min': 3,
                'max': 50,
                'description': 'Fast EMA period'
            },
            'window_slow': {
                'type': 'integer',
                'default': 26,
                'min': 5,
                'max': 100,
                'description': 'Slow EMA period'
            },
            'window_signal': {
                'type': 'integer',
                'default': 9,
                'min': 3,
                'max': 30,
                'description': 'Signal line EMA period'
            }
        }
    
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        """Calculate MACD indicator"""
        params = config.parameters
        window_fast = int(params.get('window_fast', 12))
        window_slow = int(params.get('window_slow', 26))
        window_signal = int(params.get('window_signal', 9))
        
        # Convert to float
        series = df[column].astype(float).dropna()
        
        if len(series) < window_slow + window_signal:
            # Not enough data
            result = df.copy()
            result[f"{column}_macd_{window_fast}_{window_slow}"] = pd.Series([float('nan')] * len(df), index=df.index)
            result[f"{column}_macd_signal_{window_signal}"] = pd.Series([float('nan')] * len(df), index=df.index)
            result[f"{column}_macd_histogram"] = pd.Series([float('nan')] * len(df), index=df.index)
            return result
        
        # Calculate MACD using ta library
        macd_indicator = MACD(
            close=series,
            window_slow=window_slow,
            window_fast=window_fast,
            window_sign=window_signal
        )
        
        macd_line = macd_indicator.macd()
        signal_line = macd_indicator.macd_signal()
        histogram = macd_indicator.macd_diff()
        
        # Match indices to original DataFrame
        result = df.copy()
        result[f"{column}_macd_{window_fast}_{window_slow}"] = macd_line.reindex(df.index)
        result[f"{column}_macd_signal_{window_signal}"] = signal_line.reindex(df.index)
        result[f"{column}_macd_histogram"] = histogram.reindex(df.index)
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        """Extract MACD values"""
        params = config.parameters
        window_fast = int(params.get('window_fast', 12))
        window_slow = int(params.get('window_slow', 26))
        window_signal = int(params.get('window_signal', 9))
        
        last_row = df.iloc[-1]
        snapshot = {}
        
        macd_val = last_row.get(f"{column}_macd_{window_fast}_{window_slow}")
        signal_val = last_row.get(f"{column}_macd_signal_{window_signal}")
        hist_val = last_row.get(f"{column}_macd_histogram")
        
        if pd.notnull(macd_val):
            snapshot[f"{column}_macd_{window_fast}_{window_slow}"] = float(macd_val)
        if pd.notnull(signal_val):
            snapshot[f"{column}_macd_signal_{window_signal}"] = float(signal_val)
        if pd.notnull(hist_val):
            snapshot[f"{column}_macd_histogram"] = float(hist_val)
        
        return IndicatorSnapshot(values=snapshot)
    
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        """Calculate MACD score based on histogram"""
        if config.weight <= 0:
            return None
        
        params = config.parameters
        window_fast = int(params.get('window_fast', 12))
        window_slow = int(params.get('window_slow', 26))
        window_signal = int(params.get('window_signal', 9))
        
        last_row = df.iloc[-1]
        price_val = last_row.get(column)
        hist_col = f"{column}_macd_histogram"
        hist_val = last_row.get(hist_col)
        
        if any(pd.isnull(v) for v in [hist_val, price_val]):
            return None
        
        hist_val = float(hist_val)
        price_val = float(price_val)
        if price_val == 0:
            return None
        
        # Normalize histogram relative to price (histogram is usually much smaller).
        # Clamp to a reasonable range to avoid overweighting tiny differences.
        normalized_hist = hist_val / price_val
        normalized_hist = max(-0.1, min(0.1, normalized_hist))
        raw = normalized_hist
        contribution = raw * config.weight
        
        macd_val = last_row.get(f"{column}_macd_{window_fast}_{window_slow}")
        signal_val = last_row.get(f"{column}_macd_signal_{window_signal}")
        
        if any(pd.isnull(v) for v in [macd_val, signal_val]):
            return None
        
        macd_val = float(macd_val)
        signal_val = float(signal_val)
        
        calculation_details = [
            f"MACD({window_fast},{window_slow},{window_signal})",
            f"  MACD Line: {macd_val:.4f}",
            f"  Signal Line: {signal_val:.4f}",
            f"  Histogram: {hist_val:.4f}",
            "",
            f"Step 1: Normalize Histogram = Histogram / Price",
            f"        = {hist_val:.4f} / {price_val:.2f}",
            f"        = {hist_val / price_val:.6f}",
            "",
            f"Step 2: Final Contribution = Raw Score × Weight",
            f"        = {raw:.4f} × {config.weight:.2f}",
            f"        = {contribution:.4f}"
        ]
        
        trend = "BULLISH" if hist_val > 0 else "BEARISH"
        explanation = f"MACD Histogram: {hist_val:.4f} ({trend})"
        
        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=explanation,
            calculation_details=calculation_details
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        """Generate MACD explanation"""
        params = config.parameters
        window_fast = int(params.get('window_fast', 12))
        window_slow = int(params.get('window_slow', 26))
        window_signal = int(params.get('window_signal', 9))
        
        last_row = df.iloc[-1]
        
        macd_val = last_row.get(f"{column}_macd_{window_fast}_{window_slow}")
        signal_val = last_row.get(f"{column}_macd_signal_{window_signal}")
        hist_val = last_row.get(f"{column}_macd_histogram")
        
        lines = []
        lines.append(f"📊 MACD({window_fast},{window_slow},{window_signal}) Analysis:")
        
        if any(pd.isnull([macd_val, signal_val, hist_val])):
            lines.append("  ⚠️ Insufficient data for MACD calculation")
            return lines
        
        # MACD vs Signal
        if macd_val > signal_val:
            lines.append(f"  📈 BULLISH: MACD Line ({macd_val:.4f}) > Signal ({signal_val:.4f})")
        else:
            lines.append(f"  📉 BEARISH: MACD Line ({macd_val:.4f}) < Signal ({signal_val:.4f})")
        
        # Histogram
        if hist_val > 0:
            lines.append(f"  ✅ Positive Histogram: {hist_val:.4f} (Momentum increasing)")
        else:
            lines.append(f"  ❌ Negative Histogram: {hist_val:.4f} (Momentum decreasing)")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['provides_buy_signal', 'provides_sell_signal', 'provides_trend_direction']
    
    def get_suggestions(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[str]:
        """Return buy/sell suggestion based on MACD crossover"""
        params = config.parameters
        window_fast = int(params.get('window_fast', 12))
        window_slow = int(params.get('window_slow', 26))
        window_signal = int(params.get('window_signal', 9))
        
        last_row = df.iloc[-1]
        macd_val = last_row.get(f"{column}_macd_{window_fast}_{window_slow}")
        signal_val = last_row.get(f"{column}_macd_signal_{window_signal}")
        
        if pd.isnull(macd_val) or pd.isnull(signal_val):
            return None
        
        if macd_val > signal_val:
            return "buy"
        elif macd_val < signal_val:
            return "sell"
        else:
            return "hold"


# Instantiate to register
_ = MACDIndicatorImpl()
