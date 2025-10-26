# finance_tools/stocks/analysis/retriever.py
from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, List, Optional, Sequence

import pandas as pd

from ...logging import get_logger
from ..repository import StockRepository
from ..models import StockPriceHistory, StockInfo
from ...etfs.tefas.repository import DatabaseEngineProvider


class StockDataRetriever:
    """Retrieves stock data from the SQLite database using ORM."""

    def __init__(self) -> None:
        self.logger = get_logger("stock_data_retriever")
        self.db_provider = DatabaseEngineProvider()
        self.db_provider.ensure_initialized()
        self.SessionLocal = self.db_provider.get_session_factory()

    def fetch_info(
        self,
        symbols: Optional[Sequence[str]] = None,
        start: Optional[date] = None,
        end: Optional[date] = None,
        interval: str = '1d',
        sector: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch stock price history as a pandas DataFrame with optional filters."""
        self.logger.info(f"📊 Fetching stock data - symbols: {symbols}, start: {start}, end: {end}")
        
        with self.SessionLocal() as session:
            repo = StockRepository(session)
            
            # If symbols not provided, get from database
            if symbols is None:
                symbols = repo.get_all_stock_symbols()
                self.logger.info(f"📊 Retrieved {len(symbols)} symbols from database")
                # Apply sector/industry filters if provided
                if sector or industry:
                    filtered_symbols = []
                    for symbol in symbols:
                        info = repo.get_stock_info(symbol)
                        if info:
                            if sector and info.sector != sector:
                                continue
                            if industry and info.industry != industry:
                                continue
                            filtered_symbols.append(symbol)
                    symbols = filtered_symbols
                    self.logger.info(f"📊 Filtered to {len(symbols)} symbols")
            
            norm_symbols = None
            if symbols is not None:
                norm_symbols = [str(s).strip().upper() for s in symbols if s is not None]
            
            self.logger.info(f"📊 Fetching price history for {len(norm_symbols) if norm_symbols else 0} symbols")
            
            # Get price history for all symbols
            rows = repo.get_price_history_for_symbols(
                symbols=list(norm_symbols) if norm_symbols else [],
                start_date=start,
                end_date=end,
                interval=interval
            )
            
            self.logger.info(f"📊 Retrieved {len(rows)} price history records")

        records: List[Dict] = []
        for r in rows:
            records.append(
                {
                    "date": r.date,
                    "symbol": r.symbol,
                    "open": r.open,
                    "high": r.high,
                    "low": r.low,
                    "close": r.close,
                    "volume": r.volume,
                    "dividends": r.dividends,
                    "stock_splits": r.stock_splits,
                }
            )

        df = pd.DataFrame.from_records(records)
        self.logger.info(f"📊 Created DataFrame with {len(df)} rows")
        
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
            self.logger.info(f"📊 DataFrame finalized - unique symbols: {df['symbol'].nunique()}")
        else:
            self.logger.warning(f"⚠️ No stock data found for symbols: {norm_symbols}")
        
        return df

