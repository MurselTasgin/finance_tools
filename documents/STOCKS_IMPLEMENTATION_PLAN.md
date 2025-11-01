# Stock Data Implementation Plan - Analysis & Requirements

## Current State Analysis

### ✅ What Exists

#### 1. **YFinance Downloader** (`finance_tools/stocks/data_downloaders/yfinance.py`)
- **Status**: ✅ Fully implemented
- **Features**:
  - Download single or multiple stocks
  - Date range or period-based downloads
  - Multiple intervals (1d, 1h, 5m, etc.)
  - Impersonation to avoid rate limits
  - Dividends and splits support
  - Returns formatted DataFrames

**Example usage:**
```python
downloader = YFinanceDownloader()
result = downloader.download(
    symbols=["AAPL", "MSFT"],
    start_date="2024-01-01",
    end_date="2024-12-31",
    interval="1d"
)
df = result.as_df()
```

#### 2. **TEFAS Infrastructure** (Reference Implementation)
- **Models**: `TefasFundInfo`, `TefasFundBreakdown`, `DownloadHistory`, `DownloadProgressLog`
- **Repository**: `TefasRepository` - handles all DB operations
- **Service**: `TefasPersistenceService` - orchestrates download + persistence
- **Downloader**: `TefasDownloader` - fetches data with progress callbacks
- **Backend API**: Full REST API with progress tracking

---

## ❌ What's Missing

### 1. **Database Models for Stocks**

Need to create SQLAlchemy models similar to TEFAS:

```python
# finance_tools/stocks/models.py (NEW FILE)

class StockPriceHistory(Base):
    """Stock price history table - OHLCV data"""
    __tablename__ = "stock_price_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)  # AAPL, MSFT, etc.
    date: Mapped[date] = mapped_column(Date, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(Integer)
    dividends: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stock_splits: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    interval: Mapped[str] = mapped_column(String(10), default='1d')  # 1d, 1h, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class StockInfo(Base):
    """Stock information table - company details"""
    __tablename__ = "stock_info"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(500))
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(50))
    market_cap: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class StockDownloadHistory(Base):
    """Download history for stock data"""
    __tablename__ = "stock_download_history"
    
    # Similar to DownloadHistory but for stocks
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    symbols: Mapped[str] = mapped_column(JSON)  # List of stock symbols
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    interval: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default='running')
    # ... similar to DownloadHistory
```

**Key differences from TEFAS**:
- Stocks use `symbol` (AAPL) vs TEFAS `code` (fund codes)
- Stocks have OHLCV (Open, High, Low, Close, Volume) data
- Stocks have `interval` (1d, 1h, 5m) vs TEFAS daily only
- No "breakdown" equivalent (stocks don't have portfolio breakdowns)

---

### 2. **Repository Layer for Stocks**

```python
# finance_tools/stocks/repository.py (NEW FILE)

class StockRepository:
    """Repository for stock data operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def upsert_price_history(self, records: List[Dict]) -> int:
        """Insert or update stock price records"""
        # Similar to TefasRepository.upsert_fund_info_many()
        pass
    
    def get_price_history(self, symbol: str, start_date: date, end_date: date, interval: str = '1d') -> List[StockPriceHistory]:
        """Fetch price history for a symbol"""
        pass
    
    def upsert_stock_info(self, info: Dict) -> None:
        """Insert or update stock information"""
        pass
    
    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """Get stock information"""
        pass
    
    def create_download_record(self, task_id: str, symbols: List[str], ...) -> StockDownloadHistory:
        """Create download history record"""
        pass
    
    def update_download_record(self, task_id: str, status: str, ...) -> None:
        """Update download history record"""
        pass
    
    # Similar methods to TefasRepository for:
    # - get_download_history()
    # - get_download_statistics()
    # - create_progress_log_entry()
    # - get_progress_logs()
    # - cleanup_orphaned_running_tasks()
```

---

### 3. **Service Layer for Stocks**

```python
# finance_tools/stocks/service.py (NEW FILE)

class StockPersistenceService:
    """Service for stock data download and persistence"""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.downloader = YFinanceDownloader()
        self.db_provider = DatabaseEngineProvider()  # Shared with TEFAS
        self.SessionLocal = self.db_provider.get_session_factory()
        self.progress_callback = progress_callback
    
    def download_and_persist(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        interval: str = '1d',
        include_info: bool = True
    ) -> Tuple[int, int]:
        """
        Download stock data and persist to database
        
        Returns:
            (price_records_count, info_records_count)
        """
        # Phase 1: Download price data
        if self.progress_callback:
            self.progress_callback("Downloading stock data...", 10, 0)
        
        result = self.downloader.download(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        df = result.as_df()
        
        # Phase 2: Persist price data
        if self.progress_callback:
            self.progress_callback("Saving price data to database...", 70, 0)
        
        price_count = self.persist_price_data(df)
        
        # Phase 3: Fetch and persist stock info (optional)
        info_count = 0
        if include_info:
            if self.progress_callback:
                self.progress_callback("Fetching stock information...", 90, 0)
            
            info_count = self.persist_stock_info(symbols)
        
        if self.progress_callback:
            self.progress_callback("✅ Download completed", 100, 0)
        
        return price_count, info_count
    
    def persist_price_data(self, df: pd.DataFrame) -> int:
        """Persist price data to database"""
        pass
    
    def persist_stock_info(self, symbols: List[str]) -> int:
        """Fetch and persist stock information"""
        pass
```

---

### 4. **Backend API Endpoints**

Add to `backend/main.py`:

```python
# Stock download endpoints (parallel to TEFAS)

@app.post("/api/stocks/download")
async def download_stock_data(request: dict):
    """
    Initiate stock data download
    
    Body:
    {
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "startDate": "2024-01-01",
        "endDate": "2024-12-31",
        "interval": "1d",
        "includeInfo": true
    }
    """
    pass

@app.get("/api/stocks/download-progress")
async def get_stock_download_progress():
    """Get current stock download progress"""
    pass

@app.get("/api/stocks/history")
async def get_stock_download_history():
    """Get stock download history with pagination"""
    pass

@app.get("/api/stocks/data")
async def get_stock_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = '1d'
):
    """Fetch stock price data from database"""
    pass

@app.get("/api/stocks/info/{symbol}")
async def get_stock_info(symbol: str):
    """Get stock information"""
    pass

@app.get("/api/stocks/stats")
async def get_stock_stats():
    """Get statistics about stored stock data"""
    pass
```

---

### 5. **Frontend Components**

Add to `frontend/src/components/`:

```typescript
// StockDownloadJobs.tsx
// Similar to DownloadJobs.tsx but for stocks
// Shows stock download history and live progress

// StockDataExplorer.tsx
// Browse and filter stored stock data
// Show price charts, OHLCV data

// StockInfoViewer.tsx
// Display company information
```

---

## Implementation Comparison: TEFAS vs Stocks

| Aspect | TEFAS | Stocks |
|--------|-------|--------|
| **Data Source** | TEFAS website (web scraping) | yfinance API |
| **Identifier** | Fund code (e.g., "AGG") | Stock symbol (e.g., "AAPL") |
| **Data Types** | Fund info + Breakdown | OHLCV + Company info |
| **Intervals** | Daily only | Multiple (1d, 1h, 5m, etc.) |
| **Primary Table** | `tefas_fund_info` | `stock_price_history` |
| **Secondary Table** | `tefas_fund_breakdown` | `stock_info` |
| **Download Unit** | Chunks by date range | Chunks by symbol groups |
| **Progress Tracking** | By chunks (date ranges) | By symbols processed |

---

## Database Schema Changes Needed

### Option 1: Separate Databases (Recommended)
- Keep `tefas_*` tables in current database
- Create separate `stock_*` tables in same database
- Share `download_history` or create separate `stock_download_history`

**Pros**: Clean separation, easy to manage
**Cons**: More tables

### Option 2: Unified Schema
- Rename tables to be generic (`asset_price_history`)
- Add `asset_type` column ('TEFAS' or 'STOCK')

**Pros**: Fewer tables
**Cons**: Complex queries, harder to optimize

**Recommendation**: Use Option 1 (Separate tables)

---

## Progress Tracking for Stocks

Stock downloads differ from TEFAS:

**TEFAS**: Date-based chunks (30-day periods)
```
Progress = (current_chunk / total_chunks) * 90%
```

**Stocks**: Symbol-based processing
```python
total_symbols = len(symbols)
for i, symbol in enumerate(symbols):
    progress = int((i / total_symbols) * 90)
    callback(f"Downloading {symbol}...", progress, i)
```

**Example**:
```
Downloading AAPL... (10%)
Downloading MSFT... (20%)
Downloading GOOGL... (30%)
...
Saving to database... (95%)
Complete! (100%)
```

---

## Configuration Changes

Add to `finance_tools/config.py`:

```python
# Stock data settings
STOCK_DEFAULT_INTERVAL = "1d"
STOCK_MAX_SYMBOLS_PER_REQUEST = 50
STOCK_RATE_LIMIT_DELAY = 0.5  # seconds between requests
STOCK_DATABASE_NAME = "finance_tools.db"  # same as TEFAS
```

---

## Files to Create

### Core Implementation
1. ✅ `finance_tools/stocks/models.py` - Database models
2. ✅ `finance_tools/stocks/repository.py` - Data access layer
3. ✅ `finance_tools/stocks/service.py` - Business logic layer
4. ✅ `finance_tools/stocks/schema.py` - Data validation schemas (optional)

### Backend
5. ✅ Update `backend/main.py` - Add stock endpoints

### Frontend
6. ✅ `frontend/src/components/StockDownloadJobs.tsx` - Job management
7. ✅ `frontend/src/components/StockDataExplorer.tsx` - Data browser
8. ✅ `frontend/src/services/stockApi.ts` - API client

### Configuration
9. ✅ Update `finance_tools/config.py` - Add stock settings
10. ✅ Update database initialization - Create stock tables

---

## Implementation Steps (Priority Order)

### Phase 1: Database & Core (High Priority)
1. Create `models.py` with stock tables
2. Create `repository.py` with CRUD operations
3. Create `service.py` with download orchestration
4. Update database initialization to create tables
5. Write unit tests

### Phase 2: Backend API (High Priority)
6. Add stock download endpoint
7. Add progress tracking endpoint
8. Add data retrieval endpoints
9. Add download history endpoint
10. Test with Postman/curl

### Phase 3: Frontend UI (Medium Priority)
11. Create StockDownloadJobs component
12. Add to DataManagement tabs
13. Create StockDataExplorer
14. Add stock-specific API calls
15. Test end-to-end flow

### Phase 4: Features & Polish (Low Priority)
16. Add stock info fetching (company details)
17. Add multiple interval support
18. Add bulk symbol import
19. Add data visualization charts
20. Add export functionality

---

## Key Design Decisions

### 1. **Reuse vs Separate**
- **Reuse**: DatabaseEngineProvider, progress tracking pattern, UI patterns
- **Separate**: Models, repositories, services (different data structures)

### 2. **Progress Tracking**
- Use same pattern as TEFAS (0-90% download, 90-100% save)
- Track by symbols instead of date chunks
- Reuse `download_progress` global state pattern

### 3. **API Design**
- Use `/api/stocks/*` prefix (parallel to `/api/database/*` for TEFAS)
- Keep consistent response structures
- Share download history tracking pattern

### 4. **Frontend Integration**
- Add "Stock Jobs" tab next to "Download Jobs" (TEFAS)
- OR create unified "Data Management" with sub-tabs
- Reuse modal, progress bar components

---

## Estimated Effort

| Phase | Files | Lines of Code | Time Estimate |
|-------|-------|---------------|---------------|
| Phase 1: Database & Core | 3-4 files | ~800 lines | 4-6 hours |
| Phase 2: Backend API | 1 file | ~400 lines | 2-3 hours |
| Phase 3: Frontend UI | 3-4 files | ~1000 lines | 6-8 hours |
| Phase 4: Features | Various | ~500 lines | 4-6 hours |
| **Total** | **10-13 files** | **~2700 lines** | **16-23 hours** |

---

## Next Steps

1. **Review this plan** with user
2. **Start with Phase 1**: Create database models
3. **Implement progressively**: Test each phase before moving to next
4. **Reuse patterns**: Leverage existing TEFAS implementation
5. **Maintain consistency**: Keep UI/UX similar to TEFAS features

---

## Questions to Consider

1. **Multiple intervals**: Should we support 1h, 5m data or just daily (1d)?
2. **Stock info**: Should we fetch and store company fundamentals?
3. **Real-time data**: Do we need real-time quotes or historical only?
4. **Symbols list**: Should we provide a predefined list or free input?
5. **Data retention**: How long to keep historical data?
6. **Export**: Should users be able to export stock data to CSV/Excel?

---

## Conclusion

The implementation is **straightforward** because:
- ✅ YFinance downloader already exists and works
- ✅ TEFAS provides excellent reference pattern
- ✅ Can reuse 70% of infrastructure (DB engine, progress tracking, UI patterns)
- ✅ Main work is creating models, repository, service for stocks

**Recommendation**: Start with Phase 1 (Database & Core) to establish foundation, then iterate.

