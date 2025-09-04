# finance_tools/etfs/analysis/retriever.py
from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, List, Optional, Sequence

import pandas as pd

from ...logging import get_logger
from ..tefas.repository import DatabaseEngineProvider, TefasRepository


class EtfDataRetriever:
    """Retrieves ETF data from the TEFAS SQLite database using ORM.

    This class avoids any direct downloader usage and relies entirely on
    the repository and SQLAlchemy models.
    """

    def __init__(self) -> None:
        self.logger = get_logger("etf_data_retriever")
        self.db_provider = DatabaseEngineProvider()
        self.SessionLocal = self.db_provider.get_session_factory()
        self.db_provider.ensure_initialized()

    def fetch_info(
        self,
        codes: Optional[Sequence[str]] = None,
        start: Optional[date] = None,
        end: Optional[date] = None,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        case_sensitive: bool = False,
        match_all_includes: bool = False,
    ) -> pd.DataFrame:
        """Fetch fund info rows as a pandas DataFrame with optional filters."""
        with self.SessionLocal() as session:
            repo = TefasRepository(session)
            norm_codes = None
            if codes is not None:
                norm_codes = [str(c).strip().upper() for c in codes if c is not None]
            rows = repo.query_fund_info(
                codes=list(norm_codes) if norm_codes else None,
                start=start,
                end=end,
                include_keywords=include_keywords,
                exclude_keywords=exclude_keywords,
                case_sensitive=case_sensitive,
                match_all_includes=match_all_includes,
            )

        records: List[Dict] = []
        for r in rows:
            records.append(
                {
                    "date": r.date,
                    "code": r.code,
                    "price": r.price,
                    "title": r.title,
                    "market_cap": r.market_cap,
                    "number_of_shares": r.number_of_shares,
                    "number_of_investors": r.number_of_investors,
                }
            )

        df = pd.DataFrame.from_records(records)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values(["code", "date"]).reset_index(drop=True)
        return df


