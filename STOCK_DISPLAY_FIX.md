# Stock Download Display Fix

## Problem

Stock downloads were working in the backend (visible in logs and database) but not appearing in the frontend "Download Jobs" tab.

## Root Cause

The `/api/database/download-history` and `get_download_task_details` endpoints were not returning the new unified fields (`data_type`, `symbols`, `items_completed`, `items_failed`) that were added during the unified download tracking implementation.

The frontend expects these fields to:
1. Identify download type (TEFAS vs Stock)
2. Display appropriate information for each type
3. Show symbol lists for stock downloads

## Database Verification

```sql
SELECT task_id, data_type, kind, symbols, status 
FROM download_history 
WHERE data_type='stock';
```

Result:
```
342b0f50-9ccc-4ed3-8ddb-ed663737effa|stock|1d|["APPL", "MSFT", "GOOG"]|completed
```

✅ The data exists in the database correctly with `data_type='stock'`

## Fixes Applied

### 1. Updated `/api/database/download-history` endpoint (`backend/main.py`)

**Before:**
```python
"downloads": [
    {
        "id": d.id,
        "task_id": d.task_id,
        "start_date": d.start_date.isoformat(),
        "end_date": d.end_date.isoformat(),
        "kind": d.kind,
        "funds": d.funds or [],
        "status": d.status,
        # ... missing data_type and symbols
    }
    for d in downloads
]
```

**After:**
```python
"downloads": [
    {
        "id": d.id,
        "task_id": d.task_id,
        "data_type": getattr(d, 'data_type', 'tefas'),  # ✅ Added
        "start_date": d.start_date.isoformat(),
        "end_date": d.end_date.isoformat(),
        "kind": d.kind,
        "funds": d.funds or [],
        "symbols": getattr(d, 'symbols', None) or [],  # ✅ Added
        "status": d.status,
        "items_completed": getattr(d, 'items_completed', 0),  # ✅ Added
        "items_failed": getattr(d, 'items_failed', 0),  # ✅ Added
        # ...
    }
    for d in downloads
]
```

### 2. Updated `get_download_task_details` method (`finance_tools/etfs/tefas/repository.py`)

Added the same unified fields to the task details response:

```python
"task_info": {
    "id": download.id,
    "task_id": download.task_id,
    "data_type": getattr(download, 'data_type', 'tefas'),  # ✅ Added
    "start_date": download.start_date.isoformat(),
    "end_date": download.end_date.isoformat(),
    "kind": download.kind,
    "funds": download.funds or [],
    "symbols": getattr(download, 'symbols', None) or [],  # ✅ Added
    "status": download.status,
    # ...
    "items_completed": getattr(download, 'items_completed', 0),  # ✅ Added
    "items_failed": getattr(download, 'items_failed', 0),  # ✅ Added
}
```

## Why `getattr()` was used

Used `getattr(d, 'data_type', 'tefas')` for safety because:
1. Old records might not have these fields (pre-migration)
2. Provides default values for backward compatibility
3. Ensures no errors if a field is missing

## Frontend Display Logic

The frontend (`DownloadJobs.tsx`) enriches the data to create display information:

```typescript
const dataType = (d.data_type || 'tefas').toUpperCase() === 'STOCK' ? 'Stock' : 'TEFAS';

if (dataType === 'Stock') {
  const symbolCount = d.symbols?.length || 0;
  const interval = d.kind || '1d';
  displayInfo = `${symbolCount} symbols - ${interval}`;
} else {
  const fundCount = d.funds?.length || 0;
  const kind = d.kind || 'BYF';
  displayInfo = fundCount > 0 ? `${kind} - ${fundCount} funds` : `${kind} - All funds`;
}
```

## Expected Result

Now stock downloads will:
- ✅ Appear in the "Download Jobs" tab
- ✅ Show "Stock" chip with blue color
- ✅ Display symbol count and interval (e.g., "3 symbols - 1d")
- ✅ Show in both active and completed job lists
- ✅ Provide full details when clicked

## Testing

1. **Start a new stock download:**
   - Select "Stocks" tab in download modal
   - Add symbols (e.g., AAPL, MSFT)
   - Start download

2. **Verify during download:**
   - Job appears in "Download Jobs" with "Stock" chip
   - Shows real-time progress

3. **Verify after completion:**
   - Job remains visible with "completed" status
   - Shows symbol count and interval
   - Click to view full details and logs

## Files Modified

✅ `backend/main.py` - Updated download history endpoint
✅ `finance_tools/etfs/tefas/repository.py` - Updated task details method

---

**Status:** ✅ Fixed
**Date:** 2025-10-19
**Issue:** Stock downloads not visible in frontend
**Solution:** Added missing unified fields to API responses

