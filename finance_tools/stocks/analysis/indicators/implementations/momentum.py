# finance_tools/stocks/analysis/indicators/implementations/momentum.py
from __future__ import annotations

from typing import Dict, List, Optional, Any, Sequence
import pandas as pd
from ..base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
from ..registry import registry


class MomentumIndicator(BaseIndicator):
    """Momentum indicator"""
    
    def __init__(self):
        registry.register(self)
    
    def get_id(self) -> str:
        return "momentum"
    
    def get_name(self) -> str:
        return "Momentum"
    
    def get_description(self) -> str:
        return "Price momentum over multiple periods"
    
    def get_required_columns(self) -> List[str]:
        return ['close']
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'windows': {
                'type': 'array',
                'default': [30, 60, 90, 180, 360],
                'items': {'type': 'integer'}
            }
        }
    
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        params = config.parameters
        windows: Sequence[int] = params.get("windows", [30, 60, 90, 180, 360])
        
        series = df[column].astype(float)
        result = df.copy()
        
        if "date" in result.columns and len(result.index) > 0:
            dt = pd.to_datetime(result["date"])
            last_idx = result.index[-1]
            last_date = dt.iloc[-1]
            last_price = float(series.iloc[-1]) if pd.notnull(series.iloc[-1]) else None

            def safe_pct(curr, prev):
                if curr is None or prev is None or prev == 0 or pd.isna(prev) or pd.isna(curr):
                    return float("nan")
                return (curr - prev) / prev

            for w in windows:
                pct_col = f"{column}_pct_{w}"
                result[pct_col] = pd.Series([float("nan")] * len(result), index=result.index)
                target_date = last_date - pd.Timedelta(days=int(w))
                mask = dt <= target_date
                if mask.any():
                    prev_price = float(series[mask].iloc[-1])
                    val = safe_pct(last_price, prev_price)
                    result.at[last_idx, pct_col] = val
        else:
            last_idx = result.index[-1]
            for w in windows:
                pct_col = f"{column}_pct_{w}"
                result[pct_col] = pd.Series([float("nan")] * len(result), index=result.index)
                if len(series) > w:
                    prev_price = float(series.iloc[-(w + 1)])
                    curr_price = float(series.iloc[-1])
                    val = (curr_price - prev_price) / prev_price if prev_price != 0 else float("nan")
                    result.at[last_idx, pct_col] = val
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        params = config.parameters
        windows = params.get("windows", [30, 60, 90, 180, 360])
        
        last_row = df.iloc[-1]
        snapshot = {}
        
        for w in windows:
            col_name = f"{column}_pct_{w}"
            val = last_row.get(col_name)
            if pd.notnull(val):
                snapshot[col_name] = float(val)
        
        return IndicatorSnapshot(values=snapshot)
    
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        if config.weight <= 0:
            return None
        
        params = config.parameters
        windows = params.get("windows", [30, 60, 90, 180, 360])
        
        weights = {30: 0.4, 60: 0.3, 90: 0.15, 180: 0.1, 360: 0.05}
        total_w = 0.0
        agg = 0.0
        
        last_row = df.iloc[-1]
        
        for w, wgt in weights.items():
            if w in windows:
                val = last_row.get(f"{column}_pct_{w}")
                if pd.notnull(val):
                    agg += float(val) * wgt
                    total_w += wgt
        
        if total_w == 0:
            return None

        raw = agg / total_w
        contribution = raw * config.weight

        # Detailed calculation steps
        calculation_details = [
            f"Multi-Period Momentum Score Calculation:",
            "",
            "Step 1: Individual Period Returns (with weights):"
        ]

        for w, wgt in sorted(weights.items()):
            if w in windows:
                val = last_row.get(f"{column}_pct_{w}")
                if pd.notnull(val):
                    contribution_val = float(val) * wgt
                    calculation_details.append(f"        {w:3d}-day: {float(val):+.4f} × {wgt:.2f} = {contribution_val:+.4f}")

        calculation_details.extend([
            "",
            f"Step 2: Weighted Average Return",
            f"        Raw Score = sum(weighted returns) / sum(weights)",
            f"        = {agg:+.4f} / {total_w:.2f}",
            f"        = {raw:+.4f}",
            "",
            f"Step 3: Final Contribution = Raw Score × Weight",
            f"        = {raw:+.4f} × {config.weight:.2f}",
            f"        = {contribution:+.4f}"
        ])

        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=f"Momentum: weighted average",
            calculation_details=calculation_details
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        params = config.parameters
        windows = params.get("windows", [30, 60, 90, 180, 360])
        
        lines = []
        lines.append("📊 Momentum Analysis:")
        
        last_row = df.iloc[-1]
        has_data = False
        
        for w in windows:
            col_name = f"{column}_pct_{w}"
            val = last_row.get(col_name)
            if pd.notnull(val):
                pct_val = float(val) * 100
                lines.append(f"  {w}d: {pct_val:+.2f}%")
                has_data = True
        
        if not has_data:
            lines.append("  ⚠️ Insufficient data")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['measures_price_momentum']


# Instantiate to register
_ = MomentumIndicator()

