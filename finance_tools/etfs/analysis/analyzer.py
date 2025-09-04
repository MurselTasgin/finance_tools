# finance_tools/etfs/analysis/analyzer.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd

from ...logging import get_logger
from .types import IndicatorRequest, IndicatorResult
from .retriever import EtfDataRetriever
from .filters import TitleFilter
from .indicators import TechnicalIndicatorCalculator


@dataclass
class EtfAnalyzer:
    """Coordinates ETF analysis: data retrieval, filtering, indicators."""

    retriever: EtfDataRetriever = field(default_factory=EtfDataRetriever)
    title_filter: TitleFilter = field(default_factory=TitleFilter)
    indicator_calculator: TechnicalIndicatorCalculator = field(default_factory=TechnicalIndicatorCalculator)

    def __post_init__(self):
        self.logger = get_logger("etf_analyzer")

    def analyze(self, request: IndicatorRequest) -> List[IndicatorResult]:
        df = self.retriever.fetch_info(
            codes=request.codes,
            start=request.start,
            end=request.end,
            include_keywords=(request.keyword_filter.include_keywords if request.keyword_filter else None),
            exclude_keywords=(request.keyword_filter.exclude_keywords if request.keyword_filter else None),
            case_sensitive=(request.keyword_filter.case_sensitive if request.keyword_filter else False),
            match_all_includes=(request.keyword_filter.match_all_includes if request.keyword_filter else False),
        )

        df = self.title_filter.apply(df, request.keyword_filter)

        if df is None or df.empty:
            return []

        # Compute indicators per code
        results: List[IndicatorResult] = []
        for code, g in df.groupby("code", sort=True):
            g_sorted = g.sort_values("date").reset_index(drop=True)
            enriched = self.indicator_calculator.compute(g_sorted, request.column, request.indicators)
            results.append(IndicatorResult(code=code, data=enriched))

        return results


