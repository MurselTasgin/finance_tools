# finance_tools/stocks/analysis/indicators/implementations/macd.py
from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
from ..base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
from ..registry import registry
from ta.trend import MACD


class MACDIndicator(BaseIndicator):
    """MACD indicator"""
    
    def __init__(self):
        registry.register(self)
    
    def get_id(self) -> str:
        return "macd"
    
    def get_name(self) -> str:
        return "MACD"
    
    def get_description(self) -> str:
        return "Moving Average Convergence Divergence"
    
    def get_required_columns(self) -> List[str]:
        return ['close']
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'window_slow': {'type': 'integer', 'default': 26, 'min': 12, 'max': 100},
            'window_fast': {'type': 'integer', 'default': 12, 'min': 5, 'max': 50},
            'window_sign': {'type': 'integer', 'default': 9, 'min': 3, 'max': 30}
        }
    
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        params = config.parameters
        window_slow = int(params.get('window_slow', 26))
        window_fast = int(params.get('window_fast', 12))
        window_sign = int(params.get('window_sign', 9))
        
        series = df[column].astype(float)
        macd = MACD(close=series, window_slow=window_slow, window_fast=window_fast, window_sign=window_sign, fillna=False)
        
        result = df.copy()
        result[f"{column}_macd"] = macd.macd()
        result[f"{column}_macd_signal"] = macd.macd_signal()
        result[f"{column}_macd_diff"] = macd.macd_diff()
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        last_row = df.iloc[-1]
        snapshot = {}
        
        for col_suffix in ['macd', 'macd_signal', 'macd_diff']:
            col_name = f"{column}_{col_suffix}"
            val = last_row.get(col_name)
            if pd.notnull(val):
                snapshot[col_name] = float(val)
        
        return IndicatorSnapshot(values=snapshot)
    
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        if config.weight <= 0:
            return None
        
        last_row = df.iloc[-1]
        price = last_row.get(column)
        macd = last_row.get(f"{column}_macd")
        macd_signal = last_row.get(f"{column}_macd_signal")
        macd_diff = last_row.get(f"{column}_macd_diff")
        
        if not all(pd.notnull([macd, macd_signal])) or not price or price == 0:
            return None
        
        histogram = float(macd) - float(macd_signal)
        denom = float(price) if price else 1.0
        raw = histogram / denom
        contribution = raw * config.weight

        # Detailed calculation steps
        params = config.parameters
        fast = int(params.get('fast', 12))
        slow = int(params.get('slow', 26))
        signal = int(params.get('signal', 9))

        calculation_details = [
            f"MACD Score Calculation ({fast}/{slow}/{signal}):",
            "",
            f"Step 1: MACD Components",
            f"        MACD Line = {float(macd):.4f}",
            f"        Signal Line = {float(macd_signal):.4f}",
            f"        Histogram = MACD - Signal",
            f"        = {float(macd):.4f} - {float(macd_signal):.4f}",
            f"        = {histogram:+.4f}",
            "",
            f"Step 2: Normalize by price",
            f"        Raw Score = Histogram / Price",
            f"        = {histogram:+.4f} / {float(price):.2f}",
            f"        = {raw:+.6f}",
            "",
            f"Step 3: Final Contribution = Raw Score × Weight",
            f"        = {raw:+.6f} × {config.weight:.2f}",
            f"        = {contribution:+.6f}",
            "",
            f"Note: Positive histogram = bullish, negative = bearish"
        ]

        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=f"MACD histogram: {histogram:.4f}",
            calculation_details=calculation_details
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        last_row = df.iloc[-1]
        macd = last_row.get(f"{column}_macd")
        macd_signal = last_row.get(f"{column}_macd_signal")
        price = last_row.get(column)
        
        lines = []
        lines.append("📊 MACD Analysis:")
        
        if not all(pd.notnull([macd, macd_signal])):
            lines.append("  ⚠️ Insufficient data")
            return lines
        
        histogram = float(macd) - float(macd_signal)
        macd_pct = (histogram / float(price) * 100) if price and price != 0 else 0.0
        macd_above = macd > macd_signal
        
        lines.append(f"  MACD: {float(macd):.4f}, Signal: {float(macd_signal):.4f}")
        lines.append(f"  Histogram: {histogram:+.4f} ({macd_pct:+.2f}% of price)")
        
        if macd_above:
            lines.append("  ✅ BULLISH: MACD above Signal")
        else:
            lines.append("  ❌ BEARISH: MACD below Signal")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['provides_buy_signal', 'provides_sell_signal']


# Instantiate to register
_ = MACDIndicator()

