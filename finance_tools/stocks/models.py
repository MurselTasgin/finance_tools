# finance_tools/stocks/models.py
"""
Database models for stock data using SQLAlchemy ORM.
Shares the same Base class with TEFAS for unified database.

Note: Download tracking uses shared DownloadHistory and DownloadProgressLog tables
from ..etfs.tefas.models to unify all download tracking.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, Date, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

# Import shared Base from TEFAS models to ensure all tables are in same database
from ..etfs.tefas.models import Base


class StockPriceHistory(Base):
    """
    Stock price history table - stores OHLCV (Open, High, Low, Close, Volume) data.
    
    Supports multiple intervals (1d, 1h, 5m, etc.) for the same symbol.
    """
    
    __tablename__ = "stock_price_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    interval: Mapped[str] = mapped_column(String(10), nullable=False, default='1d', index=True)
    
    # OHLCV data
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Additional data
    dividends: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    stock_splits: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow, nullable=True)
    
    __table_args__ = (
        Index('idx_symbol_date_interval', 'symbol', 'date', 'interval', unique=True),
        {"sqlite_autoincrement": True},
    )


class StockInfo(Base):
    """
    Stock information table - stores company details and metadata.
    
    This is updated less frequently than price data.
    """
    
    __tablename__ = "stock_info"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    
    # Basic information
    name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    long_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Classification
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Market data
    market_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Additional metadata
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

# Note: Stock download tracking now uses shared tables from tefas.models:
# - DownloadHistory (with data_type='stock', kind=interval, symbols=[...])
# - DownloadProgressLog (with item_name=symbol)

