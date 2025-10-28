# finance_tools/etfs/analysis/__init__.py
"""
ETF analysis package for TEFAS data.

Provides abstractions for data retrieval, filtering by title keywords,
and computing technical indicators (EMA, RSI, MACD, etc.) on selected
numeric columns like `price`, `market_cap`, `number_of_investors`,
and `number_of_shares`.

Now uses plugin-based indicators like stock analysis.
"""

from .types import IndicatorRequest, IndicatorResult, KeywordFilter
from .retriever import EtfDataRetriever
from .filters import TitleFilter
from .analyzer import EtfAnalyzer
from .scanner import EtfScanner
from .scanner_types import EtfScanCriteria, EtfScanResult, EtfSuggestion
from .indicators import registry, IndicatorRegistry
from .indicators.base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore

__all__ = [
    "IndicatorRequest",
    "IndicatorResult",
    "KeywordFilter",
    "EtfDataRetriever",
    "TitleFilter",
    "EtfAnalyzer",
    "EtfScanner",
    "EtfScanCriteria",
    "EtfScanResult",
    "EtfSuggestion",
    "registry",
    "IndicatorRegistry",
    "BaseIndicator",
    "IndicatorConfig",
    "IndicatorSnapshot",
    "IndicatorScore",
]


