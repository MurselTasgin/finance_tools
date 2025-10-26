# finance_tools/stocks/analysis/types.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Sequence


@dataclass
class KeywordFilter:
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    case_sensitive: bool = False
    match_all_includes: bool = False


@dataclass
class StockIndicatorRequest:
    symbols: Optional[Sequence[str]]
    start: Optional[date]
    end: Optional[date]
    column: str  # e.g., "close", "volume"
    indicators: Dict[str, Dict]  # e.g., {"ema": {"window": 20}, "rsi": {"window": 14}}
    keyword_filter: Optional[KeywordFilter] = None
    sector: Optional[str] = None  # Filter by sector
    industry: Optional[str] = None  # Filter by industry


@dataclass
class StockIndicatorResult:
    symbol: str
    data: "pandas.DataFrame"

