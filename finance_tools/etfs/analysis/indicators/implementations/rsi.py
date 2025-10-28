# finance_tools/etfs/analysis/indicators/implementations/rsi.py
from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
from ..base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
from ..registry import registry
from ta.momentum import RSIIndicator


class RSIIndicatorImpl(BaseIndicator):
    """RSI indicator for ETFs"""
    
    def __init__(self):
        registry.register(self)
    
    def get_id(self) -> str:
        return "rsi"
    
    def get_name(self) -> str:
        return "RSI"
    
    def get_description(self) -> str:
        return "Relative Strength Index"
    
    def get_required_columns(self) -> List[str]:
        return ['price']
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'window': {'type': 'integer', 'default': 14, 'min': 5, 'max': 50},
            'lower': {'type': 'float', 'default': 30.0, 'min': 0, 'max': 100},
            'upper': {'type': 'float', 'default': 70.0, 'min': 0, 'max': 100}
        }
    
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        params = config.parameters
        window = int(params.get('window', 14))
        
        series = df[column].astype(float)
        rsi = RSIIndicator(close=series, window=window, fillna=False).rsi()
        
        result = df.copy()
        result[f"{column}_rsi_{window}"] = rsi
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
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
        if config.weight <= 0:
            return None
        
        params = config.parameters
        window = int(params.get('window', 14))
        
        last_row = df.iloc[-1]
        col_name = f"{column}_rsi_{window}"
        rsi = last_row.get(col_name)
        
        if pd.isnull(rsi):
            return None
        
        # Score: centered around 50, normalized to -1 to 1
        raw = (float(rsi) - 50.0) / 50.0
        # Clamp to -1 to 1
        raw = max(-1.0, min(1.0, raw))
        contribution = raw * config.weight

        calculation_details = [
            f"RSI Score Calculation:",
            "",
            f"Step 1: RSI Value = {float(rsi):.2f}",
            "",
            f"Step 2: Centered Score = (RSI - 50) / 50",
            f"        = ({float(rsi):.2f} - 50.0) / 50.0",
            f"        = {raw:.4f}",
            "",
            f"Step 3: Final Contribution = Raw Score × Weight",
            f"        = {raw:.4f} × {config.weight:.2f}",
            f"        = {contribution:.4f}",
            "",
            f"Note: RSI > 50 = bullish, RSI < 50 = bearish"
        ]

        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=f"RSI: {float(rsi):.2f}",
            calculation_details=calculation_details
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        params = config.parameters
        window = int(params.get('window', 14))
        lower = float(params.get('lower', 30.0))
        upper = float(params.get('upper', 70.0))
        
        last_row = df.iloc[-1]
        col_name = f"{column}_rsi_{window}"
        rsi = last_row.get(col_name)
        
        lines = []
        lines.append("📊 RSI Analysis:")
        
        if pd.isnull(rsi):
            lines.append("  ⚠️ Insufficient data")
            return lines
        
        rsi_float = float(rsi)
        if rsi_float < lower:
            lines.append(f"  🚀 OVERSOLD: RSI ({rsi_float:.1f}) below {lower} - Strong BUY signal")
        elif rsi_float > upper:
            lines.append(f"  🔻 OVERBOUGHT: RSI ({rsi_float:.1f}) above {upper} - Strong SELL signal")
        elif rsi_float > 50:
            lines.append(f"  📈 BULLISH: RSI ({rsi_float:.1f}) above 50 - Positive momentum")
        else:
            lines.append(f"  📉 BEARISH: RSI ({rsi_float:.1f}) below 50 - Negative momentum")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['provides_buy_signal', 'provides_sell_signal']


# Instantiate to register
_ = RSIIndicatorImpl()

