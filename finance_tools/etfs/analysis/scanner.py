# finance_tools/etfs/analysis/scanner.py
from __future__ import annotations

from typing import List, Dict

import pandas as pd

from ...logging import get_logger
from .indicators import TechnicalIndicatorCalculator
from .scanner_types import EtfScanCriteria, EtfScanResult, EtfSuggestion


class EtfScanner:
    """Runs ETF scans by computing indicators and deriving suggestions."""

    def __init__(self) -> None:
        self.logger = get_logger("etf_scanner")
        self.indicator_calculator = TechnicalIndicatorCalculator()

    def scan(self, code_to_df: Dict[str, pd.DataFrame], criteria: EtfScanCriteria) -> List[EtfScanResult]:
        results: List[EtfScanResult] = []
        for code, df in code_to_df.items():
            if df is None or df.empty or criteria.column not in df.columns:
                continue
            enriched = self.indicator_calculator.compute(
                df,
                criteria.column,
                indicators={
                    "ema": {"windows": [criteria.ema_short, criteria.ema_long]},
                    "ema_cross": {"short": criteria.ema_short, "long": criteria.ema_long},
                    "macd": {
                        "window_slow": criteria.macd_slow,
                        "window_fast": criteria.macd_fast,
                        "window_sign": criteria.macd_sign,
                    },
                    "rsi": {"window": criteria.rsi_window},
                "momentum": {"windows": [30, 60, 90, 180, 360]},
                "daily_momentum": {"windows": [30, 60, 90, 180, 360]},
                "supertrend": {"hl_factor": 0.05, "atr_period": 10, "multiplier": 3.0},
                },
            )
            suggestion, score, components = self._derive_suggestion_and_score(enriched, criteria)
            last_row = enriched.iloc[-1]
            snapshot = {
                f"{criteria.column}_ema_{criteria.ema_short}": last_row.get(f"{criteria.column}_ema_{criteria.ema_short}"),
                f"{criteria.column}_ema_{criteria.ema_long}": last_row.get(f"{criteria.column}_ema_{criteria.ema_long}"),
                f"{criteria.column}_macd": last_row.get(f"{criteria.column}_macd"),
                f"{criteria.column}_macd_signal": last_row.get(f"{criteria.column}_macd_signal"),
                f"{criteria.column}_rsi_{criteria.rsi_window}": last_row.get(f"{criteria.column}_rsi_{criteria.rsi_window}"),
            }
            results.append(
                EtfScanResult(
                    code=code,
                    timestamp=pd.to_datetime(last_row["date"]).to_pydatetime() if "date" in last_row else None,
                    last_value=float(last_row[criteria.column]) if pd.notnull(last_row[criteria.column]) else None,
                    suggestion=suggestion,
                    score=score,
                    indicators_snapshot=snapshot,
                    components=components,
                )
            )
        # Sort by descending score
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def _derive_suggestion_and_score(self, df: pd.DataFrame, criteria: EtfScanCriteria) -> tuple[EtfSuggestion, float, Dict[str, float]]:
        col = criteria.column
        last = df.iloc[-1]
        reasons: List[str] = []
        components: Dict[str, float] = {}

        # EMA crossover discrete signals
        cross_up = last.get(f"{col}_ema_{criteria.ema_short}_{criteria.ema_long}_cross_up") == 1
        cross_down = last.get(f"{col}_ema_{criteria.ema_short}_{criteria.ema_long}_cross_down") == 1

        # MACD
        macd = last.get(f"{col}_macd")
        macd_signal = last.get(f"{col}_macd_signal")
        macd_diff = last.get(f"{col}_macd_diff")
        macd_above = pd.notnull(macd) and pd.notnull(macd_signal) and macd > macd_signal
        macd_rising = pd.notnull(macd_diff) and macd_diff > 0

        # RSI
        rsi = last.get(f"{col}_rsi_{criteria.rsi_window}")
        rsi_oversold = pd.notnull(rsi) and rsi < criteria.rsi_lower
        rsi_overbought = pd.notnull(rsi) and rsi > criteria.rsi_upper

        # Build reasons list (informational)
        if cross_up:
            reasons.append(f"EMA {criteria.ema_short} crossed above EMA {criteria.ema_long}")
        if cross_down:
            reasons.append(f"EMA {criteria.ema_short} crossed below EMA {criteria.ema_long}")
        if macd_above and macd_rising:
            reasons.append("MACD above signal and rising")
        elif pd.notnull(macd) and pd.notnull(macd_signal) and not macd_above:
            reasons.append("MACD below signal")
        if rsi_oversold:
            reasons.append(f"RSI below {criteria.rsi_lower} (oversold)")
        if rsi_overbought:
            reasons.append(f"RSI above {criteria.rsi_upper} (overbought)")

        # Continuous scoring components
        # Clip helpers
        def clip(v: float, lo: float, hi: float) -> float:
            return float(min(max(v, lo), hi))

        price = float(last.get(col)) if pd.notnull(last.get(col)) else None
        ema_s = last.get(f"{col}_ema_{criteria.ema_short}")
        ema_l = last.get(f"{col}_ema_{criteria.ema_long}")

        ema_price_comp = 0.0
        ema_cross_comp = 0.0
        macd_comp = 0.0
        rsi_comp = 0.0
        momentum_comp = 0.0
        momentum_daily_comp = 0.0
        supertrend_comp = 0.0

        if pd.notnull(ema_s) and pd.notnull(price) and ema_s not in [0, None]:
            ema_price_comp = clip((price - float(ema_s)) / float(ema_s), -0.1, 0.1)
        if pd.notnull(ema_s) and pd.notnull(ema_l) and ema_l not in [0, None]:
            ema_cross_comp = clip((float(ema_s) - float(ema_l)) / float(ema_l), -0.1, 0.1)

        if pd.notnull(macd) and pd.notnull(macd_signal):
            denom = price if (price and price != 0) else 1.0
            macd_comp = clip((float(macd) - float(macd_signal)) / float(denom), -0.05, 0.05)
        elif pd.notnull(macd_diff):
            denom = price if (price and price != 0) else 1.0
            macd_comp = clip(float(macd_diff) / float(denom), -0.05, 0.05)

        if pd.notnull(rsi):
            rsi_comp = clip((float(rsi) - 50.0) / 50.0, -1.0, 1.0)

        # Momentum: weighted average favoring recent windows
        weights = {30: 0.4, 60: 0.3, 90: 0.15, 180: 0.1, 360: 0.05}
        total_w = 0.0
        agg = 0.0
        for w, wgt in weights.items():
            val = last.get(f"{col}_pct_{w}")
            if pd.notnull(val):
                agg += float(val) * wgt
                total_w += wgt
        if total_w > 0:
            momentum_comp = clip(agg / total_w, -0.5, 0.5)

        # Daily momentum: weighted average per-day change
        total_w = 0.0
        agg = 0.0
        for w, wgt in weights.items():
            val = last.get(f"{col}_per_day_{w}")
            if pd.notnull(val):
                agg += float(val) * wgt
                total_w += wgt
        if total_w > 0:
            momentum_daily_comp = clip(agg / total_w, -0.01, 0.01)

        # Supertrend component: direction 1/-1 scaled by relative distance of price to supertrend
        st = last.get(f"{col}_supertrend")
        st_dir = last.get(f"{col}_supertrend_dir")
        if pd.notnull(st) and pd.notnull(price) and pd.notnull(st_dir) and price:
            rel = clip((float(price) - float(st)) / float(price), -0.2, 0.2)
            supertrend_comp = rel * float(st_dir)

        # Combine with weights
        components["ema_price"] = criteria.w_ema_cross * ema_price_comp
        components["ema_cross"] = components.get("ema_cross", 0.0) + criteria.w_ema_cross * ema_cross_comp
        components["macd"] = components.get("macd", 0.0) + criteria.w_macd * macd_comp
        components["rsi"] = components.get("rsi", 0.0) + criteria.w_rsi * rsi_comp
        components["momentum"] = criteria.w_momentum * momentum_comp
        components["momentum_daily"] = criteria.w_momentum_daily * momentum_daily_comp
        components["supertrend"] = criteria.w_supertrend * supertrend_comp

        score = sum(components.values())

        # Decide recommendation by thresholds on net score
        if score >= criteria.score_buy_threshold:
            return EtfSuggestion(recommendation="buy", reasons=reasons), score, components
        if score <= -criteria.score_sell_threshold:
            return EtfSuggestion(recommendation="sell", reasons=reasons), score, components

        return EtfSuggestion(recommendation="hold", reasons=reasons), score, components


