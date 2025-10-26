# finance_tools/stocks/analysis/analyzer.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd

from ...logging import get_logger
from .types import StockIndicatorRequest, StockIndicatorResult
from .retriever import StockDataRetriever
from .indicators import StockTechnicalIndicatorCalculator


@dataclass
class StockAnalyzer:
    """Coordinates stock analysis: data retrieval, filtering, indicators."""

    retriever: StockDataRetriever = field(default_factory=StockDataRetriever)
    indicator_calculator: StockTechnicalIndicatorCalculator = field(default_factory=StockTechnicalIndicatorCalculator)

    def __post_init__(self):
        self.logger = get_logger("stock_analyzer")

    def analyze(self, request: StockIndicatorRequest) -> List[StockIndicatorResult]:
        self.logger.info(f"🔍 Starting stock analysis - symbols: {request.symbols}, start: {request.start}, end: {request.end}")
        
        df = self.retriever.fetch_info(
            symbols=request.symbols,
            start=request.start,
            end=request.end,
            sector=(request.sector if request.sector else None),
            industry=(request.industry if request.industry else None),
        )

        self.logger.info(f"🔍 Retrieved DataFrame with {len(df)} rows, {df['symbol'].nunique() if not df.empty else 0} symbols")

        if df is None or df.empty:
            self.logger.warning("⚠️ No data retrieved for analysis")
            return []

        # Compute indicators per symbol
        results: List[StockIndicatorResult] = []
        for symbol, g in df.groupby("symbol", sort=True):
            g_sorted = g.sort_values("date").reset_index(drop=True)
            self.logger.info(f"🔍 Computing indicators for {symbol} - {len(g_sorted)} rows")
            enriched = self.indicator_calculator.compute(g_sorted, request.column, request.indicators)
            self.logger.info(f"🔍 Computed indicators for {symbol} - enriched DataFrame has {len(enriched)} rows, {len(enriched.columns)} columns")
            results.append(StockIndicatorResult(symbol=symbol, data=enriched))

        self.logger.info(f"🔍 Analysis complete - {len(results)} symbol results")
        return results

