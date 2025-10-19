# Stock Records Downloaded Progress Fix

## Problem
When downloading stock data, the "Records Downloaded" field in the UI was not updating in real-time during the download process.

## Root Cause
The frontend component `DownloadJobs.tsx` was always calling the TEFAS progress endpoint (`/api/database/download-progress`) regardless of the job's data type. Stock downloads have their own separate progress endpoint (`/api/stocks/download-progress`), so the frontend was fetching the wrong progress data for stock downloads.

## Solution

### Frontend Changes (`frontend/src/components/DownloadJobs.tsx`)

**Before:**
```typescript
const { data: downloadProgress } = useQuery<DownloadProgress>(
  'downloadProgress',
  databaseApi.getDownloadProgress,
  {
    refetchInterval: 1000,
    enabled: expandedJobId !== null && isJobActive(expandedJobId),
  }
);
```

**After:**
```typescript
// Get the data type of the expanded job
const expandedJobDataType = expandedJobId 
  ? historyData?.downloads.find(d => d.task_id === expandedJobId)?.data_type || 'tefas'
  : 'tefas';

// Fetch download progress for the expanded active job (calls the correct API based on job type)
const { data: downloadProgress } = useQuery<DownloadProgress>(
  ['downloadProgress', expandedJobDataType],
  () => expandedJobDataType === 'stock' ? stockApi.getDownloadProgress() : databaseApi.getDownloadProgress(),
  {
    refetchInterval: 1000, // Poll every second
    enabled: expandedJobId !== null && isJobActive(expandedJobId),
  }
);
```

### How It Works

1. **Job Type Detection**: When a job is expanded, the frontend determines its `data_type` ('tefas' or 'stock') from the download history.

2. **Dynamic API Selection**: Based on the job type:
   - Stock jobs → `stockApi.getDownloadProgress()` → `/api/stocks/download-progress`
   - TEFAS jobs → `databaseApi.getDownloadProgress()` → `/api/database/download-progress`

3. **Backend Processing** (already working correctly):
   - `StockPersistenceService` sends progress messages like: `✅ Downloaded AAPL: 250 records`
   - `stock_progress_callback` extracts the count using regex: `r'Downloaded.*?(\d+)\s+records'`
   - Updates `stock_download_progress["records_downloaded"]` by accumulating counts
   - Persists logs to database via `create_progress_log_entry()`

4. **UI Display** (already in place):
   - The "Records Downloaded" card displays: `{(downloadProgress.records_downloaded || 0).toLocaleString()}`
   - Polls every second for real-time updates

## Backend API Endpoints

### TEFAS Progress
```python
@app.get("/api/database/download-progress")
async def get_download_progress():
    return download_progress.copy()
```

### Stock Progress
```python
@app.get("/api/stocks/download-progress")
async def get_stock_download_progress():
    return stock_download_progress.copy()
```

## Testing

To verify the fix:
1. Start a stock download from the UI
2. Expand the active job in the "Download Jobs" tab
3. Observe the "Records Downloaded" counter updating in real-time as each symbol is downloaded

Expected behavior:
- Counter starts at 0
- Increases as each symbol's data is downloaded (e.g., +250 records for AAPL, +180 for MSFT, etc.)
- Updates every second during the download
- Shows final total when download completes

## Related Files

- `frontend/src/components/DownloadJobs.tsx` - Main UI component
- `backend/main.py` - API endpoints and progress callbacks
- `finance_tools/stocks/service.py` - Stock download service with progress reporting
- `frontend/src/services/api.ts` - API client with both TEFAS and stock endpoints

## Date
October 19, 2025

