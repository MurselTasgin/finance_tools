# finance_tools/analysis/indicators/implementations/stock/volume.py
from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd

from finance_tools.analysis.indicators.base import (
    BaseIndicator,
    IndicatorConfig,
    IndicatorSnapshot,
    IndicatorScore,
)
from finance_tools.analysis.indicators.registry import registry


class VolumeIndicator(BaseIndicator):
    """Volume Analysis indicator"""
    
    def __init__(self):
        registry.register(self)
    
    def get_id(self) -> str:
        return "volume"
    
    def get_name(self) -> str:
        return "Volume Analysis"
    
    def get_description(self) -> str:
        return "On-Balance Volume and Volume SMA"
    
    def get_required_columns(self) -> List[str]:
        return ['close', 'volume']
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'window': {'type': 'integer', 'default': 20, 'min': 5, 'max': 100}
        }
    
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        params = config.parameters
        window = int(params.get('window', 20))
        
        if 'volume' not in df.columns:
            return df
        
        series = df[column].astype(float)
        volume_col = df['volume']
        
        # Volume SMA
        volume_sma = volume_col.rolling(window=window).mean()
        
        result = df.copy()
        result[f"volume_sma_{window}"] = volume_sma
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        params = config.parameters
        window = int(params.get('window', 20))
        
        last_row = df.iloc[-1]
        col_name = f"volume_sma_{window}"
        val = last_row.get(col_name)
        
        snapshot = {}
        if pd.notnull(val):
            snapshot[col_name] = float(val)
        
        return IndicatorSnapshot(values=snapshot)
    
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        if config.weight <= 0:
            return None
        
        params = config.parameters
        window = int(params.get('window', 20))
        
        last_row = df.iloc[-1]
        volume = last_row.get('volume')
        volume_sma = last_row.get(f"volume_sma_{window}")
        
        if pd.isnull(volume) or pd.isnull(volume_sma) or volume_sma == 0:
            return None
        
        volume_ratio = float(volume) / float(volume_sma)
        pct_change = (volume_ratio - 1.0) * 100

        if volume_ratio > 1.5:
            raw = 0.1  # High volume
            interpretation = "High volume (> 1.5x avg)"
        elif volume_ratio > 1.2:
            raw = 0.05  # Above average
            interpretation = "Above average (1.2-1.5x avg)"
        elif volume_ratio < 0.9:
            raw = -0.05  # Low volume
            interpretation = "Low volume (< 0.9x avg)"
        else:
            raw = 0.0  # Normal
            interpretation = "Normal volume (0.9-1.2x avg)"

        contribution = raw * config.weight

        # Detailed calculation steps
        calculation_details = [
            f"Volume Analysis Score Calculation (Window: {window}):",
            "",
            f"Step 1: Volume Metrics",
            f"        Current Volume = {float(volume):.0f}",
            f"        {window}-day Avg Volume = {float(volume_sma):.0f}",
            f"        Volume Ratio = Current / Avg",
            f"        = {float(volume):.0f} / {float(volume_sma):.0f}",
            f"        = {volume_ratio:.2f}x ({pct_change:+.1f}%)",
            "",
            f"Step 2: Assign score based on ratio",
            f"        Ratio > 1.5: High volume → +0.10",
            f"        Ratio 1.2-1.5: Above average → +0.05",
            f"        Ratio 0.9-1.2: Normal → 0.00",
            f"        Ratio < 0.9: Low volume → -0.05",
            f"        Interpretation: {interpretation}",
            f"        Raw Score = {raw:+.4f}",
            "",
            f"Step 3: Final Contribution = Raw Score × Weight",
            f"        = {raw:+.4f} × {config.weight:.2f}",
            f"        = {contribution:+.4f}",
            "",
            f"Note: Higher volume typically confirms price movements"
        ]

        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=f"Volume: {pct_change:+.1f}% vs SMA",
            calculation_details=calculation_details
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        params = config.parameters
        window = int(params.get('window', 20))
        
        last_row = df.iloc[-1]
        volume = last_row.get('volume')
        volume_sma = last_row.get(f"volume_sma_{window}")
        
        lines = []
        lines.append("📊 Volume Analysis:")
        
        if pd.isnull(volume) or pd.isnull(volume_sma) or volume_sma == 0:
            lines.append("  ⚠️ Insufficient data")
            return lines
        
        volume_ratio = float(volume) / float(volume_sma)
        pct_change = (volume_ratio - 1.0) * 100
        
        if volume_ratio > 1.5:
            lines.append(f"  ✅ HIGH VOLUME: {pct_change:+.1f}% vs SMA - Strong conviction")
        elif volume_ratio > 1.2:
            lines.append(f"  📈 ABOVE AVERAGE: {pct_change:+.1f}% vs SMA")
        elif volume_ratio < 0.9:
            lines.append(f"  ⚠️ LOW VOLUME: {pct_change:+.1f}% vs SMA - Weak conviction")
        else:
            lines.append(f"  ➖ NORMAL: {pct_change:+.1f}% vs SMA")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['measures_volume_trend']


# Instantiate to register
_ = VolumeIndicator()
