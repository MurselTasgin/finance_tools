# finance_tools/stocks/service.py
"""
Service layer to persist stock data using YFinance downloader and repository abstractions.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Tuple, List, Optional, Callable, Dict, Any
import pandas as pd
import yfinance as yf

from .data_downloaders.yfinance import YFinanceDownloader
from .repository import StockRepository
from ..etfs.tefas.repository import DatabaseEngineProvider
from ..logging import get_logger


class StockPersistenceService:
    """
    Coordinates download and persistence of stock data.
    
    Uses YFinanceDownloader to fetch data and StockRepository to persist it.
    Supports progress tracking via callbacks.
    """
    
    def __init__(self, progress_callback: Optional[Callable[[str, int, int], None]] = None):
        """
        Initialize service with optional progress callback.
        
        Args:
            progress_callback: Function(message, progress_percent, current_item)
                Called during download to report progress
        """
        self.downloader = YFinanceDownloader()
        self.db_provider = DatabaseEngineProvider()
        self.SessionLocal = self.db_provider.get_session_factory()
        self.db_provider.ensure_initialized()
        self.progress_callback = progress_callback
        self.logger = get_logger("stock_service")
    
    def download_and_persist(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        interval: str = '1d',
        include_info: bool = True
    ) -> Tuple[int, int]:
        """
        Download stock data and persist to database.
        
        Args:
            symbols: List of stock symbols (e.g., ['AAPL', 'MSFT'])
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval ('1d', '1h', '5m', etc.)
            include_info: Whether to fetch and store company info
        
        Returns:
            Tuple of (price_records_count, info_records_count)
        """
        total_symbols = len(symbols)
        price_records_total = 0
        info_records_total = 0
        
        # Progress: 0-80% for downloading, 80-90% for saving prices, 90-100% for info
        
        try:
            # Phase 1: Download price data for each symbol
            self.logger.info(f"Starting download for {total_symbols} symbols from {start_date} to {end_date}")
            
            for i, symbol in enumerate(symbols):
                # Calculate progress (0-80% for download phase)
                progress = int((i / total_symbols) * 80)
                
                if self.progress_callback:
                    self.progress_callback(
                        f"📊 Downloading {symbol} ({i+1}/{total_symbols})...",
                        progress,
                        i + 1
                    )
                
                try:
                    # Download data for this symbol
                    result = self.downloader.download(
                        symbols=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        interval=interval,
                        use_impersonation=True
                    )
                    
                    df = result.as_df()
                    
                    if not df.empty:
                        # Persist price data immediately
                        records = self._prepare_price_records(df, symbol, interval)
                        count = self._persist_price_records(records)
                        price_records_total += count
                        
                        msg = f"✅ Downloaded {symbol}: {count} records"
                        if self.progress_callback:
                            self.progress_callback(msg, progress, i + 1)
                        self.logger.info(msg)
                    else:
                        msg = f"⚠️  No data found for {symbol}"
                        if self.progress_callback:
                            self.progress_callback(msg, progress, i + 1)
                        self.logger.warning(msg)
                
                except Exception as e:
                    msg = f"❌ Error downloading {symbol}: {str(e)}"
                    if self.progress_callback:
                        self.progress_callback(msg, progress, i + 1)
                    self.logger.error(msg)
            
            # Phase 2: Database save completion (80-90%)
            if self.progress_callback:
                self.progress_callback(
                    f"💾 Price data saved: {price_records_total} records",
                    85,
                    total_symbols
                )
            
            # Phase 3: Fetch and persist stock info (90-100%)
            if include_info:
                if self.progress_callback:
                    self.progress_callback(
                        "📋 Fetching company information...",
                        90,
                        total_symbols
                    )
                
                info_records_total = self._fetch_and_persist_info(symbols)
                
                if self.progress_callback:
                    self.progress_callback(
                        f"✅ Company info saved: {info_records_total} records",
                        95,
                        total_symbols
                    )
            
            # Complete
            if self.progress_callback:
                self.progress_callback(
                    f"✅ Download completed! {price_records_total} price records, {info_records_total} info records",
                    100,
                    total_symbols
                )
            
            self.logger.info(
                f"Download completed: {price_records_total} price records, "
                f"{info_records_total} info records"
            )
            
            return price_records_total, info_records_total
        
        except Exception as e:
            self.logger.error(f"Error in download_and_persist: {e}")
            raise
    
    def _prepare_price_records(
        self,
        df: pd.DataFrame,
        symbol: str,
        interval: str
    ) -> List[Dict[str, Any]]:
        """
        Prepare price records from DataFrame for database insertion.
        
        Args:
            df: DataFrame with price data
            symbol: Stock symbol
            interval: Data interval
        
        Returns:
            List of record dictionaries
        """
        records = []
        
        # Ensure symbol column exists
        if 'Symbol' not in df.columns:
            df['Symbol'] = symbol
        
        # Convert DataFrame to records
        for idx, row in df.iterrows():
            # Get date from index or Date column
            if isinstance(idx, pd.Timestamp):
                record_date = idx.date()
            elif 'Date' in df.columns:
                record_date = pd.to_datetime(row['Date']).date()
            else:
                record_date = pd.to_datetime(idx).date()
            
            record = {
                'symbol': symbol.upper(),
                'date': record_date,
                'interval': interval,
                'open': float(row.get('Open', 0)) if pd.notna(row.get('Open')) else None,
                'high': float(row.get('High', 0)) if pd.notna(row.get('High')) else None,
                'low': float(row.get('Low', 0)) if pd.notna(row.get('Low')) else None,
                'close': float(row.get('Close', 0)) if pd.notna(row.get('Close')) else None,
                'volume': int(row.get('Volume', 0)) if pd.notna(row.get('Volume')) else None,
                'dividends': float(row.get('Dividends', 0)) if pd.notna(row.get('Dividends')) else 0.0,
                'stock_splits': float(row.get('Stock Splits', 0)) if pd.notna(row.get('Stock Splits')) else 0.0,
            }
            records.append(record)
        
        return records
    
    def _persist_price_records(self, records: List[Dict[str, Any]]) -> int:
        """
        Persist price records to database.
        
        Args:
            records: List of price record dictionaries
        
        Returns:
            Number of records inserted/updated
        """
        if not records:
            return 0
        
        with self.SessionLocal() as session:
            repo = StockRepository(session)
            return repo.upsert_price_history_many(records)
    
    def _fetch_and_persist_info(self, symbols: List[str]) -> int:
        """
        Fetch company information from yfinance and persist to database.
        
        Args:
            symbols: List of stock symbols
        
        Returns:
            Number of info records inserted/updated
        """
        count = 0
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if info and isinstance(info, dict):
                    # Extract relevant fields
                    stock_info = {
                        'symbol': symbol.upper(),
                        'name': info.get('shortName'),
                        'long_name': info.get('longName'),
                        'sector': info.get('sector'),
                        'industry': info.get('industry'),
                        'country': info.get('country'),
                        'market_cap': info.get('marketCap'),
                        'currency': info.get('currency'),
                        'exchange': info.get('exchange'),
                        'website': info.get('website'),
                        'description': info.get('longBusinessSummary'),
                    }
                    
                    # Persist to database
                    with self.SessionLocal() as session:
                        repo = StockRepository(session)
                        repo.upsert_stock_info(stock_info)
                    
                    count += 1
                    self.logger.info(f"Saved info for {symbol}")
            
            except Exception as e:
                self.logger.warning(f"Could not fetch info for {symbol}: {e}")
        
        return count
    
    def get_price_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        Get price data from database as DataFrame.
        
        Args:
            symbol: Stock symbol
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            interval: Data interval
        
        Returns:
            DataFrame with price data
        """
        with self.SessionLocal() as session:
            repo = StockRepository(session)
            
            # Convert date strings to date objects
            start = pd.to_datetime(start_date).date() if start_date else None
            end = pd.to_datetime(end_date).date() if end_date else None
            
            records = repo.get_price_history(symbol, start, end, interval)
            
            if not records:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for record in records:
                data.append({
                    'Date': record.date,
                    'Open': record.open,
                    'High': record.high,
                    'Low': record.low,
                    'Close': record.close,
                    'Volume': record.volume,
                    'Dividends': record.dividends,
                    'Stock Splits': record.stock_splits,
                    'Symbol': record.symbol,
                })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df = df.set_index('Date')
                df = df.sort_index()
            
            return df
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get stock information from database.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dictionary with stock info or None
        """
        with self.SessionLocal() as session:
            repo = StockRepository(session)
            info = repo.get_stock_info(symbol)
            
            if not info:
                return None
            
            return {
                'symbol': info.symbol,
                'name': info.name,
                'long_name': info.long_name,
                'sector': info.sector,
                'industry': info.industry,
                'country': info.country,
                'market_cap': info.market_cap,
                'currency': info.currency,
                'exchange': info.exchange,
                'website': info.website,
                'description': info.description,
                'last_updated': info.last_updated.isoformat() if info.last_updated else None,
            }

