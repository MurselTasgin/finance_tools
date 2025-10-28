# finance_tools/analysis/indicators/implementations/common/rsi.py
"""
RSI (Relative Strength Index) indicator - Universal for both stocks and ETFs.

RSI measures the speed and magnitude of price changes, making it universal
for any asset type with a price column (close for stocks, price for ETFs).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
from ta.momentum import RSIIndicator

from finance_tools.analysis.indicators.base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
from finance_tools.analysis.indicators.registry import registry


class RSIIndicatorImpl(BaseIndicator):
    """RSI indicator - works for both stocks and ETFs"""
    
    def __init__(self):
        registry.register(self)
    
    def get_id(self) -> str:
        return "rsi"
    
    def get_name(self) -> str:
        return "RSI (Relative Strength Index)"
    
    def get_description(self) -> str:
        return "Measures the speed and magnitude of price changes. Values >70 indicate overbought, <30 indicate oversold."
    
    def get_required_columns(self) -> List[str]:
        # Works with either 'close' (stocks) or 'price' (ETFs)
        return ['close', 'price']
    
    def get_asset_types(self) -> List[str]:
        """RSI works for both asset types"""
        return ['stock', 'etf']
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'window': {
                'type': 'integer',
                'default': 14,
                'min': 2,
                'max': 50,
                'description': 'RSI calculation period'
            }
        }
    
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        """Calculate RSI indicator"""
        params = config.parameters
        window = int(params.get('window', 14))
        
        # Convert to float and drop NaN
        series = df[column].astype(float).dropna()
        
        if len(series) < window + 1:
            # Not enough data
            result = df.copy()
            result[f"{column}_rsi_{window}"] = pd.Series([float('nan')] * len(df), index=df.index)
            return result
        
        # Calculate RSI using ta library
        rsi_indicator = RSIIndicator(close=series, window=window)
        rsi_values = rsi_indicator.rsi()
        
        # Match indices to original DataFrame
        result = df.copy()
        result[f"{column}_rsi_{window}"] = rsi_values.reindex(df.index)
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        """Extract RSI value"""
        params = config.parameters
        window = int(params.get('window', 14))
        
        last_row = df.iloc[-1]
        col_name = f"{column}_rsi_{window}"
        val = last_row.get(col_name)
        
        snapshot = {}
        if pd.notnull(val):
            snapshot[col_name] = float(val)
        
        return IndicatorSnapshot(values=snapshot)
    
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        """Calculate RSI score"""
        if config.weight <= 0:
            return None
        
        params = config.parameters
        window = int(params.get('window', 14))
        
        last_row = df.iloc[-1]
        col_name = f"{column}_rsi_{window}"
        rsi_value = last_row.get(col_name)
        
        if pd.isnull(rsi_value):
            return None
        
        rsi_value = float(rsi_value)
        
        # Score based on distance from neutral (50)
        # RSI > 50: positive, RSI < 50: negative
        # Normalize to [-1, 1] range
        raw = (rsi_value - 50) / 50
        contribution = raw * config.weight
        
        calculation_details = [
            f"RSI({window}) = {rsi_value:.2f}",
            "",
            f"Step 1: RSI Normalization = (RSI - 50) / 50",
            f"        = ({rsi_value:.2f} - 50) / 50",
            f"        = {raw:.4f}",
            "",
            f"Step 2: Final Contribution = Raw Score × Weight",
            f"        = {raw:.4f} × {config.weight:.2f}",
            f"        = {contribution:.4f}"
        ]
        
        explanation = f"RSI: {rsi_value:.1f} ({'Overbought' if rsi_value > 70 else 'Oversold' if rsi_value < 30 else 'Neutral'})"
        
        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=explanation,
            calculation_details=calculation_details
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        """Generate RSI explanation"""
        params = config.parameters
        window = int(params.get('window', 14))
        
        last_row = df.iloc[-1]
        col_name = f"{column}_rsi_{window}"
        rsi_value = last_row.get(col_name)
        
        lines = []
        lines.append(f"📊 RSI({window}) Analysis:")
        
        if pd.isnull(rsi_value):
            lines.append("  ⚠️ Insufficient data for RSI calculation")
            return lines
        
        rsi_value = float(rsi_value)
        
        # Status
        if rsi_value > 70:
            lines.append(f"  🔴 OVERBOUGHT: RSI = {rsi_value:.1f} (Potential sell signal)")
        elif rsi_value < 30:
            lines.append(f"  🟢 OVERSOLD: RSI = {rsi_value:.1f} (Potential buy signal)")
        else:
            lines.append(f"  ⚪ NEUTRAL: RSI = {rsi_value:.1f}")
        
        # Strength
        if rsi_value > 80:
            lines.append("  💪 Very strong overbought condition")
        elif rsi_value < 20:
            lines.append("  💪 Very strong oversold condition")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['provides_buy_signal', 'provides_sell_signal']
    
    def get_suggestions(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[str]:
        """Return buy/sell/hold suggestion based on RSI"""
        params = config.parameters
        window = int(params.get('window', 14))
        
        last_row = df.iloc[-1]
        col_name = f"{column}_rsi_{window}"
        rsi_value = last_row.get(col_name)
        
        if pd.isnull(rsi_value):
            return None
        
        rsi_value = float(rsi_value)
        
        if rsi_value < 30:
            return "buy"
        elif rsi_value > 70:
            return "sell"
        else:
            return "hold"


# Instantiate to register
_ = RSIIndicatorImpl()
