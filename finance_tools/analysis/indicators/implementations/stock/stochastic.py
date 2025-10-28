# finance_tools/analysis/indicators/implementations/stock/stochastic.py
from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
from ta.momentum import StochasticOscillator

from finance_tools.analysis.indicators.base import (
    BaseIndicator,
    IndicatorConfig,
    IndicatorSnapshot,
    IndicatorScore,
)
from finance_tools.analysis.indicators.registry import registry


class StochasticIndicator(BaseIndicator):
    """Stochastic Oscillator"""
    
    def __init__(self):
        registry.register(self)
    
    def get_id(self) -> str:
        return "stochastic"
    
    def get_name(self) -> str:
        return "Stochastic"
    
    def get_description(self) -> str:
        return "Stochastic Oscillator"
    
    def get_required_columns(self) -> List[str]:
        return ['close', 'high', 'low']
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'k_period': {'type': 'integer', 'default': 14, 'min': 5, 'max': 50},
            'd_period': {'type': 'integer', 'default': 3, 'min': 1, 'max': 20}
        }
    
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        params = config.parameters
        k_period = int(params.get('k_period', 14))
        d_period = int(params.get('d_period', 3))
        
        if 'high' not in df.columns or 'low' not in df.columns:
            return df
        
        series = df[column].astype(float)
        high_col = df['high']
        low_col = df['low']
        
        stoch = StochasticOscillator(high=high_col, low=low_col, close=series, window=k_period, smooth_window=d_period, fillna=False)
        
        result = df.copy()
        result[f"{column}_stoch_k"] = stoch.stoch()
        result[f"{column}_stoch_d"] = stoch.stoch_signal()
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        last_row = df.iloc[-1]
        snapshot = {}
        
        for col_suffix in ['stoch_k', 'stoch_d']:
            col_name = f"{column}_{col_suffix}"
            val = last_row.get(col_name)
            if pd.notnull(val):
                snapshot[col_name] = float(val)
        
        return IndicatorSnapshot(values=snapshot)
    
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        if config.weight <= 0:
            return None
        
        last_row = df.iloc[-1]
        stoch_k = last_row.get(f"{column}_stoch_k")
        
        if pd.isnull(stoch_k):
            return None
        
        stoch_val = float(stoch_k)

        if stoch_val > 80:
            raw = -0.15  # Overbought
            interpretation = "Overbought (> 80)"
        elif stoch_val < 20:
            raw = 0.15  # Oversold
            interpretation = "Oversold (< 20)"
        elif stoch_val > 50:
            raw = 0.05  # Bullish
            interpretation = "Bullish (50-80)"
        else:
            raw = -0.05  # Bearish
            interpretation = "Bearish (20-50)"

        contribution = raw * config.weight

        explanation = f"Stochastic K: {stoch_val:.1f}"

        # Detailed calculation steps
        params = config.parameters
        k_period = int(params.get('k_period', 14))
        d_period = int(params.get('d_period', 3))

        calculation_details = [
            f"Stochastic Oscillator Score Calculation (%K period={k_period}, %D period={d_period}):",
            "",
            f"Step 1: Current %K Value = {stoch_val:.2f}",
            f"        Interpretation: {interpretation}",
            "",
            f"Step 2: Assign score based on level",
            f"        %K > 80 (Overbought): -0.15",
            f"        %K < 20 (Oversold): +0.15",
            f"        %K 50-80 (Bullish): +0.05",
            f"        %K 20-50 (Bearish): -0.05",
            f"        Raw Score = {raw:+.4f}",
            "",
            f"Step 3: Final Contribution = Raw Score × Weight",
            f"        = {raw:+.4f} × {config.weight:.2f}",
            f"        = {contribution:+.4f}",
            "",
            f"Note: < 20 = oversold (buy signal), > 80 = overbought (sell signal)"
        ]

        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=explanation,
            calculation_details=calculation_details
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        last_row = df.iloc[-1]
        stoch_k = last_row.get(f"{column}_stoch_k")
        stoch_d = last_row.get(f"{column}_stoch_d")
        
        lines = []
        lines.append("📊 Stochastic Analysis:")
        
        if not all(pd.notnull([stoch_k, stoch_d])):
            lines.append("  ⚠️ Insufficient data")
            return lines
        
        stoch_k_val = float(stoch_k)
        stoch_d_val = float(stoch_d)
        
        if stoch_k_val > 80:
            lines.append(f"  🔻 OVERBOUGHT: Stochastic K ({stoch_k_val:.1f}) > 80 - Strong SELL signal")
        elif stoch_k_val < 20:
            lines.append(f"  🚀 OVERSOLD: Stochastic K ({stoch_k_val:.1f}) < 20 - Strong BUY signal")
        elif stoch_k_val > stoch_d_val:
            lines.append(f"  📈 BULLISH: K ({stoch_k_val:.1f}) above D ({stoch_d_val:.1f})")
        else:
            lines.append(f"  📉 BEARISH: K ({stoch_k_val:.1f}) below D ({stoch_d_val:.1f})")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['provides_buy_signal', 'provides_sell_signal', 'detects_overbought_oversold']


# Instantiate to register
_ = StochasticIndicator()
