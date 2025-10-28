# finance_tools/stocks/analysis/indicators/implementations/atr.py
from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
from ..base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
from ..registry import registry
from ta.volatility import AverageTrueRange


class ATRIndicator(BaseIndicator):
    """ATR (Average True Range) indicator"""
    
    def __init__(self):
        registry.register(self)
    
    def get_id(self) -> str:
        return "atr"
    
    def get_name(self) -> str:
        return "ATR"
    
    def get_description(self) -> str:
        return "Average True Range (Volatility)"
    
    def get_required_columns(self) -> List[str]:
        return ['close', 'high', 'low']
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'window': {'type': 'integer', 'default': 14, 'min': 5, 'max': 50}
        }
    
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        params = config.parameters
        window = int(params.get('window', 14))
        
        if 'high' not in df.columns or 'low' not in df.columns:
            return df
        
        series = df[column].astype(float)
        high_col = df['high']
        low_col = df['low']
        
        atr = AverageTrueRange(high=high_col, low=low_col, close=series, window=window, fillna=False)
        
        result = df.copy()
        result[f"{column}_atr"] = atr.average_true_range()
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        last_row = df.iloc[-1]
        col_name = f"{column}_atr"
        val = last_row.get(col_name)
        
        snapshot = {}
        if pd.notnull(val):
            snapshot[col_name] = float(val)
        
        return IndicatorSnapshot(values=snapshot)
    
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        if config.weight <= 0:
            return None
        
        last_row = df.iloc[-1]
        atr = last_row.get(f"{column}_atr")
        price = last_row.get(column)
        
        if pd.isnull(atr) or not price or price == 0:
            return None
        
        # Lower ATR percentage means less volatility (better for bullish)
        atr_pct = float(atr) / float(price)
        raw = -atr_pct  # Inverted: lower volatility = positive contribution
        contribution = raw * config.weight

        # Detailed calculation steps
        params = config.parameters
        window = int(params.get('window', 14))

        calculation_details = [
            f"ATR Volatility Score Calculation (Window: {window}):",
            "",
            f"Step 1: Calculate ATR as percentage of price",
            f"        ATR Value = {float(atr):.2f}",
            f"        Current Price = {float(price):.2f}",
            f"        ATR % = ATR / Price × 100",
            f"        = {float(atr):.2f} / {float(price):.2f} × 100",
            f"        = {atr_pct*100:.2f}%",
            "",
            f"Step 2: Convert to score (lower volatility = positive)",
            f"        Raw Score = -ATR%",
            f"        = -{atr_pct:.4f}",
            f"        = {raw:+.4f}",
            "",
            f"Step 3: Final Contribution = Raw Score × Weight",
            f"        = {raw:+.4f} × {config.weight:.2f}",
            f"        = {contribution:+.4f}",
            "",
            f"Note: Negative ATR% means lower volatility (bullish)",
        ]

        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=f"ATR: {float(atr):.2f} ({atr_pct*100:.2f}% of price)",
            calculation_details=calculation_details
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        last_row = df.iloc[-1]
        atr = last_row.get(f"{column}_atr")
        price = last_row.get(column)
        
        lines = []
        lines.append("📊 ATR Analysis:")
        
        if pd.isnull(atr) or not price:
            lines.append("  ⚠️ Insufficient data")
            return lines
        
        atr_val = float(atr)
        atr_pct = (atr_val / float(price) * 100) if price != 0 else 0.0
        
        lines.append(f"  ATR: {atr_val:.2f} ({atr_pct:.2f}% of price)")
        lines.append("  Volatility indicator - Lower is better for entries")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['measures_volatility']


# Instantiate to register
_ = ATRIndicator()

