# finance_tools/etfs/analysis/indicators/implementations/daily_momentum.py
from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
from ..base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
from ..registry import registry


class DailyMomentumIndicator(BaseIndicator):
    """Daily momentum indicator for ETFs - per-day change over different periods"""
    
    def __init__(self):
        registry.register(self)
    
    def get_id(self) -> str:
        return "momentum_daily"
    
    def get_name(self) -> str:
        return "Daily Momentum"
    
    def get_description(self) -> str:
        return "Per-day price momentum over multiple time periods"
    
    def get_required_columns(self) -> List[str]:
        return ['price', 'date']
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'windows': {
                'type': 'array',
                'default': [30, 60, 90, 180, 360],
                'description': 'List of time periods in days'
            }
        }
    
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        """Calculate daily momentum - momentum divided by days"""
        params = config.parameters
        windows = params.get('windows', [30, 60, 90, 180, 360])
        
        result = df.copy()
        
        # Calculate momentum if not already present
        # Replicate momentum calculation inline to avoid circular dependency
        if "date" in result.columns and len(result.index) > 0:
            dt = pd.to_datetime(result["date"])
            last_idx = result.index[-1]
            last_date = dt.iloc[-1]
            series = result[column].astype(float)
            last_price = float(series.iloc[-1]) if pd.notnull(series.iloc[-1]) else None

            def safe_pct(curr: Optional[float], prev: Optional[float]) -> float:
                if curr is None or prev is None or prev == 0 or pd.isna(prev) or pd.isna(curr):
                    return float("nan")
                return (curr - prev) / prev

            for w in windows:
                pct_col = f"{column}_pct_{w}"
                if pct_col not in result.columns or result.at[last_idx, pct_col] is None or pd.isna(result.at[last_idx, pct_col]):
                    result[pct_col] = pd.Series([float("nan")] * len(result), index=result.index)
                    target_date = last_date - pd.Timedelta(days=int(w))
                    mask = dt <= target_date
                    if mask.any():
                        prev_price = float(series[mask].iloc[-1])
                        val = safe_pct(last_price, prev_price)
                        result.at[last_idx, pct_col] = val
        else:
            # Fallback: use row offsets if no date provided
            last_idx = result.index[-1]
            series = result[column].astype(float)
            for w in windows:
                pct_col = f"{column}_pct_{w}"
                if pct_col not in result.columns or result.at[last_idx, pct_col] is None or pd.isna(result.at[last_idx, pct_col]):
                    result[pct_col] = pd.Series([float("nan")] * len(result), index=result.index)
                    if len(series) > w:
                        prev_price = float(series.iloc[-(w + 1)])
                        curr_price = float(series.iloc[-1])
                        val = (curr_price - prev_price) / prev_price if prev_price != 0 else float("nan")
                        result.at[last_idx, pct_col] = val
        
        # Now calculate per-day
        last_idx = result.index[-1] if len(result.index) > 0 else None
        for w in windows:
            pct_col = f"{column}_pct_{w}"
            per_day_col = f"{column}_per_day_{w}"
            result[per_day_col] = pd.Series([float("nan")] * len(result), index=result.index)
            if last_idx is not None and pct_col in result.columns:
                val = result.at[last_idx, pct_col]
                result.at[last_idx, per_day_col] = (val / float(w)) if pd.notnull(val) else float("nan")
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        """Extract daily momentum values"""
        params = config.parameters
        windows = params.get('windows', [30, 60, 90, 180, 360])
        
        last_row = df.iloc[-1]
        snapshot = {}
        
        for w in windows:
            col_name = f"{column}_per_day_{w}"
            val = last_row.get(col_name)
            if pd.notnull(val):
                snapshot[col_name] = float(val)
        
        return IndicatorSnapshot(values=snapshot)
    
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        """Calculate weighted daily momentum score"""
        if config.weight <= 0:
            return None
        
        params = config.parameters
        windows = params.get('windows', [30, 60, 90, 180, 360])
        
        # Weighted average
        weights = {30: 0.4, 60: 0.3, 90: 0.15, 180: 0.1, 360: 0.05}
        total_w = 0.0
        agg = 0.0
        
        last_row = df.iloc[-1]
        for w, wgt in weights.items():
            val = last_row.get(f"{column}_per_day_{w}")
            if pd.notnull(val):
                agg += float(val) * wgt
                total_w += wgt
        
        if total_w == 0:
            return None
        
        raw = agg / total_w if total_w > 0 else 0.0
        # Clamp to reasonable range for daily momentum
        raw = max(-0.01, min(0.01, raw))
        contribution = raw * config.weight

        calculation_details = [
            "Daily Momentum Score Calculation (Per-Day Rate):",
            ""
        ]
        
        for w, wgt in weights.items():
            val = last_row.get(f"{column}_per_day_{w}")
            if pd.notnull(val):
                calculation_details.append(f"  Period {w}d: {float(val):.6f} × {wgt} = {float(val) * wgt:.6f}")
        
        calculation_details.extend([
            "",
            f"Step 1: Weighted Average = Sum(Value × Weight) / Sum(Weights)",
            f"        = {agg:.6f} / {total_w:.4f}",
            f"        = {raw:.6f}",
            "",
            f"Step 2: Final Contribution = Raw Score × Indicator Weight",
            f"        = {raw:.6f} × {config.weight:.2f}",
            f"        = {contribution:.6f}",
            "",
            f"Note: This represents the per-day rate of change"
        ])

        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=f"Weighted daily momentum: {raw:.6f}",
            calculation_details=calculation_details
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        """Generate explanation of daily momentum"""
        params = config.parameters
        windows = params.get('windows', [30, 60, 90, 180, 360])
        
        last_row = df.iloc[-1]
        lines = []
        lines.append("📊 Daily Momentum Analysis:")
        
        has_data = False
        for w in windows:
            val = last_row.get(f"{column}_per_day_{w}")
            if pd.notnull(val):
                has_data = True
                percent_per_day = float(val) * 100
                lines.append(f"  {w}d: {percent_per_day:+.4f}% per day")
        
        if not has_data:
            lines.append("  ⚠️ Insufficient data")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['provides_trend_direction']


# Instantiate to register
_ = DailyMomentumIndicator()

