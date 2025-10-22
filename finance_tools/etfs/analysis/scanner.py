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
            # Build indicators based on non-zero weights (selected scanners only)
            indicators = {}
            if criteria.w_ema_cross > 0:
                indicators["ema"] = {"windows": [criteria.ema_short, criteria.ema_long]}
                indicators["ema_cross"] = {"short": criteria.ema_short, "long": criteria.ema_long}
            if criteria.w_macd > 0:
                indicators["macd"] = {
                    "window_slow": criteria.macd_slow,
                    "window_fast": criteria.macd_fast,
                    "window_sign": criteria.macd_sign,
                }
            if criteria.w_rsi > 0:
                indicators["rsi"] = {"window": criteria.rsi_window}
            if criteria.w_momentum > 0:
                indicators["momentum"] = {"windows": [30, 60, 90, 180, 360]}
            if criteria.w_momentum_daily > 0:
                indicators["daily_momentum"] = {"windows": [30, 60, 90, 180, 360]}
            if criteria.w_supertrend > 0:
                indicators["supertrend"] = {"hl_factor": 0.05, "atr_period": 10, "multiplier": 3.0}
            
            enriched = self.indicator_calculator.compute(
                df,
                criteria.column,
                indicators=indicators,
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

        # Price and EMA values
        price = float(last.get(col)) if pd.notnull(last.get(col)) else None
        ema_s = last.get(f"{col}_ema_{criteria.ema_short}")
        ema_l = last.get(f"{col}_ema_{criteria.ema_long}")

        # Build comprehensive analysis reasons
        reasons.append("=" * 60)
        reasons.append("🔍 DETAILED TECHNICAL ANALYSIS")
        reasons.append("=" * 60)

        # EMA Analysis Section
        reasons.append("")
        reasons.append("📈 EMA (Exponential Moving Average) Analysis:")
        if cross_up:
            reasons.append(f"  ✅ BULLISH CROSSOVER: EMA {criteria.ema_short} crossed above EMA {criteria.ema_long}")
        elif cross_down:
            reasons.append(f"  ❌ BEARISH CROSSOVER: EMA {criteria.ema_short} crossed below EMA {criteria.ema_long}")
        else:
            reasons.append(f"  ➖ NO CROSSOVER: No recent EMA crossover detected")
        
        if pd.notnull(ema_s) and pd.notnull(price) and price > 0:
            if price > ema_s:
                reasons.append(f"  ✅ PRICE POSITION: Price ({price:.2f}) above EMA {criteria.ema_short} ({ema_s:.2f})")
            else:
                reasons.append(f"  ❌ PRICE POSITION: Price ({price:.2f}) below EMA {criteria.ema_short} ({ema_s:.2f})")
        
        if pd.notnull(ema_s) and pd.notnull(ema_l):
            if ema_s > ema_l:
                reasons.append(f"  📈 TREND: Short-term EMA above long-term EMA (UPTREND)")
            else:
                reasons.append(f"  📉 TREND: Short-term EMA below long-term EMA (DOWNTREND)")

        # MACD Analysis Section
        reasons.append("")
        reasons.append("📊 MACD (Moving Average Convergence Divergence) Analysis:")
        if pd.notnull(macd) and pd.notnull(macd_signal):
            if macd_above and macd_rising:
                reasons.append(f"  ✅ BULLISH: MACD ({macd:.4f}) above signal ({macd_signal:.4f}) and rising")
            elif macd_above and not macd_rising:
                reasons.append(f"  ⚠️ NEUTRAL: MACD ({macd:.4f}) above signal ({macd_signal:.4f}) but not rising")
            else:
                reasons.append(f"  ❌ BEARISH: MACD ({macd:.4f}) below signal ({macd_signal:.4f})")
        else:
            reasons.append(f"  ⚠️ INSUFFICIENT DATA: MACD analysis not available")

        # RSI Analysis Section
        reasons.append("")
        reasons.append("📊 RSI (Relative Strength Index) Analysis:")
        if pd.notnull(rsi):
            if rsi_oversold:
                reasons.append(f"  🚀 OVERSOLD: RSI ({rsi:.1f}) below {criteria.rsi_lower} - Strong BUY signal")
            elif rsi_overbought:
                reasons.append(f"  🔻 OVERBOUGHT: RSI ({rsi:.1f}) above {criteria.rsi_upper} - Strong SELL signal")
            elif rsi > 50:
                reasons.append(f"  📈 BULLISH: RSI ({rsi:.1f}) above 50 - Positive momentum")
            else:
                reasons.append(f"  📉 BEARISH: RSI ({rsi:.1f}) below 50 - Negative momentum")
        else:
            reasons.append(f"  ⚠️ INSUFFICIENT DATA: RSI analysis not available")

        # Continuous scoring components
        def clip(v: float, lo: float, hi: float) -> float:
            return float(min(max(v, lo), hi))

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

        # Combine with weights - only include selected scanners
        if criteria.w_ema_cross > 0:
            components["ema_price"] = criteria.w_ema_cross * ema_price_comp
            components["ema_cross"] = components.get("ema_cross", 0.0) + criteria.w_ema_cross * ema_cross_comp
        if criteria.w_macd > 0:
            components["macd"] = components.get("macd", 0.0) + criteria.w_macd * macd_comp
        if criteria.w_rsi > 0:
            components["rsi"] = components.get("rsi", 0.0) + criteria.w_rsi * rsi_comp
        if criteria.w_momentum > 0:
            components["momentum"] = criteria.w_momentum * momentum_comp
        if criteria.w_momentum_daily > 0:
            components["momentum_daily"] = criteria.w_momentum_daily * momentum_daily_comp
        if criteria.w_supertrend > 0:
            components["supertrend"] = criteria.w_supertrend * supertrend_comp

        score = sum(components.values())

        # Add comprehensive score analysis
        reasons.append("")
        reasons.append("=" * 60)
        reasons.append("📊 SCORE CALCULATION & ANALYSIS")
        reasons.append("=" * 60)
        reasons.append(f"Total Calculated Score: {score:.3f}")
        reasons.append("")
        reasons.append("Scanner Contributions (Component × Weight = Contribution):")
        
        # Add each component's contribution with detailed analysis (only selected scanners)
        for component_name, contribution in components.items():
            weight = getattr(criteria, f"w_{component_name}", 0.0)
            raw_value = contribution / weight if weight > 0 else 0.0
            
            # Only show components that were actually selected (have non-zero weights)
            if weight > 0:
                status = "✅ ACTIVE" if abs(contribution) > 0.001 else "➖ NEUTRAL"
                reasons.append(f"  • {component_name.replace('_', ' ').title()}: {raw_value:.3f} × {weight} = {contribution:.3f} {status}")
            # Note: We no longer show INACTIVE components since they're not in the components dict

        # Add threshold analysis
        reasons.append("")
        reasons.append("🎯 THRESHOLD ANALYSIS:")
        reasons.append(f"  • Buy Threshold: {criteria.score_buy_threshold}")
        reasons.append(f"  • Sell Threshold: -{criteria.score_sell_threshold}")
        reasons.append(f"  • Current Score: {score:.3f}")

        # Decide recommendation by thresholds on net score
        if score >= criteria.score_buy_threshold:
            reasons.append("")
            reasons.append("🚀 FINAL RECOMMENDATION: BUY")
            reasons.append(f"Reason: Score {score:.3f} >= Buy Threshold {criteria.score_buy_threshold}")
            reasons.append("Confidence: High - Multiple bullish signals detected")
            return EtfSuggestion(recommendation="buy", reasons=reasons), score, components
        elif score <= -criteria.score_sell_threshold:
            reasons.append("")
            reasons.append("🔻 FINAL RECOMMENDATION: SELL")
            reasons.append(f"Reason: Score {score:.3f} <= Sell Threshold {-criteria.score_sell_threshold}")
            reasons.append("Confidence: High - Multiple bearish signals detected")
            return EtfSuggestion(recommendation="sell", reasons=reasons), score, components
        else:
            reasons.append("")
            reasons.append("⏸️ FINAL RECOMMENDATION: HOLD")
            reasons.append(f"Reason: Score {score:.3f} between Sell Threshold {-criteria.score_sell_threshold} and Buy Threshold {criteria.score_buy_threshold}")
            reasons.append("Confidence: Medium - Mixed signals, wait for clearer direction")
            return EtfSuggestion(recommendation="hold", reasons=reasons), score, components


