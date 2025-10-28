# finance_tools/stocks/analysis/indicators/implementations/adx.py
from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
from ..base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
from ..registry import registry
from ta.trend import ADXIndicator


class ADXIndicatorImpl(BaseIndicator):
    """ADX (Average Directional Index) indicator"""
    
    def __init__(self):
        registry.register(self)
    
    def get_id(self) -> str:
        return "adx"
    
    def get_name(self) -> str:
        return "ADX"
    
    def get_description(self) -> str:
        return "Average Directional Index (Trend Strength)"
    
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
        
        adx = ADXIndicator(high=high_col, low=low_col, close=series, window=window, fillna=False)
        
        result = df.copy()
        result[f"{column}_adx"] = adx.adx()
        result[f"{column}_adx_plus"] = adx.adx_pos()
        result[f"{column}_adx_minus"] = adx.adx_neg()
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        last_row = df.iloc[-1]
        snapshot = {}
        
        for col_suffix in ['adx', 'adx_plus', 'adx_minus']:
            col_name = f"{column}_{col_suffix}"
            val = last_row.get(col_name)
            if pd.notnull(val):
                snapshot[col_name] = float(val)
        
        return IndicatorSnapshot(values=snapshot)
    
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        if config.weight <= 0:
            return None
        
        last_row = df.iloc[-1]
        adx = last_row.get(f"{column}_adx")
        
        if pd.isnull(adx):
            return None
        
        adx_val = float(adx)

        if adx_val > 25:
            raw = 0.1  # Strong trend
            interpretation = "Strong trend (> 25)"
        elif adx_val > 20:
            raw = 0.05  # Moderate trend
            interpretation = "Moderate trend (20-25)"
        else:
            raw = -0.05  # Weak trend
            interpretation = "Weak trend (< 20)"

        contribution = raw * config.weight

        # Detailed calculation steps
        params = config.parameters
        window = int(params.get('window', 14))

        calculation_details = [
            f"ADX Trend Strength Score Calculation (Window: {window}):",
            "",
            f"Step 1: Current ADX Value = {adx_val:.2f}",
            f"        Interpretation: {interpretation}",
            "",
            f"Step 2: Assign score based on trend strength",
            f"        ADX > 25: Strong trend → +0.10",
            f"        ADX 20-25: Moderate trend → +0.05",
            f"        ADX < 20: Weak trend → -0.05",
            f"        Raw Score = {raw:+.4f}",
            "",
            f"Step 3: Final Contribution = Raw Score × Weight",
            f"        = {raw:+.4f} × {config.weight:.2f}",
            f"        = {contribution:+.4f}",
            "",
            f"Note: ADX > 25 indicates strong trend (bullish or bearish)"
        ]

        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=f"ADX: {adx_val:.1f}",
            calculation_details=calculation_details
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        last_row = df.iloc[-1]
        adx = last_row.get(f"{column}_adx")
        
        lines = []
        lines.append("📊 ADX Analysis:")
        
        if pd.isnull(adx):
            lines.append("  ⚠️ Insufficient data")
            return lines
        
        adx_val = float(adx)
        
        if adx_val > 25:
            lines.append(f"  ✅ STRONG TREND: ADX ({adx_val:.1f}) > 25")
        elif adx_val > 20:
            lines.append(f"  📈 MODERATE TREND: ADX ({adx_val:.1f}) > 20")
        else:
            lines.append(f"  ⚠️ WEAK TREND: ADX ({adx_val:.1f}) < 20")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['measures_trend_strength']


# Instantiate to register
_ = ADXIndicatorImpl()

