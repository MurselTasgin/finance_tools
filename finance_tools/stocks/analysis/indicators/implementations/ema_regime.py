# finance_tools/stocks/analysis/indicators/implementations/ema_regime.py
from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from ..base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
from ..registry import registry
from ta.trend import EMAIndicator
from ta.volatility import AverageTrueRange


def _crossed_above(a: pd.Series, b: pd.Series) -> pd.Series:
    """Helper: True on the bar where a crosses above b."""
    return (a > b) & (a.shift(1) <= b.shift(1))


def _crossed_below(a: pd.Series, b: pd.Series) -> pd.Series:
    """Helper: True on the bar where a crosses below b."""
    return (a < b) & (a.shift(1) >= b.shift(1))


class EMARegimeIndicator(BaseIndicator):
    """EMA Regime Signals indicator"""
    
    def __init__(self):
        registry.register(self)
    
    def get_id(self) -> str:
        return "ema_regime"
    
    def get_name(self) -> str:
        return "EMA Regime Signals"
    
    def get_description(self) -> str:
        return "EMA-based regime signals with Golden Cross, Death Cross, trend filters, extension detection, and volume confirmation"
    
    def get_required_columns(self) -> List[str]:
        return ['close']
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'fast': {'type': 'integer', 'default': 20, 'min': 5, 'max': 100},
            'slow': {'type': 'integer', 'default': 50, 'min': 10, 'max': 200},
            'regime': {'type': 'integer', 'default': 200, 'min': 50, 'max': 500},
            'max_ext_atr': {'type': 'float', 'default': 1.5, 'min': 0.5, 'max': 5.0},
            'min_vol_mult': {'type': 'float', 'default': 1.2, 'min': 0.5, 'max': 3.0},
            'vol_sma': {'type': 'integer', 'default': 20, 'min': 5, 'max': 100},
            'atr_period': {'type': 'integer', 'default': 14, 'min': 5, 'max': 50}
        }
    
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        params = config.parameters
        ema_fast = int(params.get("fast", 20))
        ema_slow = int(params.get("slow", 50))
        ema_regime = int(params.get("regime", 200))
        max_ext_atr = float(params.get("max_ext_atr", 1.5))
        min_vol_mult = float(params.get("min_vol_mult", 1.2))
        vol_sma_period = int(params.get("vol_sma", 20))
        atr_window = int(params.get("atr_period", 14))
        
        series = df[column].astype(float)
        high_col = df.get('high')
        low_col = df.get('low')
        volume_col = df.get('volume')
        
        result = df.copy()
        
        # Compute EMAs
        ema_fast_series = EMAIndicator(close=series, window=ema_fast, fillna=False).ema_indicator()
        ema_slow_series = EMAIndicator(close=series, window=ema_slow, fillna=False).ema_indicator()
        ema_regime_series = EMAIndicator(close=series, window=ema_regime, fillna=False).ema_indicator()
        
        result[f"{column}_ema_{ema_fast}"] = ema_fast_series
        result[f"{column}_ema_{ema_slow}"] = ema_slow_series
        result[f"{column}_ema_{ema_regime}"] = ema_regime_series
        
        # Compute ATR if not already present
        atr_col = f"{column}_atr"
        if atr_col not in result.columns and high_col is not None and low_col is not None:
            atr_series = AverageTrueRange(
                high=high_col, low=low_col, close=series, window=atr_window, fillna=False
            ).average_true_range()
            result[atr_col] = atr_series
        elif atr_col in result.columns:
            atr_series = result[atr_col]
        else:
            atr_series = None
        
        # Volume SMA
        if volume_col is not None:
            vol_sma_col = f"volume_sma_{vol_sma_period}"
            result[vol_sma_col] = volume_col.rolling(window=vol_sma_period, min_periods=vol_sma_period).mean()
            vol_sma_series = result[vol_sma_col]
        else:
            vol_sma_series = None
        
        # Price x EMA-fast crosses
        result[f"{column}_sig_price_above_fast"] = _crossed_above(series, ema_fast_series).astype(int)
        result[f"{column}_sig_price_below_fast"] = _crossed_below(series, ema_fast_series).astype(int)
        
        # EMA-fast x EMA-slow crosses
        result[f"{column}_sig_fast_above_slow"] = _crossed_above(ema_fast_series, ema_slow_series).astype(int)
        result[f"{column}_sig_fast_below_slow"] = _crossed_below(ema_fast_series, ema_slow_series).astype(int)
        
        # Price x EMA-regime crosses
        result[f"{column}_sig_price_above_regime"] = _crossed_above(series, ema_regime_series).astype(int)
        result[f"{column}_sig_price_below_regime"] = _crossed_below(series, ema_regime_series).astype(int)
        
        # EMA-slow x EMA-regime crosses (Golden/Death cross)
        result[f"{column}_golden_cross"] = _crossed_above(ema_slow_series, ema_regime_series).astype(int)
        result[f"{column}_death_cross"] = _crossed_below(ema_slow_series, ema_regime_series).astype(int)
        
        # Regime filters (trend context)
        result[f"{column}_regime_long"] = (
            (series > ema_regime_series) & (ema_slow_series > ema_regime_series)
        ).astype(int)
        result[f"{column}_regime_short"] = (
            (series < ema_regime_series) & (ema_slow_series < ema_regime_series)
        ).astype(int)
        
        # Slow EMA slope filter (reduce fake flips)
        result[f"{column}_slow_ema_slope_up"] = (ema_slow_series > ema_slow_series.shift(3)).astype(int)
        result[f"{column}_slow_ema_slope_dn"] = (ema_slow_series < ema_slow_series.shift(3)).astype(int)
        
        # Extension filter (avoid buying stretched moves)
        if atr_series is not None:
            dist_fast_atr = (series - ema_fast_series).abs() / atr_series.replace(0, np.nan)
            result[f"{column}_dist_fast_atr"] = dist_fast_atr
            result[f"{column}_not_extended"] = (dist_fast_atr < max_ext_atr).astype(int)
        else:
            result[f"{column}_dist_fast_atr"] = pd.Series([float("nan")] * len(result), index=result.index)
            result[f"{column}_not_extended"] = pd.Series([0] * len(result), index=result.index)
        
        # Volume confirmation
        if volume_col is not None and vol_sma_series is not None:
            vol_confirm = (volume_col >= (min_vol_mult * vol_sma_series)).astype(int)
            result[f"{column}_vol_confirm"] = vol_confirm
        else:
            result[f"{column}_vol_confirm"] = pd.Series([0] * len(result), index=result.index)
        
        # Composite entry conditions
        regime_long = result[f"{column}_regime_long"]
        regime_short = result[f"{column}_regime_short"]
        slow_slope_up = result[f"{column}_slow_ema_slope_up"]
        slow_slope_dn = result[f"{column}_slow_ema_slope_dn"]
        not_extended = result[f"{column}_not_extended"]
        vol_confirm = result[f"{column}_vol_confirm"]
        sig_price_above_fast = result[f"{column}_sig_price_above_fast"]
        sig_price_below_fast = result[f"{column}_sig_price_below_fast"]
        sig_fast_above_slow = result[f"{column}_sig_fast_above_slow"]
        sig_fast_below_slow = result[f"{column}_sig_fast_below_slow"]
        
        result[f"{column}_long_entry_price_x_fast"] = (
            sig_price_above_fast & regime_long & slow_slope_up & not_extended & vol_confirm
        ).astype(int)
        result[f"{column}_long_entry_fast_x_slow"] = (
            sig_fast_above_slow & regime_long & slow_slope_up & not_extended & vol_confirm
        ).astype(int)
        result[f"{column}_short_entry_price_x_fast"] = (
            sig_price_below_fast & regime_short & slow_slope_dn & not_extended & vol_confirm
        ).astype(int)
        result[f"{column}_short_entry_fast_x_slow"] = (
            sig_fast_below_slow & regime_short & slow_slope_dn & not_extended & vol_confirm
        ).astype(int)
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        params = config.parameters
        ema_fast = int(params.get("fast", 20))
        ema_slow = int(params.get("slow", 50))
        ema_regime = int(params.get("regime", 200))
        
        last_row = df.iloc[-1]
        snapshot = {}
        
        for col_suffix in [
            f"ema_{ema_fast}", f"ema_{ema_slow}", f"ema_{ema_regime}",
            "sig_price_above_fast", "sig_price_below_fast",
            "sig_fast_above_slow", "sig_fast_below_slow",
            "regime_long", "regime_short",
            "long_entry_price_x_fast", "long_entry_fast_x_slow",
            "short_entry_price_x_fast", "short_entry_fast_x_slow",
            "golden_cross", "death_cross",
            "dist_fast_atr", "not_extended", "vol_confirm"
        ]:
            key = f"{column}_{col_suffix}"
            val = last_row.get(key)
            if pd.notnull(val):
                snapshot[key] = float(val)
        
        return IndicatorSnapshot(values=snapshot)
    
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        if config.weight <= 0:
            return None
        
        last_row = df.iloc[-1]
        
        # Check various signals
        golden_cross = last_row.get(f"{column}_golden_cross", 0) == 1
        death_cross = last_row.get(f"{column}_death_cross", 0) == 1
        regime_long = last_row.get(f"{column}_regime_long", 0) == 1
        regime_short = last_row.get(f"{column}_regime_short", 0) == 1
        price_above_fast = last_row.get(f"{column}_sig_price_above_fast", 0) == 1
        price_below_fast = last_row.get(f"{column}_sig_price_below_fast", 0) == 1
        fast_above_slow = last_row.get(f"{column}_sig_fast_above_slow", 0) == 1
        fast_below_slow = last_row.get(f"{column}_sig_fast_below_slow", 0) == 1
        not_extended = last_row.get(f"{column}_not_extended", 0) == 1
        vol_confirm = last_row.get(f"{column}_vol_confirm", 0) == 1
        
        raw = 0.0
        
        if golden_cross:
            raw += 0.2
        elif death_cross:
            raw -= 0.2
        
        if regime_long:
            raw += 0.15
        elif regime_short:
            raw -= 0.15
        
        if price_above_fast:
            raw += 0.1
        elif price_below_fast:
            raw -= 0.1
        
        if fast_above_slow:
            raw += 0.1
        elif fast_below_slow:
            raw -= 0.1
        
        if not_extended:
            raw += 0.05
        else:
            raw -= 0.05
        
        if vol_confirm:
            raw += 0.05
        else:
            raw -= 0.02

        contribution = raw * config.weight

        # Detailed calculation steps
        params = config.parameters
        ema_fast = int(params.get("fast", 20))
        ema_slow = int(params.get("slow", 50))
        ema_regime_val = int(params.get("regime", 200))

        calculation_details = [
            f"EMA Regime Score Calculation (EMA {ema_fast}/{ema_slow}/{ema_regime_val}):",
            "",
            "Signal Components & Weights:",
        ]

        # Golden/Death Cross
        if golden_cross:
            calculation_details.append(f"  • Golden Cross (EMA{ema_slow} > EMA{ema_regime_val}): +0.20")
        elif death_cross:
            calculation_details.append(f"  • Death Cross (EMA{ema_slow} < EMA{ema_regime_val}): -0.20")
        else:
            calculation_details.append(f"  • No Golden/Death Cross: +0.00")

        # Regime
        if regime_long:
            calculation_details.append(f"  • Long Regime: +0.15")
        elif regime_short:
            calculation_details.append(f"  • Short Regime: -0.15")
        else:
            calculation_details.append(f"  • Neutral Regime: +0.00")

        # Price vs Fast EMA
        if price_above_fast:
            calculation_details.append(f"  • Price above EMA{ema_fast}: +0.10")
        elif price_below_fast:
            calculation_details.append(f"  • Price below EMA{ema_fast}: -0.10")
        else:
            calculation_details.append(f"  • No price cross: +0.00")

        # Fast vs Slow EMA
        if fast_above_slow:
            calculation_details.append(f"  • EMA{ema_fast} above EMA{ema_slow}: +0.10")
        elif fast_below_slow:
            calculation_details.append(f"  • EMA{ema_fast} below EMA{ema_slow}: -0.10")
        else:
            calculation_details.append(f"  • No EMA cross: +0.00")

        # Extension filter
        if not_extended:
            calculation_details.append(f"  • Price not extended: +0.05")
        else:
            calculation_details.append(f"  • Price extended: -0.05")

        # Volume confirmation
        if vol_confirm:
            calculation_details.append(f"  • Volume confirmed: +0.05")
        else:
            calculation_details.append(f"  • Volume weak: -0.02")

        calculation_details.extend([
            "",
            f"Step 1: Sum all signal components",
            f"        Raw Score = {raw:+.4f}",
            "",
            f"Step 2: Final Contribution = Raw Score × Weight",
            f"        = {raw:+.4f} × {config.weight:.2f}",
            f"        = {contribution:+.4f}"
        ])

        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=f"EMA Regime signals",
            calculation_details=calculation_details
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        params = config.parameters
        ema_fast = int(params.get("fast", 20))
        ema_slow = int(params.get("slow", 50))
        ema_regime = int(params.get("regime", 200))
        
        last_row = df.iloc[-1]
        
        golden_cross = last_row.get(f"{column}_golden_cross", 0) == 1
        death_cross = last_row.get(f"{column}_death_cross", 0) == 1
        regime_long = last_row.get(f"{column}_regime_long", 0) == 1
        regime_short = last_row.get(f"{column}_regime_short", 0) == 1
        price_above_fast = last_row.get(f"{column}_sig_price_above_fast", 0) == 1
        price_below_fast = last_row.get(f"{column}_sig_price_below_fast", 0) == 1
        fast_above_slow = last_row.get(f"{column}_sig_fast_above_slow", 0) == 1
        fast_below_slow = last_row.get(f"{column}_sig_fast_below_slow", 0) == 1
        dist_atr = last_row.get(f"{column}_dist_fast_atr")
        not_extended = last_row.get(f"{column}_not_extended", 0) == 1
        vol_confirm = last_row.get(f"{column}_vol_confirm", 0) == 1
        
        lines = []
        lines.append(f"📊 EMA Regime Signals Analysis:")
        
        if golden_cross:
            lines.append(f"  🚀 GOLDEN CROSS: EMA {ema_slow} crossed above EMA {ema_regime}")
        elif death_cross:
            lines.append(f"  🔻 DEATH CROSS: EMA {ema_slow} crossed below EMA {ema_regime}")
        
        if regime_long:
            lines.append(f"  ✅ REGIME: LONG")
        elif regime_short:
            lines.append(f"  ❌ REGIME: SHORT")
        
        if price_above_fast:
            lines.append(f"  ✅ PRICE CROSS: Price crossed ABOVE EMA-{ema_fast}")
        elif price_below_fast:
            lines.append(f"  ❌ PRICE CROSS: Price crossed BELOW EMA-{ema_fast}")
        
        if fast_above_slow:
            lines.append(f"  ✅ EMA CROSS: EMA-{ema_fast} crossed ABOVE EMA-{ema_slow}")
        elif fast_below_slow:
            lines.append(f"  ❌ EMA CROSS: EMA-{ema_fast} crossed BELOW EMA-{ema_slow}")
        
        if pd.notnull(dist_atr):
            if not_extended:
                lines.append(f"  ✅ NOT EXTENDED: ({dist_atr:.2f} ATR)")
            else:
                lines.append(f"  ⚠️ EXTENDED: ({dist_atr:.2f} ATR)")
        
        if vol_confirm:
            lines.append(f"  ✅ VOLUME: Volume confirms signal")
        else:
            lines.append(f"  ⚠️ VOLUME: Weak volume")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['provides_buy_signal', 'provides_sell_signal', 'detects_trend_regime', 'measures_extension']


# Instantiate to register
_ = EMARegimeIndicator()

