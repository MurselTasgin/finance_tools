# finance_tools/stocks/analysis/indicators/implementations/rsi.py
from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
from ..base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
from ..registry import registry
from ta.momentum import RSIIndicator


class RSIIndicatorImpl(BaseIndicator):
    """RSI indicator"""
    
    def __init__(self):
        registry.register(self)
    
    def get_id(self) -> str:
        return "rsi"
    
    def get_name(self) -> str:
        return "RSI"
    
    def get_description(self) -> str:
        return "Relative Strength Index"
    
    def get_required_columns(self) -> List[str]:
        return ['close']
    
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
        lower = float(params.get('lower', 30.0))
        upper = float(params.get('upper', 70.0))
        
        last_row = df.iloc[-1]
        rsi = last_row.get(f"{column}_rsi_{window}")
        
        if pd.isnull(rsi):
            return None
        
        # Normalize RSI to [-1, 1] range
        # RSI 0-50 -> negative, 50-100 -> positive
        raw = (float(rsi) - 50.0) / 50.0
        contribution = raw * config.weight

        if rsi < lower:
            explanation = f"RSI {rsi:.1f} - OVERSOLD"
            signal_type = "OVERSOLD (BUY)"
        elif rsi > upper:
            explanation = f"RSI {rsi:.1f} - OVERBOUGHT"
            signal_type = "OVERBOUGHT (SELL)"
        else:
            explanation = f"RSI {rsi:.1f} - NEUTRAL"
            signal_type = "NEUTRAL"

        # Detailed calculation steps
        calculation_details = [
            f"RSI Score Calculation (Window: {window}):",
            "",
            f"Step 1: Current RSI Value = {float(rsi):.2f}",
            f"        Thresholds: Oversold < {lower}, Overbought > {upper}",
            f"        Signal: {signal_type}",
            "",
            f"Step 2: Normalize to [-1, +1] range",
            f"        Raw Score = (RSI - 50) / 50",
            f"        = ({float(rsi):.2f} - 50) / 50",
            f"        = {raw:+.4f}",
            "",
            f"Step 3: Final Contribution = Raw Score × Weight",
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
        params = config.parameters
        window = int(params.get('window', 14))
        lower = float(params.get('lower', 30.0))
        upper = float(params.get('upper', 70.0))
        
        last_row = df.iloc[-1]
        rsi = last_row.get(f"{column}_rsi_{window}")
        
        lines = []
        lines.append(f"📊 RSI Analysis:")
        
        if pd.isnull(rsi):
            lines.append("  ⚠️ Insufficient data")
            return lines
        
        rsi_val = float(rsi)
        
        if rsi_val < lower:
            lines.append(f"  🚀 OVERSOLD: RSI ({rsi_val:.1f}) < {lower} - Strong BUY signal")
        elif rsi_val > upper:
            lines.append(f"  🔻 OVERBOUGHT: RSI ({rsi_val:.1f}) > {upper} - Strong SELL signal")
        elif rsi_val > 50:
            lines.append(f"  📈 BULLISH: RSI ({rsi_val:.1f}) > 50 - Positive momentum")
        else:
            lines.append(f"  📉 BEARISH: RSI ({rsi_val:.1f}) < 50 - Negative momentum")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['provides_buy_signal', 'provides_sell_signal', 'detects_overbought_oversold']


# Instantiate to register
_ = RSIIndicatorImpl()

