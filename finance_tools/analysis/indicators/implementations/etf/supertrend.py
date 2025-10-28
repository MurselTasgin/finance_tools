# finance_tools/analysis/indicators/implementations/etf/supertrend.py
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


class SupertrendIndicator(BaseIndicator):
    """Supertrend indicator for ETFs"""

    def __init__(self):
        registry.register(self)

    def get_id(self) -> str:
        return "supertrend"

    def get_name(self) -> str:
        return "Supertrend"

    def get_description(self) -> str:
        return "Trend-following indicator based on ATR"

    def get_required_columns(self) -> List[str]:
        return ["price", "date"]

    def get_asset_types(self) -> List[str]:
        return ["etf"]

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "hl_factor": {"type": "float", "default": 0.05, "min": 0.01, "max": 0.2},
            "atr_period": {"type": "integer", "default": 10, "min": 3, "max": 50},
            "multiplier": {"type": "float", "default": 3.0, "min": 1.0, "max": 5.0},
        }

    def calculate(
        self, df: pd.DataFrame, column: str, config: IndicatorConfig
    ) -> pd.DataFrame:
        """Calculate Supertrend indicator"""
        params = config.parameters
        hl_factor = float(params.get("hl_factor", 0.05))
        atr_period = int(params.get("atr_period", 10))
        multiplier = float(params.get("multiplier", 3.0))

        close = df[column].astype(float)
        high = close * (1.0 + hl_factor)
        low = close * (1.0 - hl_factor)

        st, direction = self._compute_supertrend(
            high, low, close, atr_period, multiplier
        )

        result = df.copy()
        result[f"{column}_supertrend"] = st
        result[f"{column}_supertrend_dir"] = direction

        return result

    def _compute_supertrend(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int, multiplier: float
    ) -> tuple[pd.Series, pd.Series]:
        """Compute Supertrend values"""
        # True Range
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR as EMA
        atr = tr.ewm(span=period, adjust=False, min_periods=period).mean()
        hl2 = (high + low) / 2.0
        basic_ub = hl2 + multiplier * atr
        basic_lb = hl2 - multiplier * atr

        final_ub = basic_ub.copy()
        final_lb = basic_lb.copy()
        for i in range(1, len(close)):
            if not pd.isna(close.iloc[i - 1]):
                if (basic_ub.iloc[i] < final_ub.iloc[i - 1]) or (
                    close.iloc[i - 1] > final_ub.iloc[i - 1]
                ):
                    final_ub.iloc[i] = basic_ub.iloc[i]
                else:
                    final_ub.iloc[i] = final_ub.iloc[i - 1]
                if (basic_lb.iloc[i] > final_lb.iloc[i - 1]) or (
                    close.iloc[i - 1] < final_lb.iloc[i - 1]
                ):
                    final_lb.iloc[i] = basic_lb.iloc[i]
                else:
                    final_lb.iloc[i] = final_lb.iloc[i - 1]

        supertrend = pd.Series(index=close.index, dtype=float)
        direction = pd.Series(index=close.index, dtype=float)
        for i in range(len(close)):
            if i == 0 or pd.isna(close.iloc[i - 1]):
                supertrend.iloc[i] = basic_ub.iloc[i]
                direction.iloc[i] = -1.0
                continue
            if (supertrend.iloc[i - 1] == final_ub.iloc[i - 1]) and (
                close.iloc[i] <= final_ub.iloc[i]
            ):
                supertrend.iloc[i] = final_ub.iloc[i]
                direction.iloc[i] = -1.0
            elif (supertrend.iloc[i - 1] == final_ub.iloc[i - 1]) and (
                close.iloc[i] > final_ub.iloc[i]
            ):
                supertrend.iloc[i] = final_lb.iloc[i]
                direction.iloc[i] = 1.0
            elif (supertrend.iloc[i - 1] == final_lb.iloc[i - 1]) and (
                close.iloc[i] >= final_lb.iloc[i]
            ):
                supertrend.iloc[i] = final_lb.iloc[i]
                direction.iloc[i] = 1.0
            elif (supertrend.iloc[i - 1] == final_lb.iloc[i - 1]) and (
                close.iloc[i] < final_lb.iloc[i]
            ):
                supertrend.iloc[i] = final_ub.iloc[i]
                direction.iloc[i] = -1.0
            else:
                supertrend.iloc[i] = final_ub.iloc[i]
                direction.iloc[i] = -1.0

        return supertrend, direction

    def get_snapshot(
        self, df: pd.DataFrame, column: str, config: IndicatorConfig
    ) -> IndicatorSnapshot:
        """Extract Supertrend values"""
        last_row = df.iloc[-1]
        snapshot = {}

        supertrend = last_row.get(f"{column}_supertrend")
        direction = last_row.get(f"{column}_supertrend_dir")

        if pd.notnull(supertrend):
            snapshot[f"{column}_supertrend"] = float(supertrend)
        if pd.notnull(direction):
            snapshot[f"{column}_supertrend_dir"] = float(direction)

        return IndicatorSnapshot(values=snapshot)

    def get_score(
        self, df: pd.DataFrame, column: str, config: IndicatorConfig
    ) -> Optional[IndicatorScore]:
        """Calculate Supertrend score"""
        if config.weight <= 0:
            return None

        last_row = df.iloc[-1]
        price = last_row.get(column)
        supertrend = last_row.get(f"{column}_supertrend")
        direction = last_row.get(f"{column}_supertrend_dir")

        if not all(pd.notnull([supertrend, direction])) or not price or price == 0:
            return None

        # Direction: 1 for bullish (uptrend), -1 for bearish (downtrend)
        # Score: relative distance from price to supertrend, scaled by direction
        rel = (float(price) - float(supertrend)) / float(price)
        # Clamp to reasonable range
        rel = max(-0.2, min(0.2, rel))
        raw = rel * float(direction)
        contribution = raw * config.weight

        calculation_details = [
            "Supertrend Score Calculation:",
            "",
            "Step 1: Supertrend Components",
            f"        Price = {float(price):.2f}",
            f"        Supertrend Value = {float(supertrend):.2f}",
            f"        Direction = {'Bullish (+1)' if direction > 0 else 'Bearish (-1)'}",
            "",
            "Step 2: Relative Position",
            f"        Relative Distance = (Price - Supertrend) / Price",
            f"        = ({float(price):.2f} - {float(supertrend):.2f}) / {float(price):.2f}",
            f"        = {rel:.4f}",
            "",
            "Step 3: Apply Direction",
            f"        Raw Score = Relative Distance × Direction",
            f"        = {rel:.4f} × {float(direction):.0f}",
            f"        = {raw:.4f}",
            "",
            "Step 4: Final Contribution = Raw Score × Indicator Weight",
            f"        = {raw:.4f} × {config.weight:.2f}",
            f"        = {contribution:.4f}",
        ]

        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=f"Supertrend direction: {'bullish' if direction > 0 else 'bearish'}",
            calculation_details=calculation_details,
        )

    def explain(
        self, df: pd.DataFrame, column: str, config: IndicatorConfig
    ) -> List[str]:
        """Generate explanation"""
        last_row = df.iloc[-1]
        price = last_row.get(column)
        supertrend = last_row.get(f"{column}_supertrend")
        direction = last_row.get(f"{column}_supertrend_dir")

        lines = []
        lines.append("📊 Supertrend Analysis:")

        if not all(pd.notnull([supertrend, direction])):
            lines.append("  ⚠️ Insufficient data")
            return lines

        price_float = float(price) if pd.notnull(price) else 0
        supertrend_float = float(supertrend) if pd.notnull(supertrend) else 0
        direction_float = float(direction) if pd.notnull(direction) else 0

        lines.append(f"  Supertrend: {supertrend_float:.2f}")

        if direction_float > 0:
            lines.append("  ✅ BULLISH: Price above Supertrend (Uptrend)")
        else:
            lines.append("  ❌ BEARISH: Price below Supertrend (Downtrend)")

        distance = price_float - supertrend_float
        percent = (distance / price_float * 100) if price_float > 0 else 0
        lines.append(f"  Distance: {distance:+.2f} ({percent:+.2f}%)")

        return lines

    def get_capabilities(self) -> List[str]:
        return ["provides_buy_signal", "provides_sell_signal", "provides_trend_direction"]


# Instantiate to register
_ = SupertrendIndicator()
