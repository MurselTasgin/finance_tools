# finance_tools/stocks/analysis/indicators.py
from __future__ import annotations

from typing import Dict, Optional, List, Sequence

import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.volatility import AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator

from ...logging import get_logger


class StockTechnicalIndicatorCalculator:
    """Computes technical indicators on stock price and volume data.
    
    Supports indicators including:
    - Price indicators: EMA, RSI, MACD, Supertrend, ADX, ATR
    - Volume indicators: OBV, Volume SMA
    - Momentum indicators: Stochastic, ROC, Williams %R
    """

    def __init__(self) -> None:
        self.logger = get_logger("stock_indicators")

    def compute(self, df: pd.DataFrame, column: str, indicators: Dict[str, Dict]) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not present in DataFrame")

        output = df.copy()
        
        # Ensure we have OHLCV columns (check in output, not df, since we'll add columns)
        series = output[column].astype(float)
        
        # Get column references - check in output as we iterate
        def get_high_col():
            return output['high'] if 'high' in output.columns else None
        def get_low_col():
            return output['low'] if 'low' in output.columns else None
        def get_volume_col():
            return output['volume'] if 'volume' in output.columns else None

        for name, params in indicators.items():
            name_lower = name.lower()
            params = params or {}
            
            if name_lower == "ema":
                if "windows" in params and isinstance(params["windows"], (list, tuple)):
                    windows: List[int] = [int(w) for w in params["windows"]]
                    for w in windows:
                        ema = EMAIndicator(close=series, window=w, fillna=False).ema_indicator()
                        output[f"{column}_ema_{w}"] = ema
                else:
                    window = int(params.get("window", 20))
                    ema = EMAIndicator(close=series, window=window, fillna=False).ema_indicator()
                    output[f"{column}_ema_{window}"] = ema
                    
            elif name_lower == "rsi":
                window = int(params.get("window", 14))
                rsi = RSIIndicator(close=series, window=window, fillna=False).rsi()
                output[f"{column}_rsi_{window}"] = rsi
                
            elif name_lower == "macd":
                window_slow = int(params.get("window_slow", 26))
                window_fast = int(params.get("window_fast", 12))
                window_sign = int(params.get("window_sign", 9))
                macd = MACD(
                    close=series,
                    window_slow=window_slow,
                    window_fast=window_fast,
                    window_sign=window_sign,
                    fillna=False,
                )
                output[f"{column}_macd"] = macd.macd()
                output[f"{column}_macd_signal"] = macd.macd_signal()
                output[f"{column}_macd_diff"] = macd.macd_diff()
                
            elif name_lower == "ema_cross":
                short_w = int(params.get("short", 20))
                long_w = int(params.get("long", 50))
                ema_short = EMAIndicator(close=series, window=short_w, fillna=False).ema_indicator()
                ema_long = EMAIndicator(close=series, window=long_w, fillna=False).ema_indicator()
                short_col = f"{column}_ema_{short_w}"
                long_col = f"{column}_ema_{long_w}"
                if short_col not in output.columns:
                    output[short_col] = ema_short
                if long_col not in output.columns:
                    output[long_col] = ema_long
                prev_diff = (ema_short - ema_long).shift(1)
                curr_diff = (ema_short - ema_long)
                cross_up = (prev_diff <= 0) & (curr_diff > 0)
                cross_down = (prev_diff >= 0) & (curr_diff < 0)
                output[f"{column}_ema_{short_w}_{long_w}_cross_up"] = cross_up.astype(int)
                output[f"{column}_ema_{short_w}_{long_w}_cross_down"] = cross_down.astype(int)
                
            elif name_lower == "momentum":
                windows: Sequence[int] = params.get("windows", [30, 60, 90, 180, 360])
                if "date" in output.columns and len(output.index) > 0:
                    dt = pd.to_datetime(output["date"])
                    last_idx = output.index[-1]
                    last_date = dt.iloc[-1]
                    last_price = float(series.iloc[-1]) if pd.notnull(series.iloc[-1]) else None

                    def safe_pct(curr: Optional[float], prev: Optional[float]) -> float:
                        if curr is None or prev is None or prev == 0 or pd.isna(prev) or pd.isna(curr):
                            return float("nan")
                        return (curr - prev) / prev

                    for w in windows:
                        pct_col = f"{column}_pct_{w}"
                        output[pct_col] = pd.Series([float("nan")] * len(output), index=output.index)
                        target_date = last_date - pd.Timedelta(days=int(w))
                        mask = dt <= target_date
                        if mask.any():
                            prev_price = float(series[mask].iloc[-1])
                            val = safe_pct(last_price, prev_price)
                            output.at[last_idx, pct_col] = val
                else:
                    last_idx = output.index[-1]
                    for w in windows:
                        pct_col = f"{column}_pct_{w}"
                        output[pct_col] = pd.Series([float("nan")] * len(output), index=output.index)
                        if len(series) > w:
                            prev_price = float(series.iloc[-(w + 1)])
                            curr_price = float(series.iloc[-1])
                            val = (curr_price - prev_price) / prev_price if prev_price != 0 else float("nan")
                            output.at[last_idx, pct_col] = val
                            
            elif name_lower == "daily_momentum":
                windows: Sequence[int] = params.get("windows", [30, 60, 90, 180, 360])
                output = self.compute(output, column, {"momentum": {"windows": windows}})
                last_idx = output.index[-1] if len(output.index) > 0 else None
                for w in windows:
                    pct_col = f"{column}_pct_{w}"
                    per_day_col = f"{column}_per_day_{w}"
                    output[per_day_col] = pd.Series([float("nan")] * len(output), index=output.index)
                    if last_idx is not None and pct_col in output.columns:
                        val = output.at[last_idx, pct_col]
                        output.at[last_idx, per_day_col] = (val / float(w)) if pd.notnull(val) else float("nan")
                        
            elif name_lower == "supertrend":
                high_col = get_high_col()
                low_col = get_low_col()
                if high_col is None or low_col is None:
                    self.logger.warning("High/Low data not available for supertrend")
                    continue
                hl_factor = float(params.get("hl_factor", 0.05))
                atr_period = int(params.get("atr_period", 10))
                multiplier = float(params.get("multiplier", 3.0))
                close = series
                high = high_col
                low = low_col
                st, direction = self._compute_supertrend(high, low, close, atr_period, multiplier)
                output[f"{column}_supertrend"] = st
                output[f"{column}_supertrend_dir"] = direction
                
            elif name_lower == "volume_obv":
                volume_col = get_volume_col()
                if volume_col is not None:
                    obv = OnBalanceVolumeIndicator(close=series, volume=volume_col)
                    output[f"{column}_obv"] = obv.on_balance_volume()
                
            elif name_lower == "volume_sma":
                volume_col = get_volume_col()
                if volume_col is not None:
                    window = int(params.get("window", 20))
                    volume_sma = volume_col.rolling(window=window).mean()
                    output[f"volume_sma_{window}"] = volume_sma
                
            elif name_lower == "stochastic":
                high_col = get_high_col()
                low_col = get_low_col()
                if high_col is None or low_col is None:
                    self.logger.warning("High/Low data not available for stochastic")
                    continue
                k_period = int(params.get("k_period", 14))
                d_period = int(params.get("d_period", 3))
                stoch = StochasticOscillator(
                    high=high_col,
                    low=low_col,
                    close=series,
                    window=k_period,
                    smooth_window=d_period,
                    fillna=False
                )
                output[f"{column}_stoch_k"] = stoch.stoch()
                output[f"{column}_stoch_d"] = stoch.stoch_signal()
                
            elif name_lower == "roc":
                window = int(params.get("window", 10))
                roc = ((series / series.shift(window)) - 1) * 100
                output[f"{column}_roc_{window}"] = roc
                
            elif name_lower == "williams":
                high_col = get_high_col()
                low_col = get_low_col()
                if high_col is None or low_col is None:
                    self.logger.warning("High/Low data not available for Williams %R")
                    continue
                window = int(params.get("window", 14))
                wr = self._compute_williams_r(high_col, low_col, series, window)
                output[f"{column}_williams_r"] = wr
                
            elif name_lower == "atr":
                high_col = get_high_col()
                low_col = get_low_col()
                if high_col is None or low_col is None:
                    self.logger.warning("High/Low data not available for ATR")
                    continue
                window = int(params.get("window", 14))
                atr = AverageTrueRange(high=high_col, low=low_col, close=series, window=window, fillna=False)
                output[f"{column}_atr"] = atr.average_true_range()
                
            elif name_lower == "adx":
                high_col = get_high_col()
                low_col = get_low_col()
                if high_col is None or low_col is None:
                    self.logger.warning("High/Low data not available for ADX")
                    continue
                window = int(params.get("window", 14))
                adx = ADXIndicator(high=high_col, low=low_col, close=series, window=window, fillna=False)
                output[f"{column}_adx"] = adx.adx()
                output[f"{column}_adx_plus"] = adx.adx_pos()
                output[f"{column}_adx_minus"] = adx.adx_neg()
                
            else:
                self.logger.warning(f"Unknown indicator '{name}'. Skipping.")

        return output
    
    def _compute_supertrend(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int, multiplier: float
    ) -> tuple[pd.Series, pd.Series]:
        """Compute Supertrend indicator."""
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.ewm(span=period, adjust=False, min_periods=period).mean()
        hl2 = (high + low) / 2.0
        basic_ub = hl2 + multiplier * atr
        basic_lb = hl2 - multiplier * atr
        
        final_ub = basic_ub.copy()
        final_lb = basic_lb.copy()
        
        for i in range(1, len(close)):
            if not pd.isna(close.iloc[i - 1]):
                if (basic_ub.iloc[i] < final_ub.iloc[i - 1]) or (close.iloc[i - 1] > final_ub.iloc[i - 1]):
                    final_ub.iloc[i] = basic_ub.iloc[i]
                else:
                    final_ub.iloc[i] = final_ub.iloc[i - 1]
                    
                if (basic_lb.iloc[i] > final_lb.iloc[i - 1]) or (close.iloc[i - 1] < final_lb.iloc[i - 1]):
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
                
            if (supertrend.iloc[i - 1] == final_ub.iloc[i - 1]) and (close.iloc[i] <= final_ub.iloc[i]):
                supertrend.iloc[i] = final_ub.iloc[i]
                direction.iloc[i] = -1.0
            elif (supertrend.iloc[i - 1] == final_ub.iloc[i - 1]) and (close.iloc[i] > final_ub.iloc[i]):
                supertrend.iloc[i] = final_lb.iloc[i]
                direction.iloc[i] = 1.0
            elif (supertrend.iloc[i - 1] == final_lb.iloc[i - 1]) and (close.iloc[i] >= final_lb.iloc[i]):
                supertrend.iloc[i] = final_lb.iloc[i]
                direction.iloc[i] = 1.0
            elif (supertrend.iloc[i - 1] == final_lb.iloc[i - 1]) and (close.iloc[i] < final_lb.iloc[i]):
                supertrend.iloc[i] = final_ub.iloc[i]
                direction.iloc[i] = -1.0
            else:
                supertrend.iloc[i] = basic_ub.iloc[i]
                direction.iloc[i] = -1.0

        return supertrend, direction
    
    def _compute_williams_r(
        self, high: pd.Series, low: pd.Series, close: pd.Series, window: int
    ) -> pd.Series:
        """Compute Williams %R indicator."""
        highest_high = high.rolling(window=window, min_periods=window).max()
        lowest_low = low.rolling(window=window, min_periods=window).min()
        wr = -100 * (highest_high - close) / (highest_high - lowest_low)
        return wr

