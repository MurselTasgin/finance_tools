# finance_tools/etfs/analysis/types.py
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
class IndicatorRequest:
    codes: Optional[Sequence[str]]
    start: Optional[date]
    end: Optional[date]
    column: str  # e.g., "price", "market_cap", "number_of_investors", "number_of_shares"
    indicators: Dict[str, Dict]  # e.g., {"ema": {"window": 20}, "rsi": {"window": 14}}
    keyword_filter: Optional[KeywordFilter] = None


@dataclass
class IndicatorResult:
    code: str
    data: "pandas.DataFrame"


