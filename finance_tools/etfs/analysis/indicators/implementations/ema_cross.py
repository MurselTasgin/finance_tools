# finance_tools/etfs/analysis/indicators/implementations/ema_cross.py
from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
from ..base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
from ..registry import registry
from ta.trend import EMAIndicator


class EMACrossIndicator(BaseIndicator):
    """EMA Crossover indicator for ETFs"""
    
    def __init__(self):
        # Register on instantiation
        registry.register(self)
    
    def get_id(self) -> str:
        return "ema_cross"
    
    def get_name(self) -> str:
        return "EMA Crossover"
    
    def get_description(self) -> str:
        return "Detects when short-term EMA crosses above/below long-term EMA"
    
    def get_required_columns(self) -> List[str]:
        return ['price']  # ETFs use 'price' instead of 'close'
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'short': {
                'type': 'integer',
                'default': 20,
                'min': 5,
                'max': 200,
                'description': 'Short-term EMA period'
            },
            'long': {
                'type': 'integer',
                'default': 50,
                'min': 10,
                'max': 500,
                'description': 'Long-term EMA period'
            }
        }
    
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        """Calculate EMA and cross signals"""
        params = config.parameters
        short_period = int(params.get('short', 20))
        long_period = int(params.get('long', 50))
        
        series = df[column].astype(float)
        
        # Calculate EMAs
        ema_short = EMAIndicator(close=series, window=short_period, fillna=False).ema_indicator()
        ema_long = EMAIndicator(close=series, window=long_period, fillna=False).ema_indicator()
        
        result = df.copy()
        result[f"{column}_ema_{short_period}"] = ema_short
        result[f"{column}_ema_{long_period}"] = ema_long
        
        # Cross signals
        prev_diff = (ema_short - ema_long).shift(1)
        curr_diff = (ema_short - ema_long)
        
        result[f"{column}_ema_{short_period}_{long_period}_cross_up"] = (
            (prev_diff <= 0) & (curr_diff > 0)
        ).astype(int)
        result[f"{column}_ema_{short_period}_{long_period}_cross_down"] = (
            (prev_diff >= 0) & (curr_diff < 0)
        ).astype(int)
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        """Extract current values"""
        params = config.parameters
        short_period = int(params.get('short', 20))
        long_period = int(params.get('long', 50))
        
        last_row = df.iloc[-1]
        snapshot = {}
        
        for period in [short_period, long_period]:
            col_name = f"{column}_ema_{period}"
            val = last_row.get(col_name)
            if pd.notnull(val):
                snapshot[col_name] = float(val)
        
        return IndicatorSnapshot(values=snapshot)
    
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        """Calculate score based on price position relative to EMAs"""
        if config.weight <= 0:
            return None
        
        params = config.parameters
        short_period = int(params.get('short', 20))
        long_period = int(params.get('long', 50))
        
        last_row = df.iloc[-1]
        price = last_row.get(column)
        ema_short = last_row.get(f"{column}_ema_{short_period}")
        ema_long = last_row.get(f"{column}_ema_{long_period}")
        
        if not all(pd.notnull([price, ema_short, ema_long])) or price == 0:
            return None
        
        # Score components
        price_comp = 0.0
        if ema_short and ema_short > 0:
            price_comp = (float(price) - float(ema_short)) / float(ema_short)
            # Clamp to reasonable range
            price_comp = max(-0.1, min(0.1, price_comp))
        
        cross_comp = 0.0
        if ema_long and ema_long > 0:
            cross_comp = (float(ema_short) - float(ema_long)) / float(ema_long)
            # Clamp to reasonable range
            cross_comp = max(-0.1, min(0.1, cross_comp))
        
        # Weighted average
        raw = (price_comp * 0.5) + (cross_comp * 0.5)
        contribution = raw * config.weight

        explanation = f"Price position: {price_comp:.3f}, EMA cross: {cross_comp:.3f}"

        # Detailed calculation steps
        calculation_details = [
            f"Step 1: Price Position Score = (Price - EMA{short_period}) / EMA{short_period}",
            f"        = ({float(price):.2f} - {float(ema_short):.2f}) / {float(ema_short):.2f}",
            f"        = {price_comp:.4f}",
            "",
            f"Step 2: EMA Cross Score = (EMA{short_period} - EMA{long_period}) / EMA{long_period}",
            f"        = ({float(ema_short):.2f} - {float(ema_long):.2f}) / {float(ema_long):.2f}",
            f"        = {cross_comp:.4f}",
            "",
            f"Step 3: Raw Score = (Price Position × 0.5) + (EMA Cross × 0.5)",
            f"        = ({price_comp:.4f} × 0.5) + ({cross_comp:.4f} × 0.5)",
            f"        = {raw:.4f}",
            "",
            f"Step 4: Final Contribution = Raw Score × Weight",
            f"        = {raw:.4f} × {config.weight:.2f}",
            f"        = {contribution:.4f}"
        ]

        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=explanation,
            calculation_details=calculation_details
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        """Generate explanation"""
        params = config.parameters
        short_period = int(params.get('short', 20))
        long_period = int(params.get('long', 50))
        
        last_row = df.iloc[-1]
        
        price = last_row.get(column)
        ema_short = last_row.get(f"{column}_ema_{short_period}")
        ema_long = last_row.get(f"{column}_ema_{long_period}")
        
        lines = []
        lines.append(f"📈 EMA {short_period}/{long_period} Analysis:")
        
        if not all(pd.notnull([price, ema_short, ema_long])):
            lines.append("  ⚠️ Insufficient data")
            return lines
        
        # Cross status
        cross_up = last_row.get(f"{column}_ema_{short_period}_{long_period}_cross_up")
        cross_down = last_row.get(f"{column}_ema_{short_period}_{long_period}_cross_down")
        
        if cross_up == 1:
            lines.append(f"  ✅ BULLISH CROSS: EMA {short_period} crossed above EMA {long_period}")
        elif cross_down == 1:
            lines.append(f"  ❌ BEARISH CROSS: EMA {short_period} crossed below EMA {long_period}")
        else:
            lines.append(f"  ➖ NO CROSS: No recent crossover detected")
        
        # Price vs EMAs
        price_float = float(price) if pd.notnull(price) else 0
        ema_short_float = float(ema_short) if pd.notnull(ema_short) else 0
        ema_long_float = float(ema_long) if pd.notnull(ema_long) else 0
        
        if price_float > ema_short_float:
            lines.append(f"  ✅ Price ({price_float:.2f}) above EMA {short_period} ({ema_short_float:.2f})")
        else:
            lines.append(f"  ❌ Price ({price_float:.2f}) below EMA {short_period} ({ema_short_float:.2f})")
        
        # Trend
        if ema_short_float > ema_long_float:
            lines.append(f"  📈 UPTREND: Short-term EMA above long-term EMA")
        else:
            lines.append(f"  📉 DOWNTREND: Short-term EMA below long-term EMA")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['provides_buy_signal', 'provides_sell_signal', 'provides_trend_direction']
    
    def get_suggestions(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[str]:
        """Return buy/sell/hold suggestion"""
        params = config.parameters
        short_period = int(params.get('short', 20))
        long_period = int(params.get('long', 50))
        
        last_row = df.iloc[-1]
        
        cross_up = last_row.get(f"{column}_ema_{short_period}_{long_period}_cross_up")
        cross_down = last_row.get(f"{column}_ema_{short_period}_{long_period}_cross_down")
        
        if cross_up == 1:
            return "buy"
        elif cross_down == 1:
            return "sell"
        return "hold"


# Instantiate to register
_ = EMACrossIndicator()

