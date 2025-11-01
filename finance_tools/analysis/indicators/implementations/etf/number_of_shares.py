# finance_tools/analysis/indicators/implementations/etf/number_of_shares.py
from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
from ta.trend import EMAIndicator

from finance_tools.analysis.indicators.base import (
    BaseIndicator,
    IndicatorConfig,
    IndicatorSnapshot,
    IndicatorScore,
)
from finance_tools.analysis.indicators.registry import registry


class NumberOfSharesIndicator(BaseIndicator):
    """Number of Shares indicator for ETFs with EMA"""

    def __init__(self):
        registry.register(self)

    def get_id(self) -> str:
        return "number_of_shares"

    def get_name(self) -> str:
        return "Number of Shares"

    def get_description(self) -> str:
        return "Tracks the number of outstanding shares with EMA smoothing"

    def get_required_columns(self) -> List[str]:
        return ["number_of_shares"]

    def get_asset_types(self) -> List[str]:
        return ["etf"]

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "ema_period": {
                "type": "integer",
                "default": 20,
                "min": 5,
                "max": 200,
                "description": "EMA period for smoothing",
            }
        }

    def calculate(
        self, df: pd.DataFrame, column: str, config: IndicatorConfig
    ) -> pd.DataFrame:
        """Calculate number of shares with EMA"""
        params = config.parameters
        ema_period = int(params.get("ema_period", 20))

        # Use number_of_shares column directly (not the column parameter which is for price)
        if "number_of_shares" not in df.columns:
            return df

        result = df.copy()
        series = df["number_of_shares"].astype(float)

        # Ensure the raw column is explicitly in the result (it should already be, but make sure)
        # This ensures it's included in the indicator's column list for the frontend
        if "number_of_shares" not in result.columns:
            result["number_of_shares"] = series

        # Calculate EMA - include period in column name to allow different periods
        ema_col_name = f"number_of_shares_ema_{ema_period}"
        if ema_col_name not in result.columns:
            ema_series = EMAIndicator(close=series, window=ema_period, fillna=False).ema_indicator()
            result[ema_col_name] = ema_series

        return result

    def get_snapshot(
        self, df: pd.DataFrame, column: str, config: IndicatorConfig
    ) -> IndicatorSnapshot:
        """Extract current number of shares values"""
        params = config.parameters
        ema_period = int(params.get("ema_period", 20))

        last_row = df.iloc[-1]
        snapshot = {}

        # Get raw value
        raw_val = last_row.get("number_of_shares")
        if pd.notnull(raw_val):
            snapshot["number_of_shares"] = float(raw_val)

        # Get EMA value
        ema_col_name = f"number_of_shares_ema_{ema_period}"
        ema_val = last_row.get(ema_col_name)
        if pd.notnull(ema_val):
            snapshot[ema_col_name] = float(ema_val)

        return IndicatorSnapshot(values=snapshot)

    def get_score(
        self, df: pd.DataFrame, column: str, config: IndicatorConfig
    ) -> Optional[IndicatorScore]:
        """Calculate score based on number of shares trend"""
        if config.weight <= 0:
            return None

        params = config.parameters
        ema_period = int(params.get("ema_period", 20))

        last_row = df.iloc[-1]
        raw_val = last_row.get("number_of_shares")
        ema_col_name = f"number_of_shares_ema_{ema_period}"
        ema_val = last_row.get(ema_col_name)

        if not all(pd.notnull([raw_val, ema_val])) or ema_val == 0:
            return None

        # Score: positive if shares increasing (more liquidity/investor interest)
        raw = (float(raw_val) - float(ema_val)) / float(ema_val)
        # Clamp to reasonable range
        raw = max(-0.1, min(0.1, raw))
        contribution = raw * config.weight

        explanation = f"Number of shares: {float(raw_val):,.0f}, EMA: {float(ema_val):,.0f}, Trend: {raw:+.3f}"

        calculation_details = [
            f"Number of Shares Indicator (EMA {ema_period}):",
            "",
            f"Step 1: Current Shares = {float(raw_val):,.0f}",
            f"Step 2: EMA {ema_period} = {float(ema_val):,.0f}",
            "",
            "Step 3: Trend Score = (Current - EMA) / EMA",
            f"        = ({float(raw_val):,.0f} - {float(ema_val):,.0f}) / {float(ema_val):,.0f}",
            f"        = {raw:.4f}",
            "",
            "Step 4: Final Contribution = Trend Score × Weight",
            f"        = {raw:.4f} × {config.weight:.2f}",
            f"        = {contribution:.4f}",
        ]

        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=explanation,
            calculation_details=calculation_details,
        )

    def explain(
        self, df: pd.DataFrame, column: str, config: IndicatorConfig
    ) -> List[str]:
        """Generate explanation of number of shares trend"""
        params = config.parameters
        ema_period = int(params.get("ema_period", 20))

        last_row = df.iloc[-1]
        lines = []
        lines.append(f"📊 Number of Shares Analysis (EMA {ema_period}):")

        raw_val = last_row.get("number_of_shares")
        ema_col_name = f"number_of_shares_ema_{ema_period}"
        ema_val = last_row.get(ema_col_name)

        if not all(pd.notnull([raw_val, ema_val])):
            lines.append("  ⚠️ Insufficient data")
            return lines

        raw_float = float(raw_val)
        ema_float = float(ema_val)

        lines.append(f"  Current: {raw_float:,.0f} shares")
        lines.append(f"  EMA: {ema_float:,.0f} shares")

        if raw_float > ema_float:
            diff_pct = ((raw_float - ema_float) / ema_float) * 100
            lines.append(f"  ✅ Increasing: {diff_pct:+.2f}% above EMA")
        elif raw_float < ema_float:
            diff_pct = ((raw_float - ema_float) / ema_float) * 100
            lines.append(f"  ❌ Decreasing: {diff_pct:+.2f}% below EMA")
        else:
            lines.append("  ➖ Stable: At EMA level")

        return lines

    def get_capabilities(self) -> List[str]:
        return ["provides_trend_direction"]


# Instantiate to register
_ = NumberOfSharesIndicator()

