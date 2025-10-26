# finance_tools/stocks/analysis/scanner.py
from __future__ import annotations

from typing import List, Dict

import pandas as pd

from ...logging import get_logger
from .indicators import StockTechnicalIndicatorCalculator
from .scanner_types import StockScanCriteria, StockScanResult, StockSuggestion


class StockScanner:
    """Runs stock scans by computing indicators and deriving suggestions."""

    def __init__(self) -> None:
        self.logger = get_logger("stock_scanner")
        self.indicator_calculator = StockTechnicalIndicatorCalculator()

    def scan(self, symbol_to_df: Dict[str, pd.DataFrame], criteria: StockScanCriteria) -> List[StockScanResult]:
        self.logger.info(f"🔍 Starting scan for {len(symbol_to_df)} symbols with column: {criteria.column}")
        results: List[StockScanResult] = []
        for symbol, df in symbol_to_df.items():
            self.logger.info(f"🔍 Processing {symbol} - DataFrame shape: {df.shape if df is not None else 'None'}, columns: {list(df.columns) if df is not None and not df.empty else 'empty'}")
            if df is None or df.empty:
                self.logger.warning(f"⚠️ Skipping {symbol} - DataFrame is empty")
                continue
            if criteria.column not in df.columns:
                self.logger.warning(f"⚠️ Skipping {symbol} - Column '{criteria.column}' not found in DataFrame. Available columns: {list(df.columns)}")
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
            if criteria.w_volume > 0:
                indicators["volume_obv"] = {}
                indicators["volume_sma"] = {"window": criteria.volume_window}
            if criteria.w_stochastic > 0:
                indicators["stochastic"] = {
                    "k_period": criteria.stoch_k_period,
                    "d_period": criteria.stoch_d_period
                }
            if criteria.w_atr > 0:
                indicators["atr"] = {"window": criteria.atr_window}
            if criteria.w_adx > 0:
                indicators["adx"] = {"window": criteria.adx_window}
            
            self.logger.info(f"🔍 Computing indicators for {symbol} - weights: w_macd={criteria.w_macd}, w_volume={criteria.w_volume}, w_stochastic={criteria.w_stochastic}")
            self.logger.debug(f"🔍 Indicators dict: {indicators}")
            
            enriched = self.indicator_calculator.compute(
                df,
                criteria.column,
                indicators=indicators,
            )
            
            self.logger.debug(f"🔍 Enriched DataFrame columns: {list(enriched.columns)}")
            suggestion, score, components = self._derive_suggestion_and_score(enriched, criteria)
            last_row = enriched.iloc[-1]
            
            # Build snapshot inline like ETF scanner - only include valid float values
            snapshot = {}
            col = criteria.column
            
            # EMA values
            if criteria.w_ema_cross > 0:
                ema_short_val = last_row.get(f"{col}_ema_{criteria.ema_short}")
                if pd.notnull(ema_short_val):
                    snapshot[f"{col}_ema_{criteria.ema_short}"] = float(ema_short_val)
                ema_long_val = last_row.get(f"{col}_ema_{criteria.ema_long}")
                if pd.notnull(ema_long_val):
                    snapshot[f"{col}_ema_{criteria.ema_long}"] = float(ema_long_val)
            
            # MACD
            if criteria.w_macd > 0:
                macd_val = last_row.get(f"{col}_macd")
                self.logger.debug(f"🔍 MACD value for {symbol}: {macd_val}, column exists: {f'{col}_macd' in enriched.columns}")
                if pd.notnull(macd_val):
                    snapshot[f"{col}_macd"] = float(macd_val)
                macd_signal_val = last_row.get(f"{col}_macd_signal")
                if pd.notnull(macd_signal_val):
                    snapshot[f"{col}_macd_signal"] = float(macd_signal_val)
            
            # RSI
            if criteria.w_rsi > 0:
                rsi_val = last_row.get(f"{col}_rsi_{criteria.rsi_window}")
                if pd.notnull(rsi_val):
                    snapshot[f"{col}_rsi_{criteria.rsi_window}"] = float(rsi_val)
            
            # Volume
            if criteria.w_volume > 0:
                volume_sma_val = last_row.get(f"volume_sma_{criteria.volume_window}")
                self.logger.debug(f"🔍 Volume SMA value for {symbol}: {volume_sma_val}, column exists: {f'volume_sma_{criteria.volume_window}' in enriched.columns}")
                if pd.notnull(volume_sma_val):
                    snapshot[f"volume_sma_{criteria.volume_window}"] = float(volume_sma_val)
            
            # Stochastic
            if criteria.w_stochastic > 0:
                stoch_k_val = last_row.get(f"{col}_stoch_k")
                self.logger.debug(f"🔍 Stochastic K value for {symbol}: {stoch_k_val}, column exists: {f'{col}_stoch_k' in enriched.columns}")
                if pd.notnull(stoch_k_val):
                    snapshot[f"{col}_stoch_k"] = float(stoch_k_val)
            
            # ATR
            if criteria.w_atr > 0:
                atr_val = last_row.get(f"{col}_atr")
                if pd.notnull(atr_val):
                    snapshot[f"{col}_atr"] = float(atr_val)
            
            # ADX
            if criteria.w_adx > 0:
                adx_val = last_row.get(f"{col}_adx")
                if pd.notnull(adx_val):
                    snapshot[f"{col}_adx"] = float(adx_val)
            
            # Clean components - now they are dicts with raw, weight, contribution
            clean_components = {}
            for k, v in components.items():
                if isinstance(v, dict) and "contribution" in v:
                    # New format: store the full dict
                    clean_components[k] = v
            
            results.append(
                StockScanResult(
                    symbol=symbol,
                    timestamp=pd.to_datetime(last_row["date"]).to_pydatetime() if "date" in last_row else None,
                    last_value=float(last_row[criteria.column]) if pd.notnull(last_row[criteria.column]) else None,
                    suggestion=suggestion,
                    score=score,
                    indicators_snapshot=snapshot,
                    components=clean_components,
                )
            )
        # Sort by descending score
        results.sort(key=lambda r: r.score, reverse=True)
        return results
    
    def _build_snapshot(self, last_row: pd.Series, criteria: StockScanCriteria) -> Dict[str, float]:
        """Build snapshot of indicator values."""
        snapshot = {}
        col = criteria.column
        
        # Standard indicators
        for key, val in [
            (f"{col}_ema_{criteria.ema_short}", last_row.get(f"{col}_ema_{criteria.ema_short}")),
            (f"{col}_ema_{criteria.ema_long}", last_row.get(f"{col}_ema_{criteria.ema_long}")),
            (f"{col}_macd", last_row.get(f"{col}_macd")),
            (f"{col}_macd_signal", last_row.get(f"{col}_macd_signal")),
            (f"{col}_rsi_{criteria.rsi_window}", last_row.get(f"{col}_rsi_{criteria.rsi_window}")),
            (f"volume_sma_{criteria.volume_window}", last_row.get(f"volume_sma_{criteria.volume_window}")),
            (f"{col}_stoch_k", last_row.get(f"{col}_stoch_k")),
            (f"{col}_atr", last_row.get(f"{col}_atr")),
            (f"{col}_adx", last_row.get(f"{col}_adx")),
        ]:
            if pd.notnull(val):
                snapshot[key] = float(val)
        
        return snapshot

    def _derive_suggestion_and_score(self, df: pd.DataFrame, criteria: StockScanCriteria) -> tuple[StockSuggestion, float, Dict[str, float]]:
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

        # Volume analysis
        volume = last.get("volume") if "volume" in df.columns else None
        volume_sma = last.get(f"volume_sma_{criteria.volume_window}")
        
        # Debug: Log indicator availability
        self.logger.debug(f"Volume column exists: {'volume' in df.columns}")
        self.logger.debug(f"Volume SMA column exists: {f'volume_sma_{criteria.volume_window}' in df.columns}")
        if "volume" in df.columns:
            self.logger.debug(f"Volume value (last row): {volume}")
        if f"volume_sma_{criteria.volume_window}" in df.columns:
            self.logger.debug(f"Volume SMA value (last row): {volume_sma}")
        volume_comp = 0.0

        # Stochastic
        stoch_k = last.get(f"{col}_stoch_k")
        stoch_d = last.get(f"{col}_stoch_d")
        stochastic_comp = 0.0
        
        # Debug: Log stochastic availability
        self.logger.debug(f"Stochastic K column exists: {f'{col}_stoch_k' in df.columns}")
        self.logger.debug(f"Stochastic D column exists: {f'{col}_stoch_d' in df.columns}")
        if f"{col}_stoch_k" in df.columns:
            self.logger.debug(f"Stochastic K value (last row): {stoch_k}")
        if f"{col}_stoch_d" in df.columns:
            self.logger.debug(f"Stochastic D value (last row): {stoch_d}")

        # ATR (volatility)
        atr = last.get(f"{col}_atr")
        atr_comp = 0.0

        # ADX (trend strength)
        adx = last.get(f"{col}_adx")
        adx_comp = 0.0

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
        if criteria.w_macd <= 0:
            reasons.append(f"  ℹ️ Not selected by user (weight = {criteria.w_macd})")
        elif pd.notnull(macd) and pd.notnull(macd_signal):
            macd_histogram = float(macd) - float(macd_signal)
            macd_pct = (macd_histogram / price * 100) if price and price != 0 else 0.0
            if macd_above and macd_rising:
                reasons.append(f"  ✅ BULLISH: MACD ({macd:.4f}) > Signal ({macd_signal:.4f}), Histogram: {macd_histogram:+.4f} ({macd_pct:+.2f}% of price) - Rising")
            elif macd_above and not macd_rising:
                reasons.append(f"  ⚠️ NEUTRAL: MACD ({macd:.4f}) > Signal ({macd_signal:.4f}), Histogram: {macd_histogram:+.4f} ({macd_pct:+.2f}% of price) - Not rising")
            else:
                reasons.append(f"  ❌ BEARISH: MACD ({macd:.4f}) < Signal ({macd_signal:.4f}), Histogram: {macd_histogram:+.4f} ({macd_pct:+.2f}% of price)")
        else:
            reasons.append(f"  ⚠️ INSUFFICIENT DATA: MACD analysis not available")

        # RSI Analysis Section
        reasons.append("")
        reasons.append("📊 RSI (Relative Strength Index) Analysis:")
        if criteria.w_rsi <= 0:
            reasons.append(f"  ℹ️ Not selected by user (weight = {criteria.w_rsi})")
        elif pd.notnull(rsi):
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

        # Volume Analysis Section
        reasons.append("")
        reasons.append("📊 VOLUME Analysis:")
        if criteria.w_volume <= 0:
            reasons.append(f"  ℹ️ Not selected by user (weight = {criteria.w_volume})")
        elif pd.notnull(volume) and pd.notnull(volume_sma) and volume_sma > 0:
            volume_ratio = volume / volume_sma
            pct_change = (volume_ratio - 1.0) * 100
            if volume_ratio > 1.5:
                reasons.append(f"  ✅ HIGH VOLUME: Volume ({volume:.0f}) is {pct_change:+.1f}% vs SMA ({volume_sma:.0f}) - Strong conviction")
                volume_comp = 0.1
            elif volume_ratio > 1.2:
                reasons.append(f"  📈 ABOVE AVERAGE: Volume ({volume:.0f}) is {pct_change:+.1f}% vs SMA ({volume_sma:.0f})")
                volume_comp = 0.05
            elif volume_ratio < 0.9:
                reasons.append(f"  ⚠️ LOW VOLUME: Volume ({volume:.0f}) is {pct_change:+.1f}% vs SMA ({volume_sma:.0f}) - Weak conviction")
                volume_comp = -0.05
            else:
                reasons.append(f"  ➖ NORMAL: Volume ({volume:.0f}) is {pct_change:+.1f}% vs SMA ({volume_sma:.0f})")
        else:
            reasons.append(f"  ⚠️ INSUFFICIENT DATA: Volume analysis not available")

        # Stochastic Analysis Section
        reasons.append("")
        reasons.append("📊 STOCHASTIC Analysis:")
        if criteria.w_stochastic <= 0:
            reasons.append(f"  ℹ️ Not selected by user (weight = {criteria.w_stochastic})")
        elif pd.notnull(stoch_k) and pd.notnull(stoch_d):
            if stoch_k > 80:
                reasons.append(f"  🔻 OVERBOUGHT: Stochastic K ({stoch_k:.1f}) > 80 - Strong SELL signal")
                stochastic_comp = -0.15
            elif stoch_k < 20:
                reasons.append(f"  🚀 OVERSOLD: Stochastic K ({stoch_k:.1f}) < 20 - Strong BUY signal")
                stochastic_comp = 0.15
            elif stoch_k > stoch_d:
                reasons.append(f"  📈 BULLISH: K ({stoch_k:.1f}) above D ({stoch_d:.1f})")
                stochastic_comp = 0.05
            else:
                reasons.append(f"  📉 BEARISH: K ({stoch_k:.1f}) below D ({stoch_d:.1f})")
                stochastic_comp = -0.05
        else:
            reasons.append(f"  ⚠️ INSUFFICIENT DATA: Stochastic analysis not available")

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
            ema_price_comp = (price - float(ema_s)) / float(ema_s)
        if pd.notnull(ema_s) and pd.notnull(ema_l) and ema_l not in [0, None]:
            ema_cross_comp = (float(ema_s) - float(ema_l)) / float(ema_l)

        # MACD: Use histogram (MACD - Signal) as percentage of price for continuous scoring
        # Normalize by price to get comparable values across different price levels
        if pd.notnull(macd) and pd.notnull(macd_signal):
            histogram = float(macd) - float(macd_signal)
            denom = price if (price and price != 0) else 1.0
            # MACD histogram as percentage of price (e.g., 0.01 = 1% of price)
            macd_comp = histogram / float(denom)
        elif pd.notnull(macd_diff):
            denom = price if (price and price != 0) else 1.0
            # Use MACD diff directly as percentage of price
            macd_comp = float(macd_diff) / float(denom)

        if pd.notnull(rsi):
            rsi_comp = (float(rsi) - 50.0) / 50.0

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
            momentum_comp = agg / total_w

        # Daily momentum: weighted average per-day change
        total_w = 0.0
        agg = 0.0
        for w, wgt in weights.items():
            val = last.get(f"{col}_per_day_{w}")
            if pd.notnull(val):
                agg += float(val) * wgt
                total_w += wgt
        if total_w > 0:
            momentum_daily_comp = agg / total_w

        # Supertrend component
        st = last.get(f"{col}_supertrend")
        st_dir = last.get(f"{col}_supertrend_dir")
        if pd.notnull(st) and pd.notnull(price) and pd.notnull(st_dir) and price:
            rel = (float(price) - float(st)) / float(price)
            supertrend_comp = rel * float(st_dir)

        # ATR component (volatility - lower is better for bullish signals)
        if pd.notnull(atr) and pd.notnull(price) and price > 0:
            atr_pct = float(atr) / float(price)
            # Lower ATR percentage means less volatility (better for bullish)
            atr_comp = -atr_pct  # Inverted: lower volatility = positive contribution

        # ADX component (trend strength)
        if pd.notnull(adx):
            # ADX > 25 indicates strong trend, < 20 is weak trend
            if adx > 25:
                adx_comp = 0.1  # Strong trend
            elif adx > 20:
                adx_comp = 0.05  # Moderate trend
            else:
                adx_comp = -0.05  # Weak trend

        # Combine with weights - store detailed information for each component
        # Store as: { "indicator_name": {"raw": raw_value, "weight": weight, "contribution": weighted_value} }
        component_info = {}
        
        if criteria.w_ema_cross > 0 and (pd.notnull(ema_price_comp) or pd.notnull(ema_cross_comp)):
            if pd.notnull(ema_price_comp):
                component_info["ema_price"] = {
                    "raw": float(ema_price_comp),
                    "weight": criteria.w_ema_cross,
                    "contribution": float(criteria.w_ema_cross * ema_price_comp)
                }
            if pd.notnull(ema_cross_comp):
                component_info["ema_cross"] = {
                    "raw": float(ema_cross_comp),
                    "weight": criteria.w_ema_cross,
                    "contribution": float(criteria.w_ema_cross * ema_cross_comp)
                }
        
        if criteria.w_macd > 0 and pd.notnull(macd_comp):
            component_info["macd"] = {
                "raw": float(macd_comp),
                "weight": criteria.w_macd,
                "contribution": float(criteria.w_macd * macd_comp)
            }
        
        if criteria.w_rsi > 0 and pd.notnull(rsi_comp):
            component_info["rsi"] = {
                "raw": float(rsi_comp),
                "weight": criteria.w_rsi,
                "contribution": float(criteria.w_rsi * rsi_comp)
            }
        
        if criteria.w_momentum > 0 and pd.notnull(momentum_comp):
            component_info["momentum"] = {
                "raw": float(momentum_comp),
                "weight": criteria.w_momentum,
                "contribution": float(criteria.w_momentum * momentum_comp)
            }
        
        if criteria.w_momentum_daily > 0 and pd.notnull(momentum_daily_comp):
            component_info["momentum_daily"] = {
                "raw": float(momentum_daily_comp),
                "weight": criteria.w_momentum_daily,
                "contribution": float(criteria.w_momentum_daily * momentum_daily_comp)
            }
        
        if criteria.w_supertrend > 0 and pd.notnull(supertrend_comp):
            component_info["supertrend"] = {
                "raw": float(supertrend_comp),
                "weight": criteria.w_supertrend,
                "contribution": float(criteria.w_supertrend * supertrend_comp)
            }
        
        if criteria.w_volume > 0 and pd.notnull(volume_comp):
            component_info["volume"] = {
                "raw": float(volume_comp),
                "weight": criteria.w_volume,
                "contribution": float(criteria.w_volume * volume_comp)
            }
        
        if criteria.w_stochastic > 0 and pd.notnull(stochastic_comp):
            component_info["stochastic"] = {
                "raw": float(stochastic_comp),
                "weight": criteria.w_stochastic,
                "contribution": float(criteria.w_stochastic * stochastic_comp)
            }
        
        if criteria.w_atr > 0 and pd.notnull(atr_comp):
            component_info["atr"] = {
                "raw": float(atr_comp),
                "weight": criteria.w_atr,
                "contribution": float(criteria.w_atr * atr_comp)
            }
        
        if criteria.w_adx > 0 and pd.notnull(adx_comp):
            component_info["adx"] = {
                "raw": float(adx_comp),
                "weight": criteria.w_adx,
                "contribution": float(criteria.w_adx * adx_comp)
            }
        
        # Return the component info dict
        components = component_info

        # Calculate score from contributions
        score = sum([comp["contribution"] for comp in components.values()])

        # Add comprehensive score analysis
        reasons.append("")
        reasons.append("=" * 60)
        reasons.append("📊 SCORE CALCULATION & ANALYSIS")
        reasons.append("=" * 60)
        reasons.append(f"Total Calculated Score: {score:.3f}")
        reasons.append("")
        reasons.append("Scanner Contributions (Raw Value × Weight = Contribution):")
        
        for component_name, comp_data in components.items():
            raw_value = comp_data["raw"]
            weight = comp_data["weight"]
            contribution = comp_data["contribution"]
            
            if weight > 0:
                status = "✅ ACTIVE" if abs(contribution) > 0.001 else "➖ NEUTRAL"
                reasons.append(f"  • {component_name.replace('_', ' ').title()}: {raw_value:.3f} × {weight} = {contribution:.3f} {status}")

        reasons.append("")
        reasons.append("🎯 THRESHOLD ANALYSIS:")
        reasons.append(f"  • Buy Threshold: {criteria.score_buy_threshold}")
        reasons.append(f"  • Sell Threshold: -{criteria.score_sell_threshold}")
        reasons.append(f"  • Current Score: {score:.3f}")

        # Decide recommendation by thresholds
        if score >= criteria.score_buy_threshold:
            reasons.append("")
            reasons.append("🚀 FINAL RECOMMENDATION: BUY")
            reasons.append(f"Reason: Score {score:.3f} >= Buy Threshold {criteria.score_buy_threshold}")
            reasons.append("Confidence: High - Multiple bullish signals detected")
            return StockSuggestion(recommendation="buy", reasons=reasons), score, components
        elif score <= -criteria.score_sell_threshold:
            reasons.append("")
            reasons.append("🔻 FINAL RECOMMENDATION: SELL")
            reasons.append(f"Reason: Score {score:.3f} <= Sell Threshold {-criteria.score_sell_threshold}")
            reasons.append("Confidence: High - Multiple bearish signals detected")
            return StockSuggestion(recommendation="sell", reasons=reasons), score, components
        else:
            reasons.append("")
            reasons.append("⏸️ FINAL RECOMMENDATION: HOLD")
            reasons.append(f"Reason: Score {score:.3f} between Sell Threshold {-criteria.score_sell_threshold} and Buy Threshold {criteria.score_buy_threshold}")
            reasons.append("Confidence: Medium - Mixed signals, wait for clearer direction")
            return StockSuggestion(recommendation="hold", reasons=reasons), score, components

