# finance_tools/stocks/analysis/scanner_types.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class StockScanCriteria:
    column: str = "close"
    # EMA parameters
    ema_short: int = 20
    ema_long: int = 50
    # MACD parameters
    macd_slow: int = 26
    macd_fast: int = 12
    macd_sign: int = 9
    # RSI parameters
    rsi_window: int = 14
    rsi_lower: float = 30.0
    rsi_upper: float = 70.0
    # Volume parameters
    volume_window: int = 20
    # Stochastic parameters
    stoch_k_period: int = 14
    stoch_d_period: int = 3
    # ATR parameters
    atr_window: int = 14
    # ADX parameters
    adx_window: int = 14
    # EMA regime parameters
    ema_fast: int = 20
    ema_slow: int = 50
    ema_regime: int = 200
    max_ext_atr: float = 1.5
    min_vol_mult: float = 1.2
    vol_sma_period: int = 20
    # Weights for weighted scanning - dynamically settable
    score_buy_threshold: float = 1.0
    score_sell_threshold: float = 1.0
    
    def __post_init__(self):
        """Allow dynamic weight attributes to be set"""
        pass
    
    def get_weight(self, indicator_id: str) -> float:
        """Get weight for an indicator dynamically"""
        weight_attr = f"w_{indicator_id}"
        return getattr(self, weight_attr, 0.0)
    
    def set_weight(self, indicator_id: str, weight: float):
        """Set weight for an indicator dynamically"""
        weight_attr = f"w_{indicator_id}"
        setattr(self, weight_attr, weight)


@dataclass
class StockSuggestion:
    recommendation: str  # "buy" | "sell" | "hold"
    reasons: List[str] = field(default_factory=list)


@dataclass
class StockScanResult:
    symbol: str
    timestamp: Optional[datetime]
    last_value: Optional[float]
    suggestion: StockSuggestion
    score: float = 0.0
    indicators_snapshot: Dict[str, float] = field(default_factory=dict)
    components: Dict[str, float] = field(default_factory=dict)
    indicator_details: Dict = field(default_factory=dict)  # Per-indicator grouped details

