# Download Jobs Display Fix - Stock Downloads Not Showing

## Problem
Stock download jobs were not appearing in the Download Jobs list. They would start but immediately disappear from the UI.

## Root Cause
The `DownloadJobs` component was only fetching TEFAS download history from `/api/database/download-history`. Stock downloads were being saved to a separate `stock_download_history` table and were not being fetched or displayed.

## Solution

### 1. Fetch Both TEFAS and Stock Histories

Modified `DownloadJobs.tsx` to fetch both histories separately and merge them:

```typescript
// Fetch TEFAS download history
const { data: tefasHistoryData } = useQuery(
  ['tefasDownloadHistory', page + 1, rowsPerPage, searchTerm, statusFilter],
  () => databaseApi.getDownloadHistory({...}),
  { refetchInterval: 5000 }
);

// Fetch Stock download history
const { data: stockHistoryData } = useQuery(
  ['stockDownloadHistory', page + 1, rowsPerPage, searchTerm, statusFilter],
  () => stockApi.getHistory({...}),
  { refetchInterval: 5000 }
);
```

### 2. Merge and Enrich Data

Created a `useMemo` hook to merge both histories with additional metadata:

```typescript
const historyData = React.useMemo(() => {
  // Add data_type and display_info to each download
  const tefasDownloads = (tefasHistoryData?.downloads || []).map(d => ({
    ...d,
    data_type: 'TEFAS',
    display_info: `${d.kind || 'BYF'} - ${d.funds?.length || 0} funds`,
  }));
  
  const stockDownloads = (stockHistoryData?.downloads || []).map(d => ({
    ...d,
    data_type: 'Stock',
    display_info: `${d.symbols?.length || 0} symbols - ${d.interval || '1d'}`,
  }));
  
  // Merge and sort by start_time (most recent first)
  const allDownloads = [...tefasDownloads, ...stockDownloads].sort((a, b) => {
    return new Date(b.start_time).getTime() - new Date(a.start_time).getTime();
  });
  
  return { downloads: allDownloads, total, page, pageSize };
}, [tefasHistoryData, stockHistoryData, page, rowsPerPage]);
```

### 3. Update Table Display

Updated the table to show unified data:

**Before:**
- Type column showed: TEFAS `kind` (BYF, YAT, EMK)
- Details column showed: Fund codes

**After:**
- Type column shows: **TEFAS** (secondary chip) or **Stock** (primary chip)
- Details column shows:
  - TEFAS: `BYF - 3 funds` or `YAT - 0 funds (All funds)`
  - Stock: `3 symbols - 1d` or `5 symbols - 1h`

```typescript
<TableCell>
  <Chip 
    label={job.data_type || 'TEFAS'} 
    size="small" 
    variant="outlined"
    color={job.data_type === 'Stock' ? 'primary' : 'secondary'}
  />
</TableCell>
<TableCell>
  <Typography variant="body2" color="textSecondary">
    {job.display_info || (job.funds?.length > 0 ? job.funds.join(', ') : 'All funds')}
  </Typography>
</TableCell>
```

### 4. Update Query Invalidation

Updated all mutations to invalidate both history queries:

```typescript
onSuccess: () => {
  queryClient.invalidateQueries('databaseStats');
  queryClient.invalidateQueries('tefasDownloadHistory');  // TEFAS
  queryClient.invalidateQueries('stockDownloadHistory');  // Stock
  queryClient.invalidateQueries('activeTasks');
}
```

## Features

### Unified View
- ✅ **Single table** showing both TEFAS and Stock downloads
- ✅ **Color-coded** chips for easy identification
- ✅ **Sorted chronologically** (most recent first)
- ✅ **Real-time updates** every 5 seconds

### Data Type Display
- **TEFAS** - Shows as secondary (purple) chip
- **Stock** - Shows as primary (blue) chip

### Details Column
- **TEFAS**: Shows fund type and count (e.g., "BYF - 3 funds")
- **Stock**: Shows symbol count and interval (e.g., "5 symbols - 1d")

### Status Tracking
- Both types use the same status system:
  - 🟡 Running
  - ✅ Completed
  - ❌ Failed
  - 🚫 Cancelled

## Testing

### Test TEFAS Download:
1. Open "Download Jobs"
2. Click "New Download"
3. Stay on "TEFAS Funds" tab
4. Download some data
5. ✅ Should appear in list with **TEFAS** chip

### Test Stock Download:
1. Open "Download Jobs"
2. Click "New Download"
3. Switch to "**Stocks**" tab
4. Add symbols: AAPL, MSFT
5. Download data
6. ✅ Should appear in list with **Stock** chip

### Test Mixed List:
1. Download both TEFAS and Stock data
2. ✅ Should see both in the same table
3. ✅ Sorted by most recent first
4. ✅ Each with appropriate type chip and details

## Table Headers

Updated headers to be more generic:

| Header | Description |
|--------|-------------|
| Date Range | Start date - End date |
| **Data Type** | TEFAS or Stock |
| **Details** | Type-specific info (funds/symbols) |
| Status | Running, Completed, Failed, Cancelled |
| Duration | Time taken |
| Records | Downloaded/Total |
| Started | Start timestamp |

## Files Modified

✅ `frontend/src/components/DownloadJobs.tsx`
- Added stock history query
- Merged TEFAS and stock histories
- Updated table display
- Updated query invalidation

## Benefits

1. **Unified Experience**: Users see all downloads in one place
2. **Clear Identification**: Easy to distinguish TEFAS vs Stock
3. **Consistent UI**: Same table format for both types
4. **Real-time Updates**: Both types update automatically
5. **Scalable**: Easy to add more data types in future

---

**Status:** ✅ Fixed and Tested
**Date:** 2025-10-19
**Issue:** Stock downloads not showing in Download Jobs
**Solution:** Fetch and merge both TEFAS and Stock histories
**Result:** Unified download jobs table showing both types

