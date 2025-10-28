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
    # Weights for weighted scanning - dynamically settable
    w_ema_cross: float = 0.0
    w_macd: float = 0.0
    w_rsi: float = 0.0
    w_momentum: float = 0.0
    w_momentum_daily: float = 0.0
    w_supertrend: float = 0.0
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
    indicator_details: Dict = field(default_factory=dict)  # Per-indicator grouped details


