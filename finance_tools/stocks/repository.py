# finance_tools/stocks/repository.py
"""
Repository layer for stock data persistence using SQLAlchemy ORM.
Handles all database operations for stocks.

Note: Uses shared DownloadHistory and DownloadProgressLog from tefas.models
for unified download tracking across all data types.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .models import StockPriceHistory, StockInfo, StockGroup, Base
from ..etfs.tefas.models import DownloadHistory, DownloadProgressLog
from ..logging import get_logger


class StockRepository:
    """
    Repository for stock data operations.
    
    Provides CRUD operations and queries for stock price history,
    stock information, and download tracking.
    """
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session
        self.logger = get_logger("stock_repo")
    
    # ==================== Price History Operations ====================
    
    def upsert_price_history_many(self, records: List[Dict[str, Any]]) -> int:
        """
        Insert or update multiple price history records.
        
        Uses UPSERT logic - if record exists (symbol, date, interval), updates it.
        Otherwise inserts new record.
        
        Args:
            records: List of dictionaries with price data
                Required keys: symbol, date, interval
                Optional keys: open, high, low, close, volume, dividends, stock_splits
        
        Returns:
            Number of records inserted/updated
        """
        if not records:
            return 0
        
        try:
            # Prepare records with proper types
            prepared_records = []
            for rec in records:
                prepared = {
                    'symbol': str(rec.get('symbol', '')).upper(),
                    'date': rec['date'],
                    'interval': rec.get('interval', '1d'),
                    'open': rec.get('open'),
                    'high': rec.get('high'),
                    'low': rec.get('low'),
                    'close': rec.get('close'),
                    'volume': rec.get('volume'),
                    'dividends': rec.get('dividends', 0.0),
                    'stock_splits': rec.get('stock_splits', 0.0),
                    'created_at': datetime.utcnow(),
                }
                prepared_records.append(prepared)
            
            # Use SQLite UPSERT (INSERT OR REPLACE)
            stmt = sqlite_insert(StockPriceHistory).values(prepared_records)
            stmt = stmt.on_conflict_do_update(
                index_elements=['symbol', 'date', 'interval'],
                set_={
                    'open': stmt.excluded.open,
                    'high': stmt.excluded.high,
                    'low': stmt.excluded.low,
                    'close': stmt.excluded.close,
                    'volume': stmt.excluded.volume,
                    'dividends': stmt.excluded.dividends,
                    'stock_splits': stmt.excluded.stock_splits,
                    'updated_at': datetime.utcnow(),
                }
            )
            
            self.session.execute(stmt)
            self.session.commit()
            
            self.logger.info(f"Upserted {len(prepared_records)} price history records")
            return len(prepared_records)
            
        except Exception as e:
            self.logger.error(f"Error upserting price history: {e}")
            self.session.rollback()
            raise
    
    def get_price_history(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        interval: str = '1d',
        limit: Optional[int] = None
    ) -> List[StockPriceHistory]:
        """
        Get price history for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            interval: Data interval (default: '1d')
            limit: Maximum number of records (optional)
        
        Returns:
            List of StockPriceHistory records, ordered by date descending
        """
        query = select(StockPriceHistory).where(
            and_(
                StockPriceHistory.symbol == symbol.upper(),
                StockPriceHistory.interval == interval
            )
        )
        
        if start_date:
            query = query.where(StockPriceHistory.date >= start_date)
        
        if end_date:
            query = query.where(StockPriceHistory.date <= end_date)
        
        query = query.order_by(desc(StockPriceHistory.date))
        
        if limit:
            query = query.limit(limit)
        
        result = self.session.execute(query)
        return list(result.scalars().all())
    
    def get_price_history_for_symbols(
        self,
        symbols: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        interval: str = '1d'
    ) -> List[StockPriceHistory]:
        """
        Get price history for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            interval: Data interval (default: '1d')
        
        Returns:
            List of StockPriceHistory records for all symbols
        """
        symbols_upper = [s.upper() for s in symbols]
        
        query = select(StockPriceHistory).where(
            and_(
                StockPriceHistory.symbol.in_(symbols_upper),
                StockPriceHistory.interval == interval
            )
        )
        
        if start_date:
            query = query.where(StockPriceHistory.date >= start_date)
        
        if end_date:
            query = query.where(StockPriceHistory.date <= end_date)
        
        query = query.order_by(StockPriceHistory.symbol, desc(StockPriceHistory.date))
        
        result = self.session.execute(query)
        return list(result.scalars().all())
    
    def get_latest_price_date(self, symbol: str, interval: str = '1d') -> Optional[date]:
        """
        Get the latest date for which we have price data.
        
        Args:
            symbol: Stock symbol
            interval: Data interval
        
        Returns:
            Latest date or None if no data
        """
        query = select(func.max(StockPriceHistory.date)).where(
            and_(
                StockPriceHistory.symbol == symbol.upper(),
                StockPriceHistory.interval == interval
            )
        )
        
        result = self.session.execute(query)
        return result.scalar_one_or_none()
    
    # ==================== Stock Info Operations ====================
    
    def upsert_stock_info(self, info: Dict[str, Any]) -> None:
        """
        Insert or update stock information.
        
        Args:
            info: Dictionary with stock information
                Required: symbol
                Optional: name, long_name, sector, industry, country, market_cap,
                         currency, exchange, website, description
        """
        try:
            symbol = info['symbol'].upper()
            
            # Check if record exists
            existing = self.session.execute(
                select(StockInfo).where(StockInfo.symbol == symbol)
            ).scalar_one_or_none()
            
            if existing:
                # Update existing record
                for key, value in info.items():
                    if key != 'symbol' and hasattr(existing, key):
                        setattr(existing, key, value)
                existing.last_updated = datetime.utcnow()
            else:
                # Insert new record
                new_info = StockInfo(
                    symbol=symbol,
                    name=info.get('name'),
                    long_name=info.get('long_name'),
                    sector=info.get('sector'),
                    industry=info.get('industry'),
                    country=info.get('country'),
                    market_cap=info.get('market_cap'),
                    currency=info.get('currency'),
                    exchange=info.get('exchange'),
                    website=info.get('website'),
                    description=info.get('description'),
                    last_updated=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                self.session.add(new_info)
            
            self.session.commit()
            self.logger.info(f"Upserted stock info for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error upserting stock info: {e}")
            self.session.rollback()
            raise
    
    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """
        Get stock information.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            StockInfo record or None if not found
        """
        result = self.session.execute(
            select(StockInfo).where(StockInfo.symbol == symbol.upper())
        )
        return result.scalar_one_or_none()
    
    def get_all_stock_symbols(self) -> List[str]:
        """
        Get list of all stock symbols in database.
        
        Returns:
            List of stock symbols
        """
        result = self.session.execute(
            select(StockInfo.symbol).order_by(StockInfo.symbol)
        )
        return [row[0] for row in result.all()]
    
    # ==================== Download History Operations ====================
    
    def create_download_record(
        self,
        task_id: str,
        symbols: List[str],
        start_date: date,
        end_date: date,
        interval: str = '1d'
    ) -> DownloadHistory:
        """
        Create a new download history record for stocks.
        Uses shared DownloadHistory table with data_type='stock'.
        
        Args:
            task_id: Unique task identifier (UUID)
            symbols: List of stock symbols
            start_date: Download start date
            end_date: Download end date
            interval: Data interval (e.g., '1d', '1h')
        
        Returns:
            Created DownloadHistory record
        """
        try:
            download = DownloadHistory(
                task_id=task_id,
                data_type='stock',  # Identifies this as a stock download
                kind=interval,  # For stocks, 'kind' stores the interval
                symbols=symbols,  # Stock symbols
                funds=None,  # Not used for stocks
                start_date=start_date,
                end_date=end_date,
                status='running',
                start_time=datetime.utcnow(),
                records_downloaded=0,
                total_records=0,
                items_completed=0,  # Will track symbols_completed
                items_failed=0,  # Will track symbols_failed
                created_at=datetime.utcnow()
            )
            
            self.session.add(download)
            self.session.commit()
            
            self.logger.info(f"Created stock download record for task {task_id}")
            return download
            
        except Exception as e:
            self.logger.error(f"Error creating download record: {e}")
            self.session.rollback()
            raise
    
    def update_download_record(
        self,
        task_id: str,
        status: str,
        records_downloaded: int = 0,
        total_records: int = 0,
        symbols_completed: int = 0,
        symbols_failed: int = 0,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update download history record.
        Uses shared DownloadHistory table.
        
        Args:
            task_id: Task identifier
            status: New status (running, completed, failed, cancelled)
            records_downloaded: Number of records downloaded
            total_records: Total expected records
            symbols_completed: Number of symbols completed
            symbols_failed: Number of symbols failed
            error_message: Error message if applicable
        """
        try:
            download = self.session.execute(
                select(DownloadHistory).where(
                    and_(
                        DownloadHistory.task_id == task_id,
                        DownloadHistory.data_type == 'stock'
                    )
                )
            ).scalar_one_or_none()
            
            if not download:
                self.logger.warning(f"Stock download record not found for task {task_id}")
                return
            
            download.status = status
            download.records_downloaded = records_downloaded
            download.total_records = total_records
            download.items_completed = symbols_completed  # Map to items_completed
            download.items_failed = symbols_failed  # Map to items_failed
            
            if error_message:
                download.error_message = error_message
            
            if status in ['completed', 'failed', 'cancelled']:
                download.end_time = datetime.utcnow()
            
            self.session.commit()
            self.logger.info(f"Updated stock download record for task {task_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating download record: {e}")
            self.session.rollback()
            raise
    
    def get_download_history(
        self,
        page: int = 1,
        page_size: int = 50,
        search: str = "",
        status_filter: Optional[str] = None
    ) -> Tuple[List[DownloadHistory], int]:
        """
        Get stock download history with pagination and filtering.
        Uses shared DownloadHistory table filtered by data_type='stock'.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of records per page
            search: Search term for symbols
            status_filter: Filter by status (optional)
        
        Returns:
            Tuple of (list of DownloadHistory records, total count)
        """
        query = select(DownloadHistory).where(DownloadHistory.data_type == 'stock')
        
        # Apply filters
        if search:
            # Search in symbols JSON field
            query = query.where(
                DownloadHistory.symbols.contains(search.upper())
            )
        
        if status_filter:
            query = query.where(DownloadHistory.status == status_filter)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = self.session.execute(count_query).scalar_one()
        
        # Apply pagination and ordering
        query = query.order_by(desc(DownloadHistory.start_time))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = self.session.execute(query)
        records = list(result.scalars().all())
        
        return records, total
    
    def cleanup_orphaned_running_tasks(self) -> int:
        """
        Mark all 'running' stock tasks as 'failed' on startup.
        Called when server restarts to clean up interrupted stock tasks.
        
        Returns:
            Number of tasks cleaned up
        """
        try:
            running_tasks = self.session.execute(
                select(DownloadHistory).where(
                    and_(
                        DownloadHistory.data_type == 'stock',
                        DownloadHistory.status == 'running'
                    )
                )
            ).scalars().all()
            
            if not running_tasks:
                return 0
            
            for task in running_tasks:
                task.status = 'failed'
                task.end_time = datetime.utcnow()
                task.error_message = 'Task interrupted by server restart or crash'
            
            self.session.commit()
            self.logger.info(f"Cleaned up {len(running_tasks)} orphaned stock 'running' tasks")
            
            return len(running_tasks)
            
        except Exception as e:
            self.logger.error(f"Error cleaning up orphaned tasks: {e}")
            self.session.rollback()
            return 0
    
    # ==================== Progress Log Operations ====================
    
    def create_progress_log_entry(
        self,
        task_id: str,
        timestamp: datetime,
        message: str,
        message_type: str,
        progress_percent: int,
        symbol_number: int,
        records_count: Optional[int] = None,
        symbol: Optional[str] = None
    ) -> None:
        """
        Create a progress log entry.
        Uses shared DownloadProgressLog table.
        
        Args:
            task_id: Task identifier
            timestamp: Log timestamp
            message: Log message
            message_type: Type (info, success, warning, error)
            progress_percent: Progress percentage (0-100)
            symbol_number: Current symbol number being processed
            records_count: Number of records in this operation
            symbol: Symbol being processed (optional)
        """
        try:
            log_entry = DownloadProgressLog(
                task_id=task_id,
                timestamp=timestamp,
                message=message,
                message_type=message_type,
                progress_percent=progress_percent,
                chunk_number=symbol_number,  # Map symbol_number to chunk_number
                records_count=records_count,
                item_name=symbol.upper() if symbol else None,  # Map symbol to item_name
                created_at=datetime.utcnow()
            )
            
            self.session.add(log_entry)
            self.session.commit()
            
        except Exception as e:
            self.logger.error(f"Error creating progress log entry: {e}")
            self.session.rollback()
    
    def get_progress_logs(self, task_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get progress logs for a task.
        Uses shared DownloadProgressLog table.
        
        Args:
            task_id: Task identifier
            limit: Maximum number of logs to return
        
        Returns:
            List of progress log dictionaries
        """
        query = select(DownloadProgressLog).where(
            DownloadProgressLog.task_id == task_id
        ).order_by(DownloadProgressLog.timestamp).limit(limit)
        
        result = self.session.execute(query)
        logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "task_id": log.task_id,
                "timestamp": log.timestamp.isoformat(),
                "message": log.message,
                "message_type": log.message_type,
                "progress_percent": log.progress_percent,
                "symbol_number": log.chunk_number,  # Map back to symbol_number
                "records_count": log.records_count,
                "symbol": log.item_name,  # Map back to symbol
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    
    # ==================== Statistics Operations ====================
    
    def get_total_records_count(self) -> int:
        """Get total number of price history records."""
        result = self.session.execute(select(func.count(StockPriceHistory.id)))
        return result.scalar_one()
    
    def get_unique_symbols_count(self) -> int:
        """Get count of unique stock symbols."""
        result = self.session.execute(
            select(func.count(func.distinct(StockPriceHistory.symbol)))
        )
        return result.scalar_one()
    
    def get_date_range(self) -> Dict[str, Optional[date]]:
        """
        Get the date range of stored price data.
        
        Returns:
            Dictionary with 'start' and 'end' dates
        """
        min_date = self.session.execute(
            select(func.min(StockPriceHistory.date))
        ).scalar_one_or_none()
        
        max_date = self.session.execute(
            select(func.max(StockPriceHistory.date))
        ).scalar_one_or_none()
        
        return {"start": min_date, "end": max_date}
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stock downloads.
        Uses shared DownloadHistory table filtered by data_type='stock'.
        
        Returns:
            Dictionary with download statistics
        """
        total = self.session.execute(
            select(func.count(DownloadHistory.id)).where(DownloadHistory.data_type == 'stock')
        ).scalar_one()
        
        completed = self.session.execute(
            select(func.count(DownloadHistory.id)).where(
                and_(
                    DownloadHistory.data_type == 'stock',
                    DownloadHistory.status == 'completed'
                )
            )
        ).scalar_one()
        
        failed = self.session.execute(
            select(func.count(DownloadHistory.id)).where(
                and_(
                    DownloadHistory.data_type == 'stock',
                    DownloadHistory.status == 'failed'
                )
            )
        ).scalar_one()
        
        total_records = self.session.execute(
            select(func.sum(DownloadHistory.records_downloaded)).where(DownloadHistory.data_type == 'stock')
        ).scalar_one() or 0
        
        return {
            "total_downloads": total,
            "successful_downloads": completed,
            "failed_downloads": failed,
            "total_records_downloaded": total_records
        }
    
    def get_stock_download_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a download task including progress logs.
        Uses shared DownloadHistory and DownloadProgressLog tables.
        
        Args:
            task_id: Task identifier
        
        Returns:
            Dictionary with task info, progress logs, and statistics
        """
        # Get the main download record
        download = self.session.execute(
            select(DownloadHistory).where(
                and_(
                    DownloadHistory.task_id == task_id,
                    DownloadHistory.data_type == 'stock'
                )
            )
        ).scalar_one_or_none()
        
        if not download:
            return None
        
        # Get progress logs
        progress_logs = self.get_progress_logs(task_id)
        
        # Calculate statistics
        total_messages = len(progress_logs)
        success_messages = len([log for log in progress_logs if log['message_type'] == 'success'])
        error_messages = len([log for log in progress_logs if log['message_type'] == 'error'])
        warning_messages = len([log for log in progress_logs if log['message_type'] == 'warning'])
        
        total_records_from_logs = sum([
            log['records_count'] for log in progress_logs 
            if log['records_count'] is not None
        ])
        
        return {
            "task_info": {
                "id": download.id,
                "task_id": download.task_id,
                "symbols": download.symbols,
                "start_date": download.start_date.isoformat(),
                "end_date": download.end_date.isoformat(),
                "interval": download.kind,  # For stocks, kind stores the interval
                "status": download.status,
                "start_time": download.start_time.isoformat(),
                "end_time": download.end_time.isoformat() if download.end_time else None,
                "records_downloaded": download.records_downloaded,
                "total_records": download.total_records,
                "symbols_completed": download.items_completed,  # Map from items_completed
                "symbols_failed": download.items_failed,  # Map from items_failed
                "error_message": download.error_message,
                "created_at": download.created_at.isoformat()
            },
            "progress_logs": progress_logs,
            "statistics": {
                "total_messages": total_messages,
                "success_messages": success_messages,
                "error_messages": error_messages,
                "warning_messages": warning_messages,
                "total_records_from_logs": total_records_from_logs,
                "duration_seconds": (
                    (download.end_time or datetime.utcnow()) - download.start_time
                ).total_seconds() if download.start_time else 0
            }
        }
    
    # ==================== Stock Group Operations ====================
    
    def create_stock_group(
        self,
        name: str,
        description: Optional[str],
        symbols: List[str],
        user_id: Optional[str] = None
    ) -> StockGroup:
        """Create a new stock group."""
        try:
            group = StockGroup(
                name=name,
                description=description,
                symbols=json.dumps(symbols),
                user_id=user_id,
                created_at=datetime.utcnow()
            )
            self.session.add(group)
            self.session.commit()
            self.logger.info(f"Created stock group: {name} with {len(symbols)} symbols")
            return group
        except Exception as e:
            self.logger.error(f"Error creating stock group: {e}")
            self.session.rollback()
            raise
    
    def get_stock_groups(self, user_id: Optional[str] = None) -> List[StockGroup]:
        """Get all stock groups, optionally filtered by user."""
        query = select(StockGroup)
        if user_id:
            query = query.where(StockGroup.user_id == user_id)
        query = query.order_by(StockGroup.created_at.desc())
        result = self.session.execute(query)
        return list(result.scalars().all())
    
    def get_stock_group(self, group_id: int) -> Optional[StockGroup]:
        """Get a specific stock group by ID."""
        result = self.session.execute(
            select(StockGroup).where(StockGroup.id == group_id)
        )
        return result.scalar_one_or_none()
    
    def update_stock_group(
        self,
        group_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        symbols: Optional[List[str]] = None
    ) -> Optional[StockGroup]:
        """Update an existing stock group."""
        try:
            group = self.get_stock_group(group_id)
            if not group:
                return None
            
            if name:
                group.name = name
            if description is not None:
                group.description = description
            if symbols:
                group.symbols = json.dumps(symbols)
            group.updated_at = datetime.utcnow()
            
            self.session.commit()
            self.logger.info(f"Updated stock group: {group_id}")
            return group
        except Exception as e:
            self.logger.error(f"Error updating stock group: {e}")
            self.session.rollback()
            raise
    
    def delete_stock_group(self, group_id: int) -> bool:
        """Delete a stock group."""
        try:
            group = self.get_stock_group(group_id)
            if not group:
                return False
            
            self.session.delete(group)
            self.session.commit()
            self.logger.info(f"Deleted stock group: {group_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting stock group: {e}")
            self.session.rollback()
            return False
