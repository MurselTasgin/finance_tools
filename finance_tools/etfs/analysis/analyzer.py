# finance_tools/etfs/analysis/analyzer.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd

from ...logging import get_logger
from .types import IndicatorRequest, IndicatorResult
from .retriever import EtfDataRetriever
from .filters import TitleFilter
from ...analysis.indicators import registry as unified_indicator_registry, IndicatorConfig


@dataclass
class EtfAnalyzer:
    """Coordinates ETF analysis: data retrieval, filtering, indicators."""

    retriever: EtfDataRetriever = field(default_factory=EtfDataRetriever)
    title_filter: TitleFilter = field(default_factory=TitleFilter)

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
            fund_type=request.fund_type,
        )

        df = self.title_filter.apply(df, request.keyword_filter)

        if df is None or df.empty:
            return []

        # Compute indicators per code using plugin-based system
        results: List[IndicatorResult] = []
        for code, g in df.groupby("code", sort=True):
            g_sorted = g.sort_values("date").reset_index(drop=True)
            
            # Use plugin-based indicators
            enriched = self._compute_indicators(g_sorted, request.column, request.indicators)
            results.append(IndicatorResult(code=code, data=enriched))

        return results
    
    def _compute_indicators(self, df: pd.DataFrame, column: str, indicators: Dict[str, Dict]) -> pd.DataFrame:
        """Compute indicators using the plugin-based system"""
        if df is None or df.empty or column not in df.columns:
            return df
        
        result = df.copy()
        
        # Process each indicator configuration
        for indicator_name, params in indicators.items():
            indicator = unified_indicator_registry.get(indicator_name)
            if indicator is None:
                self.logger.warning(f"⚠️ Unknown indicator: {indicator_name}")
                continue

            if "etf" not in indicator.get_asset_types():
                self.logger.warning(f"⚠️ Indicator {indicator_name} does not support ETF asset type")
                continue
            
            # Create indicator config
            config = IndicatorConfig(
                name=indicator.get_name(),
                parameters=params,
                weight=0  # Not used for analysis, only for scanning
            )
            
            try:
                result = indicator.calculate(result, column, config)
            except Exception as e:
                self.logger.error(f"Error calculating {indicator_name}: {e}")
        
        return result

