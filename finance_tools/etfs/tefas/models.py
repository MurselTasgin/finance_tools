# finance_tools/etfs/tefas/models.py
"""
Database models for TEFAS data using SQLAlchemy ORM.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import String, Integer, Float, Date, DateTime, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TefasFundInfo(Base):
    """TEFAS fund information table."""
    
    __tablename__ = "tefas_fund_info"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    market_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    number_of_shares: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    number_of_investors: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fund_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)  # BYF, YAT, EMK
    
    # Unique constraint on date and code
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class TefasFundBreakdown(Base):
    """TEFAS fund breakdown table."""
    
    __tablename__ = "tefas_fund_breakdown"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, index=True)
    
    # Individual breakdown fields
    bank_bills: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exchange_traded_fund: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    other: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fx_payable_bills: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    government_bond: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    foreign_currency_bills: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eurobonds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    commercial_paper: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fund_participation_certificate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    real_estate_certificate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    venture_capital_investment_fund_participation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    real_estate_investment_fund_participation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    treasury_bill: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stock: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    government_bonds_and_bills_fx: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    participation_account: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    participation_account_au: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    participation_account_d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    participation_account_tl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    government_lease_certificates: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    government_lease_certificates_d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    government_lease_certificates_tl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    government_lease_certificates_foreign: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precious_metals: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precious_metals_byf: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precious_metals_kba: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precious_metals_kks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    public_domestic_debt_instruments: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    private_sector_lease_certificates: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    private_sector_bond: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    repo: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    derivatives: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tmm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reverse_repo: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    asset_backed_securities: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    term_deposit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    term_deposit_au: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    term_deposit_d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    term_deposit_tl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    futures_cash_collateral: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    foreign_debt_instruments: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    foreign_domestic_debt_instruments: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    foreign_private_sector_debt_instruments: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    foreign_exchange_traded_funds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    foreign_equity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    foreign_securities: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    foreign_investment_fund_participation_shares: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    private_sector_international_lease_certificate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    private_sector_foreign_debt_instruments: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Unique constraint on date and code
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class DownloadHistory(Base):
    """
    Unified download history tracking table for both TEFAS and Stock downloads.
    
    Fields usage:
    - TEFAS: data_type='tefas', kind='BYF/YAT/EMK', funds=[fund_codes], symbols=None
    - Stock: data_type='stock', kind=interval, funds=None, symbols=[stock_symbols]
    """
    
    __tablename__ = "download_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)  # UUID
    
    # Data type: 'tefas' or 'stock'
    data_type: Mapped[str] = mapped_column(String(20), nullable=False, default='tefas', index=True)
    
    # Date range
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Type/Kind field: For TEFAS = BYF/YAT/EMK, For Stock = interval (1d/1h/etc)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # TEFAS-specific: fund codes
    funds: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    
    # Stock-specific: stock symbols
    symbols: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    
    # Status tracking
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='running')  # running, completed, failed, cancelled
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Download statistics
    records_downloaded: Mapped[int] = mapped_column(Integer, default=0)
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    
    # Stock-specific counts (can be used for funds too if needed)
    items_completed: Mapped[int] = mapped_column(Integer, default=0)  # symbols_completed or funds_completed
    items_failed: Mapped[int] = mapped_column(Integer, default=0)  # symbols_failed or funds_failed
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class DownloadProgressLog(Base):
    """
    Unified detailed progress log for both TEFAS and Stock download tasks.

    Fields usage:
    - TEFAS: item_name=fund_name, chunk_number=chunk number
    - Stock: item_name=symbol, chunk_number=symbol index
    """

    __tablename__ = "download_progress_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), index=True)  # UUID
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), nullable=False)  # info, success, warning, error
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Chunk or item number
    chunk_number: Mapped[int] = mapped_column(Integer, default=0)
    records_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Records in this message

    # Item name: fund code for TEFAS, stock symbol for stocks
    item_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class AnalysisResult(Base):
    """
    Store analysis results for caching and history.

    Supports both ETF and Stock analytics with flexible JSON storage
    for different result types and parameters.
    """

    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'etf_technical', 'etf_scan', 'stock_technical'
    analysis_name: Mapped[str] = mapped_column(String(100), nullable=False)  # Human-readable name

    # Parameters used for the analysis (JSON)
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Results data (JSON) - flexible storage for different result types
    results_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Metadata
    result_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Number of items in results
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='completed')  # completed, failed, running
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Caching and expiration
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # For cache expiry

    # User tracking (for future multi-user support)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Indexing for performance
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class UserAnalysisHistory(Base):
    """
    Track user analysis history for analytics dashboard.

    Records each analysis execution for history, favorites, and quick re-run.
    """

    __tablename__ = "user_analysis_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Analysis details
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    analysis_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Parameters used (JSON)
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Execution tracking
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Result reference (links to AnalysisResult if saved)
    result_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # User interaction tracking
    is_favorite: Mapped[bool] = mapped_column(Integer, default=0)  # SQLite boolean
    access_count: Mapped[int] = mapped_column(Integer, default=1)

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class AnalysisTask(Base):
    """
    Track analysis task execution for both ETF and Stock analytics.
    
    Supports background task management with real-time progress tracking,
    cancellation, and detailed logging for all analysis types.
    
    Fields usage:
    - ETF Technical: analysis_type='etf_technical', parameters={codes, start_date, end_date, ...}
    - ETF Scan: analysis_type='etf_scan', parameters={fund_type, codes, ...}
    - Stock Technical: analysis_type='stock_technical', parameters={symbols, start_date, ...}
    """
    
    __tablename__ = "analysis_tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)  # UUID
    
    # Analysis identification
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Possible values: 'etf_technical', 'etf_scan', 'stock_technical', etc.
    
    analysis_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Human-readable name: "ETF Technical Analysis", "ETF Scan Analysis", etc.
    
    # Execution parameters (JSON)
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status tracking
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='running')
    # Possible values: 'running', 'completed', 'failed', 'cancelled'
    
    # Progress tracking
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    progress_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Step tracking for detailed progress
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timing
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Results reference
    result_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Links to AnalysisResult table if results are saved
    
    # User tracking (for future multi-user support)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class AnalysisProgressLog(Base):
    """
    Detailed progress logs for analysis tasks.
    
    Tracks all progress updates, messages, and step completions during analysis execution.
    Supports both batch and real-time progress reporting.
    """
    
    __tablename__ = "analysis_progress_log"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)  # UUID
    
    # Log entry details
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # Possible values: 'info', 'progress', 'success', 'warning', 'error'
    
    # Progress snapshot at this point in time
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    
    # Optional: data being processed at this step
    # For ETF analysis: fund code, for Stock analysis: symbol
    item_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    item_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Optional: items/records counts
    items_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )