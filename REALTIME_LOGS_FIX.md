# Real-time Progress Logs Fix for Stock Downloads

## Problem

Stock download progress logs appeared **all at once when the job finished**, not in real-time during the download. TEFAS downloads showed real-time logs, but stock downloads didn't.

## Root Cause

The frontend had conditional logic that prevented polling for progress logs during active downloads:

```typescript
// OLD CODE - BROKEN
const { data: jobDetails } = useQuery(
  ['downloadTaskDetails', expandedJobId],
  () => databaseApi.getDownloadTaskDetails(expandedJobId!),
  {
    enabled: expandedJobId !== null && !isJobActive(expandedJobId),  // ❌ Only for completed jobs!
    refetchInterval: (data) => {
      const status = historyData?.downloads.find(d => d.task_id === expandedJobId)?.status;
      return status === 'running' ? 5000 : false;
    },
  }
);
```

The condition `!isJobActive(expandedJobId)` meant:
- ❌ **Active jobs**: Query DISABLED → No logs fetched
- ✅ **Completed jobs**: Query ENABLED → Logs fetched

So during an active download:
1. Logs were being saved to the database correctly (backend working)
2. Frontend was NOT polling the database for logs (frontend not polling)
3. When job finished, query became enabled
4. All logs appeared at once

## Why TEFAS Appeared to Work

TEFAS downloads use a different mechanism with in-memory `detailed_messages` in the `downloadProgress` object, which is polled separately. Stock downloads didn't have this, so they relied entirely on database logs.

## Fixes Applied

### 1. Enable Polling for Active Jobs

**File**: `frontend/src/components/DownloadJobs.tsx`

Changed the `jobDetails` query to poll for **both active AND completed** jobs:

```typescript
// NEW CODE - FIXED
const { data: jobDetails, isLoading: detailsLoading } = useQuery(
  ['downloadTaskDetails', expandedJobId],
  () => databaseApi.getDownloadTaskDetails(expandedJobId!),
  {
    enabled: expandedJobId !== null,  // ✅ Poll for ALL expanded jobs
    refetchInterval: (data) => {
      if (!expandedJobId) return false;
      
      // For active jobs, poll every 2 seconds for real-time logs
      if (isJobActive(expandedJobId)) {
        return 2000;  // ✅ Fast polling for active jobs
      }
      
      // For completed/failed/cancelled jobs, don't poll
      const status = historyData?.downloads.find(d => d.task_id === expandedJobId)?.status;
      return (status === 'running') ? 5000 : false;
    },
  }
);
```

**Key Changes:**
- Removed `!isJobActive(expandedJobId)` condition
- Added 2-second polling for active jobs
- Stops polling when job completes

### 2. Display Database Logs for Active Jobs

Updated the active job rendering to show logs from `jobDetails` (database) instead of only `downloadProgress` (in-memory):

```typescript
// NEW CODE - Show database logs for active jobs
{jobDetails && jobDetails.progress_logs && jobDetails.progress_logs.length > 0 && (
  <Box>
    <Typography variant="subtitle2" gutterBottom>
      Progress Logs (Real-time)
    </Typography>
    <Paper variant="outlined" sx={{ maxHeight: 400, overflowY: 'auto', p: 2 }}>
      <List dense>
        {jobDetails.progress_logs.map((log) => (
          <ListItem key={log.id} sx={{ py: 0.5 }}>
            <ListItemIcon sx={{ minWidth: 36 }}>
              {getMessageIcon(log.message_type)}
            </ListItemIcon>
            <ListItemText
              primary={log.message}
              secondary={formatTime(log.timestamp)}
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  </Box>
)}

{/* Fallback to in-memory messages if no DB logs yet */}
{(!jobDetails || !jobDetails.progress_logs || jobDetails.progress_logs.length === 0) && 
 downloadProgress.detailed_messages && downloadProgress.detailed_messages.length > 0 && (
  // ... show in-memory messages as fallback
)}
```

**Key Changes:**
- Primary display: Database logs from `jobDetails.progress_logs`
- Fallback: In-memory messages from `downloadProgress.detailed_messages`
- Works for both TEFAS and Stock downloads

## How It Works Now

### During Active Download

1. **Backend saves logs** to `download_progress_log` table every 2-3 seconds
   ```sql
   INSERT INTO download_progress_log (task_id, message, timestamp, ...)
   VALUES ('abc-123', '📊 Downloading AAPL (1/3)...', '2025-10-19 20:00:01', ...);
   ```

2. **Frontend polls** `/api/database/download-task-details/{task_id}` every 2 seconds
   ```
   GET /api/database/download-task-details/abc-123
   Response: {
     task_info: {...},
     progress_logs: [
       { message: '📊 Downloading AAPL (1/3)...', timestamp: '...', ... },
       { message: '✅ Downloaded AAPL: 250 records', timestamp: '...', ... }
     ],
     statistics: {...}
   }
   ```

3. **UI updates** with new logs appearing in real-time
   ```
   📊 Downloading AAPL (1/3)...      20:00:01
   ✅ Downloaded AAPL: 250 records   20:00:05
   📊 Downloading MSFT (2/3)...      20:00:06  ← NEW!
   ```

4. **Auto-scrolls** to show latest log (browser behavior)

### After Completion

1. **isJobActive(taskId)** returns `false`
2. **Polling stops** (refetchInterval returns `false`)
3. **Final logs displayed** from last fetch
4. **Statistics calculated** from all logs

## Timeline Comparison

### Before Fix (❌ Broken)

```
00:00 - Start stock download (AAPL, MSFT, GOOGL)
00:00 - User expands job
00:00 - Frontend: jobDetails query DISABLED (job is active)
00:01 - Backend: Saves log "Downloading AAPL"
00:03 - Backend: Saves log "Downloaded AAPL: 250 records"
00:05 - Backend: Saves log "Downloading MSFT"
00:07 - Backend: Saves log "Downloaded MSFT: 300 records"
00:09 - Backend: Saves log "Downloading GOOGL"
00:11 - Backend: Saves log "Downloaded GOOGL: 200 records"
00:12 - Backend: Saves log "Download completed"
00:12 - Job status changes to "completed"
00:12 - Frontend: jobDetails query ENABLED (job completed)
00:12 - Frontend: Fetches ALL logs at once
00:12 - UI: Shows all 7 logs suddenly ❌
```

### After Fix (✅ Working)

```
00:00 - Start stock download (AAPL, MSFT, GOOGL)
00:00 - User expands job
00:00 - Frontend: jobDetails query ENABLED (polls every 2s)
00:01 - Backend: Saves log "Downloading AAPL"
00:02 - Frontend: Polls, gets 1 log, displays ✅
00:03 - Backend: Saves log "Downloaded AAPL: 250 records"
00:04 - Frontend: Polls, gets 2 logs, displays ✅
00:05 - Backend: Saves log "Downloading MSFT"
00:06 - Frontend: Polls, gets 3 logs, displays ✅
00:07 - Backend: Saves log "Downloaded MSFT: 300 records"
00:08 - Frontend: Polls, gets 4 logs, displays ✅
00:09 - Backend: Saves log "Downloading GOOGL"
00:10 - Frontend: Polls, gets 5 logs, displays ✅
00:11 - Backend: Saves log "Downloaded GOOGL: 200 records"
00:12 - Backend: Saves log "Download completed"
00:12 - Frontend: Polls, gets 7 logs, displays ✅
00:12 - Job completes, polling stops
```

## Benefits

1. ✅ **Real-time visibility**: See progress as it happens
2. ✅ **Same experience for TEFAS and Stock**: Unified behavior
3. ✅ **Efficient polling**: 2-second interval balances freshness and performance
4. ✅ **Auto-stops polling**: No wasted requests after completion
5. ✅ **Fallback support**: Can still show in-memory logs if needed

## Testing

### Test Stock Download Real-time Logs

1. Start stock download (AAPL, MSFT, GOOGL)
2. Immediately expand the running job
3. ✅ Should see logs appearing every 2-3 seconds:
   ```
   📊 Downloading AAPL (1/3)...
   ✅ Downloaded AAPL: 250 records
   📊 Downloading MSFT (2/3)...
   ✅ Downloaded MSFT: 300 records
   ...
   ```
4. ✅ Logs should appear incrementally, not all at once
5. ✅ Progress bar should update smoothly

### Test TEFAS Download Real-time Logs

1. Start TEFAS download
2. Expand the running job
3. ✅ Should also see real-time logs (unchanged behavior)

### Test Completed Job

1. Wait for any job to complete
2. Expand it
3. ✅ Should show full log history
4. ✅ Polling should stop (check network tab - no more requests)

### Verify Polling Stops

1. Open browser DevTools → Network tab
2. Expand an active job
3. ✅ See requests every 2 seconds: `GET /api/database/download-task-details/...`
4. Wait for job to complete
5. ✅ Requests should stop

## Performance Considerations

### Polling Frequency

- **Active jobs**: 2 seconds (500 requests/hour max)
- **Completed jobs**: No polling (0 requests)

### Network Impact

For a 30-second stock download:
- **Before**: 1 request (at completion)
- **After**: ~15 requests (every 2 seconds)
- **Acceptable**: Modern APIs easily handle this load

### Database Impact

- Each request queries: `SELECT * FROM download_progress_log WHERE task_id = ?`
- Indexed on `task_id` → Fast lookup
- Typical result: 10-50 rows → Lightweight

## Files Modified

✅ `frontend/src/components/DownloadJobs.tsx`
  - Changed `jobDetails` query condition
  - Added polling for active jobs
  - Updated rendering to show database logs

## Architecture

```
Stock Download Running
    ↓
Backend saves log to DB every few seconds
    ↓
Frontend polls /api/database/download-task-details/{task_id} every 2s
    ↓
jobDetails updated with new logs
    ↓
UI re-renders with new log entries
    ↓
User sees real-time progress
```

---

**Status:** ✅ Fixed
**Date:** 2025-10-19
**Issue:** Stock logs appeared all at once when job finished
**Solution:** Enable polling for active jobs
**Impact:** Real-time log visibility for all downloads

