# finance_tools/etfs/analysis/scanner_types.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class EtfScanCriteria:
    column: str = "price"
    ema_short: int = 20
    ema_long: int = 50
    macd_slow: int = 26
    macd_fast: int = 12
    macd_sign: int = 9
    rsi_window: int = 14
    rsi_lower: float = 30.0
    rsi_upper: float = 70.0
    # Weights for weighted scanning
    w_ema_cross: float = 1.0
    w_macd: float = 1.0
    w_rsi: float = 1.0
    w_momentum: float = 1.0
    w_momentum_daily: float = 1.0
    w_supertrend: float = 1.0
    score_buy_threshold: float = 1.0
    score_sell_threshold: float = 1.0


@dataclass
class EtfSuggestion:
    recommendation: str  # "buy" | "sell" | "hold"
    reasons: List[str] = field(default_factory=list)


@dataclass
class EtfScanResult:
    code: str
    timestamp: Optional[datetime]
    last_value: Optional[float]
    suggestion: EtfSuggestion
    score: float = 0.0
    indicators_snapshot: Dict[str, float] = field(default_factory=dict)
    components: Dict[str, float] = field(default_factory=dict)


