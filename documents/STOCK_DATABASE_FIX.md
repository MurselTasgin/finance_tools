# Stock Database Tables Fix

## Problem
Stock download jobs were failing with errors:
```
sqlite3.OperationalError: no such table: stock_info
sqlite3.OperationalError: no such table: stock_download_history
sqlite3.OperationalError: no such table: stock_price_history
```

## Root Cause
The stock database tables were not being created because:
1. Stock models were defined but not imported during database initialization
2. SQLAlchemy's `Base.metadata.create_all()` only creates tables for models it knows about
3. The models need to be imported before `create_all()` is called

## Solution

### 1. Updated `finance_tools/etfs/tefas/repository.py`

Added stock model imports at the module level:

```python
# Import stock models to ensure they're registered with SQLAlchemy Base
# This must happen before create_all() is called
try:
    from ...stocks.models import StockPriceHistory, StockInfo, StockDownloadHistory, StockDownloadProgressLog
    STOCK_MODELS_AVAILABLE = True
except ImportError:
    STOCK_MODELS_AVAILABLE = False
```

Updated `is_initialized()` to check for stock tables:

```python
def is_initialized(self) -> bool:
    """Check whether all required tables exist in the database."""
    engine = self.get_engine()
    inspector = inspect(engine)
    required_tables = [
        TefasFundInfo.__tablename__,
        TefasFundBreakdown.__tablename__,
        'download_history',
        'download_progress_log',
    ]
    
    # Add stock tables if stock models are available
    if STOCK_MODELS_AVAILABLE:
        required_tables.extend([
            'stock_price_history',
            'stock_info',
            'stock_download_history',
            'stock_download_progress_log',
        ])
    
    return all(inspector.has_table(t) for t in required_tables)
```

### 2. Created Initialization Script

Created `init_stock_tables.py` to manually initialize database tables:

```bash
python init_stock_tables.py
```

This script:
- Checks which tables exist
- Creates missing tables
- Verifies all tables were created successfully

## Tables Created

✅ All 8 tables now exist in the database:

**TEFAS Tables:**
1. `tefas_fund_info` - TEFAS fund price data
2. `tefas_fund_breakdown` - TEFAS fund breakdown data
3. `download_history` - TEFAS download tracking
4. `download_progress_log` - TEFAS progress logs

**Stock Tables:**
5. `stock_price_history` - Stock OHLCV data
6. `stock_info` - Company information
7. `stock_download_history` - Stock download tracking
8. `stock_download_progress_log` - Stock progress logs

## Verification

Run the initialization script to verify:

```bash
cd /Users/murseltasgin/projects/finance_tools
python init_stock_tables.py
```

Expected output:
```
============================================================
Initializing Stock Database Tables
============================================================
Database path: /Users/murseltasgin/projects/finance_tools/test_finance_tools.db
✅ All tables already exist!

📊 Available tables:
  ✓ download_history
  ✓ download_progress_log
  ✓ stock_download_history
  ✓ stock_download_progress_log
  ✓ stock_info
  ✓ stock_price_history
  ✓ tefas_fund_breakdown
  ✓ tefas_fund_info

============================================================
Initialization Complete!
============================================================
```

## Testing

Now you can test stock downloads:

1. **Restart the backend** (if it's running):
   ```bash
   # Stop the current backend (Ctrl+C)
   # Then restart:
   cd backend
   python main.py
   ```

2. **Test stock download via UI**:
   - Open http://localhost:3000
   - Go to "Data Management" → "Download Jobs"
   - Click "New Download"
   - Select "Stocks" tab
   - Add symbols: AAPL, MSFT, GOOGL
   - Click "Download Data"

3. **Test stock download via API**:
   ```bash
   curl -X POST http://localhost:8070/api/stocks/download \
     -H "Content-Type: application/json" \
     -d '{
       "symbols": ["AAPL", "MSFT"],
       "startDate": "2024-01-01",
       "endDate": "2024-12-31",
       "interval": "1d"
     }'
   ```

## Future Behavior

Going forward:
- ✅ New database instances will automatically create all tables (TEFAS + Stock)
- ✅ `DatabaseEngineProvider.ensure_initialized()` checks for all tables
- ✅ Missing tables are created automatically on first backend startup
- ✅ No manual intervention needed for new deployments

## Files Modified

1. ✅ `finance_tools/etfs/tefas/repository.py` - Added stock model imports and updated initialization logic
2. ✅ `init_stock_tables.py` - Created initialization script for manual table creation

---

**Status:** ✅ Fixed and Verified
**Date:** 2025-10-19
**Issue:** Stock tables missing
**Solution:** Import stock models during database initialization
**Result:** All 8 tables created successfully

