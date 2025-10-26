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
    # Weights for weighted scanning
    w_ema_cross: float = 1.0
    w_macd: float = 1.0
    w_rsi: float = 1.0
    w_momentum: float = 1.0
    w_momentum_daily: float = 1.0
    w_supertrend: float = 1.0
    w_volume: float = 1.0
    w_stochastic: float = 1.0
    w_atr: float = 1.0
    w_adx: float = 1.0
    score_buy_threshold: float = 1.0
    score_sell_threshold: float = 1.0


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

