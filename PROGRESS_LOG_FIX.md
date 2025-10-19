# Progress Log Field Name Fix

## Problem

When clicking on a finished download job (TEFAS or Stock) to view details, the following error occurred:

```
ERROR - Error getting download task details: 'DownloadProgressLog' object has no attribute 'fund_name'
```

Frontend displayed: **"No details available for this job"**

## Root Cause

During the unified download tracking implementation, we renamed the `fund_name` field to `item_name` in the `DownloadProgressLog` model to make it generic (works for both fund names and stock symbols).

However, two methods in `TefasRepository` were still using the old `fund_name` attribute:

1. **`get_progress_logs()`** - Line 738: Tried to access `log.fund_name`
2. **`create_progress_log_entry()`** - Line 712: Tried to set `fund_name=fund_name`

Since the SQLAlchemy model no longer had `fund_name` as a mapped column (only `item_name`), accessing it raised an AttributeError.

## Database State

The database still has both columns (from migration):
```sql
PRAGMA table_info(download_progress_log);
-- Shows both:
-- 8|fund_name|VARCHAR(100)|0||0
-- 10|item_name|VARCHAR(100)|0||0
```

Migration successfully copied `fund_name` values to `item_name`:
```
Total records: 208
Has fund_name: 92
Has item_name: 100
```

## Fixes Applied

### 1. Fixed `get_progress_logs()` method

**Before:**
```python
return [
    {
        # ...
        "fund_name": log.fund_name,  # ❌ AttributeError!
        # ...
    }
    for log in logs
]
```

**After:**
```python
return [
    {
        # ...
        "item_name": getattr(log, 'item_name', None),  # ✅ Unified field
        "fund_name": getattr(log, 'item_name', None),  # ✅ Backward compatibility
        # ...
    }
    for log in logs
]
```

**Benefits:**
- Uses `item_name` from the model (works for both TEFAS and Stock)
- Provides `fund_name` alias for backward compatibility with frontend
- Uses `getattr()` for safety

### 2. Fixed `create_progress_log_entry()` method

**Before:**
```python
log_entry = DownloadProgressLog(
    task_id=task_id,
    # ...
    fund_name=fund_name  # ❌ Model doesn't have this field!
)
```

**After:**
```python
log_entry = DownloadProgressLog(
    task_id=task_id,
    # ...
    item_name=fund_name  # ✅ Maps to correct field
)
```

**Benefits:**
- Method signature unchanged (keeps `fund_name` parameter for backward compatibility)
- Maps `fund_name` parameter to `item_name` model field
- Works for both TEFAS (fund names) and Stock (symbols)

## Model Definition

The unified `DownloadProgressLog` model only has `item_name`:

```python
class DownloadProgressLog(Base):
    """
    Unified detailed progress log for both TEFAS and Stock download tasks.
    
    Fields usage:
    - TEFAS: item_name=fund_name, chunk_number=chunk number
    - Stock: item_name=symbol, chunk_number=symbol index
    """
    __tablename__ = "download_progress_log"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), index=True)
    # ...
    item_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # ✅ Unified field
    # Note: fund_name no longer in model
```

## Testing

### Test TEFAS Job Details
1. Click on a completed TEFAS download job
2. ✅ Should see full progress log history
3. ✅ Should see fund names in logs
4. ✅ Should see statistics (message counts)

### Test Stock Job Details
1. Click on a completed Stock download job
2. ✅ Should see full progress log history
3. ✅ Should see stock symbols in logs
4. ✅ Should see record counts per symbol

### Verify No Errors
1. Check backend logs
2. ✅ No more AttributeError
3. ✅ Job details load successfully

## API Response Format

The API now returns progress logs with both fields:

```json
{
  "task_info": { /* ... */ },
  "progress_logs": [
    {
      "id": 1,
      "task_id": "abc-123",
      "timestamp": "2025-10-19T20:00:00",
      "message": "✅ Downloaded AAPL: 250 records",
      "message_type": "success",
      "progress_percent": 30,
      "chunk_number": 1,
      "records_count": 250,
      "item_name": "AAPL",      // ✅ New unified field
      "fund_name": "AAPL",      // ✅ Backward compatibility alias
      "created_at": "2025-10-19T20:00:00"
    }
  ],
  "statistics": { /* ... */ }
}
```

## Backward Compatibility

The fix maintains backward compatibility:

1. **Method signatures unchanged**: `create_progress_log_entry()` still accepts `fund_name` parameter
2. **API response includes both fields**: Frontend can use either `item_name` or `fund_name`
3. **Database has both columns**: Old records still accessible
4. **TEFAS code unchanged**: Existing TEFAS download code works as-is

## Files Modified

✅ `finance_tools/etfs/tefas/repository.py`
  - Updated `get_progress_logs()` method
  - Updated `create_progress_log_entry()` method

## Summary

| Component | Old Field | New Field | Status |
|-----------|-----------|-----------|--------|
| Database | `fund_name` | `item_name` | ✅ Both exist |
| Model | `fund_name` | `item_name` | ✅ Only item_name |
| Repository Write | `fund_name` | `item_name` | ✅ Fixed |
| Repository Read | `log.fund_name` | `log.item_name` | ✅ Fixed |
| API Response | - | Both returned | ✅ Fixed |

---

**Status:** ✅ Fixed
**Date:** 2025-10-19
**Issue:** AttributeError when viewing job details
**Solution:** Updated repository methods to use `item_name` field
**Impact:** Job details now load correctly for both TEFAS and Stock downloads

