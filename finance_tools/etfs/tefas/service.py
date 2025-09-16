# finance_tools/etfs/tefas/service.py
"""
Service layer to persist TEFAS data using downloader and repository abstractions.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Tuple, List, Optional, Sequence, Callable

import pandas as pd

from .downloader import TefasDownloader
from .repository import DatabaseEngineProvider, TefasRepository


class TefasPersistenceService:
    """Coordinates download and persistence of TEFAS data."""

    def __init__(self, progress_callback: Optional[Callable[[str, int, int], None]] = None):
        self.downloader = TefasDownloader(progress_callback)
        self.db_provider = DatabaseEngineProvider()
        self.SessionLocal = self.db_provider.get_session_factory()
        self.db_provider.ensure_initialized()
        self.progress_callback = progress_callback

    def download_last_week(self, code: Optional[str] = None, kind: str = "BYF") -> pd.DataFrame:
        end = datetime.utcnow().date().strftime("%Y-%m-%d")
        start = (datetime.utcnow().date() - timedelta(days=7)).strftime("%Y-%m-%d")
        df = self.downloader.download_fund_prices(
            funds=code, startDate=str(start), endDate=str(end), columns=None, kind=kind
        )
        return df

    def download_between(
        self,
        start_date: str,
        end_date: str,
        funds: Optional[Sequence[str]] = None,
        kind: str = "BYF",
    ) -> pd.DataFrame:
        """Download TEFAS data between start_date and end_date (YYYY-MM-DD)."""
        if isinstance(funds, str):
            funds = [funds]
        return self.downloader.download_fund_prices(
            funds=funds, startDate=start_date, endDate=end_date, columns=None, kind=kind
        )

    def download_and_persist(
        self,
        start_date: str,
        end_date: str,
        funds: Optional[Sequence[str]] = None,
        kind: str = "BYF",
    ) -> Tuple[int, int]:
        df = self.download_between(start_date=start_date, end_date=end_date, funds=funds, kind=kind)
        
        # Report progress for persistence phase
        if self.progress_callback:
            self.progress_callback("Saving data to database...", 90, 0)
        
        return self.persist_dataframe(df)

    def persist_dataframe(self, df: pd.DataFrame) -> Tuple[int, int]:
        if df is None or df.empty:
            return 0, 0
        
        # Create a proper copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        # Split into info and breakdown dicts
        # Normalize columns
        if "code" not in df.columns and "symbol" in df.columns:
            df = df.rename(columns={"symbol": "code"})

        # Ensure `date` is Python date
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

        info_cols = [
            "date",
            "code",
            "price",
            "title",
            "market_cap",
            "number_of_shares",
            "number_of_investors",
        ]
        breakdown_cols = [c for c in df.columns if c not in info_cols]
        breakdown_cols = ["date", "code"] + [c for c in breakdown_cols if c not in {"date", "code"}]

        info_rows = df[info_cols].to_dict(orient="records")
        breakdown_rows = df[breakdown_cols].to_dict(orient="records")

        with self.SessionLocal() as session:
            repo = TefasRepository(session)
            inserted_info = repo.upsert_fund_info_many(info_rows)
            inserted_breakdown = repo.upsert_breakdown_many(breakdown_rows)
            return inserted_info, inserted_breakdown

    def query_info(self, code: str) -> List[dict]:
        with self.SessionLocal() as session:
            repo = TefasRepository(session)
            rows = repo.get_fund_info(code=code)
            return [
                {
                    "date": r.date,
                    "code": r.code,
                    "price": r.price,
                    "title": r.title,
                    "market_cap": r.market_cap,
                    "number_of_shares": r.number_of_shares,
                    "number_of_investors": r.number_of_investors,
                }
                for r in rows
            ]


