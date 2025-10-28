# finance_tools/analysis/indicators/implementations/common/momentum.py
"""
Momentum indicator - Universal for both stocks and ETFs.

Calculates price momentum as percentage change over specified periods.
Works for any asset type with a price column.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd

from finance_tools.analysis.indicators.base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
from finance_tools.analysis.indicators.registry import registry


class MomentumIndicatorImpl(BaseIndicator):
    """Momentum indicator - works for both stocks and ETFs"""
    
    def __init__(self):
        registry.register(self)
    
    def get_id(self) -> str:
        return "momentum"
    
    def get_name(self) -> str:
        return "Price Momentum"
    
    def get_description(self) -> str:
        return "Price momentum over multiple time periods as percentage change"
    
    def get_required_columns(self) -> List[str]:
        # Works with either 'close' (stocks) or 'price' (ETFs) plus optional 'date'
        return ['close', 'price', 'date']
    
    def get_asset_types(self) -> List[str]:
        """Momentum works for both asset types"""
        return ['stock', 'etf']
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'windows': {
                'type': 'array',
                'default': [30, 60, 90, 180, 360],
                'description': 'List of time periods in days for momentum calculation'
            }
        }
    
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        """Calculate momentum as percentage change over different periods"""
        params = config.parameters
        windows = params.get('windows', [30, 60, 90, 180, 360])
        
        result = df.copy()
        series = result[column].astype(float)
        
        # Handle date-based calculation if date column exists
        if "date" in result.columns and len(result.index) > 0:
            dt = pd.to_datetime(result["date"])
            last_idx = result.index[-1]
            last_date = dt.iloc[-1]
            last_price = float(series.iloc[-1]) if pd.notnull(series.iloc[-1]) else None

            def safe_pct(curr: Optional[float], prev: Optional[float]) -> float:
                if (
                    curr is None
                    or prev is None
                    or prev == 0
                    or pd.isna(prev)
                    or pd.isna(curr)
                ):
                    return float("nan")
                return (curr - prev) / prev

            for w in windows:
                pct_col = f"{column}_pct_{w}"
                result[pct_col] = pd.Series(
                    [float("nan")] * len(result), index=result.index
                )

                target_date = last_date - pd.Timedelta(days=int(w))
                mask = dt <= target_date

                if mask.any():
                    prev_price = float(series[mask].iloc[-1])
                    result.at[last_idx, pct_col] = safe_pct(last_price, prev_price)
        else:
            # Fallback: use row offsets if no date provided
            for w in windows:
                pct_col = f"{column}_pct_{w}"
                result[pct_col] = pd.Series([float("nan")] * len(result), index=result.index)
                
                if len(series) > w:
                    last_idx = result.index[-1]
                    prev_price = float(series.iloc[-(w + 1)])
                    curr_price = float(series.iloc[-1])
                    
                    if prev_price != 0:
                        val = (curr_price - prev_price) / prev_price
                        result.at[last_idx, pct_col] = val
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        """Extract momentum values"""
        params = config.parameters
        windows = params.get('windows', [30, 60, 90, 180, 360])
        
        last_row = df.iloc[-1]
        snapshot = {}
        
        for w in windows:
            col_name = f"{column}_pct_{w}"
            val = last_row.get(col_name)
            if pd.notnull(val):
                snapshot[col_name] = float(val)
        
        return IndicatorSnapshot(values=snapshot)
    
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        """Calculate weighted momentum score"""
        if config.weight <= 0:
            return None
        
        params = config.parameters
        windows = params.get('windows', [30, 60, 90, 180, 360])
        
        # Weighted average favoring recent windows
        weights = {30: 0.4, 60: 0.3, 90: 0.15, 180: 0.1, 360: 0.05}
        total_w = 0.0
        agg = 0.0
        
        last_row = df.iloc[-1]
        for w, wgt in weights.items():
            if w not in windows:
                continue
            val = last_row.get(f"{column}_pct_{w}")
            if pd.notnull(val):
                agg += float(val) * wgt
                total_w += wgt
        
        if total_w == 0:
            return None
        
        raw = agg / total_w if total_w > 0 else 0.0
        # Clamp to reasonable range
        raw = max(-0.5, min(0.5, raw))
        contribution = raw * config.weight
        
        calculation_details = [
            "Momentum Score Calculation (Weighted Average):",
            ""
        ]
        
        for w, wgt in weights.items():
            if w not in windows:
                continue
            val = last_row.get(f"{column}_pct_{w}")
            if pd.notnull(val):
                calculation_details.append(f"  Period {w}d: {float(val):.4f} × {wgt} = {float(val) * wgt:.4f}")
        
        calculation_details.extend([
            "",
            f"Step 1: Weighted Average = Sum(Value × Weight) / Sum(Weights)",
            f"        = {agg:.4f} / {total_w:.4f}",
            f"        = {raw:.4f}",
            "",
            f"Step 2: Final Contribution = Raw Score × Indicator Weight",
            f"        = {raw:.4f} × {config.weight:.2f}",
            f"        = {contribution:.4f}"
        ])
        
        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=f"Weighted momentum: {raw:.4f}",
            calculation_details=calculation_details
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        """Generate momentum explanation"""
        params = config.parameters
        windows = params.get('windows', [30, 60, 90, 180, 360])
        
        last_row = df.iloc[-1]
        lines = []
        lines.append("📊 Momentum Analysis:")
        
        has_data = False
        for w in windows:
            val = last_row.get(f"{column}_pct_{w}")
            if pd.notnull(val):
                has_data = True
                percent = float(val) * 100
                emoji = "📈" if val > 0 else "📉"
                lines.append(f"  {emoji} {w}d: {percent:+.2f}%")
        
        if not has_data:
            lines.append("  ⚠️ Insufficient data")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['provides_trend_direction']


# Instantiate to register
_ = MomentumIndicatorImpl()
