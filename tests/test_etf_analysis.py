# tests/test_etf_analysis.py
import os
from datetime import date, timedelta

import pandas as pd

from finance_tools.config import get_config
from finance_tools.etfs.tefas.repository import DatabaseEngineProvider, TefasRepository
from finance_tools.etfs.analysis import EtfAnalyzer, IndicatorRequest, KeywordFilter


def seed_in_memory_db():
    cfg = get_config()
    os.environ["DATABASE_TYPE"] = "sqlite"
    os.environ["DATABASE_NAME"] = ":memory:"
    cfg.reload()

    provider = DatabaseEngineProvider()
    provider.ensure_initialized()
    SessionLocal = provider.get_session_factory()
    with SessionLocal() as session:
        repo = TefasRepository(session)
        today = date(2024, 1, 10)
        rows = []
        # GOLD-themed ETF (should match include 'gold')
        for i, p in enumerate([10.0, 10.5, 11.0, 10.8, 11.2], start=0):
            rows.append(
                {
                    "date": today - timedelta(days=(4 - i)),
                    "code": "GLD",
                    "price": p,
                    "title": "Global Gold Fund",
                    "market_cap": 1000.0 + i,
                    "number_of_shares": 100.0 + i,
                    "number_of_investors": 50.0 + i,
                }
            )
        # USD-themed ETF (should be excluded by exclude 'usd')
        for i, p in enumerate([20.0, 19.8, 20.2, 20.5, 20.3], start=0):
            rows.append(
                {
                    "date": today - timedelta(days=(4 - i)),
                    "code": "USDX",
                    "price": p,
                    "title": "USD Index Fund",
                    "market_cap": 2000.0 + i,
                    "number_of_shares": 200.0 + i,
                    "number_of_investors": 75.0 + i,
                }
            )
        repo.upsert_fund_info_many(rows)


def test_etf_analyzer_with_keyword_filters():
    seed_in_memory_db()
    analyzer = EtfAnalyzer()

    request = IndicatorRequest(
        codes=None,
        start=date(2024, 1, 6),
        end=date(2024, 1, 10),
        column="price",
        indicators={
            "ema": {"window": 3},
            "rsi": {"window": 2},
            "macd": {"window_slow": 4, "window_fast": 2, "window_sign": 2},
        },
        keyword_filter=KeywordFilter(include_keywords=["gold"], exclude_keywords=["usd"]),
    )

    results = analyzer.analyze(request)
    # Only GLD should remain due to filters
    codes = {r.code for r in results}
    assert codes == {"GLD"}
    assert len(results) == 1

    df = results[0].data
    # Check indicator columns exist
    assert "price_ema_3" in df.columns
    assert any(c.startswith("price_rsi_") for c in df.columns)
    assert {"price_macd", "price_macd_signal", "price_macd_diff"}.issubset(df.columns)


