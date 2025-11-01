# Download Progress Analysis

## Current Progress Flow

### 1. Downloader Layer (`downloader.py`)

The `TefasDownloader` sends progress updates via callback with 3 parameters:
- `status` (str): Message describing current action
- `progress` (int): Progress percentage (0-100)
- `current_chunk` (int): Current chunk number

**Messages sent:**
```python
# Starting a chunk
f"Fetching data from {b_date} to {e_date}"

# Per-fund results
f"✅ Fetched data for {f_name}: {len(t_data)} rows"
f"⚠️ No data found for {f_name}"
f"❌ Error fetching data for {f_name}: {e}"

# All funds result (when funds=None)
f"✅ Fetched data: {len(t_data)} rows"

# Final completion
f"✅ Download completed! Total records: {len(funds_df)}"
```

**Key data available:**
- ✅ Total chunks: Calculated upfront
- ✅ Current chunk: Passed with each callback
- ✅ Records per chunk: Included in success messages
- ✅ Date range per chunk: In "Fetching data from..." messages
- ✅ Per-fund row counts: In "Fetched data for..." messages

### 2. Backend Progress Callback (`backend/main.py` lines 227-547)

The `progress_callback` function parses these messages and builds a rich progress object:

**Fields populated:**
```python
{
    # Basic progress
    "is_downloading": bool,
    "progress": int,  # 0-100
    "status": str,
    "current_phase": str,  # "initializing", "downloading", "completed", "error"
    
    # Record counts
    "records_downloaded": int,  # ✅ Live count, updated as records arrive
    "total_records": int,  # Set at completion
    
    # Chunk information
    "current_chunk_info": {
        "start_date": str,
        "end_date": str,
        "chunk_number": int,
        "total_chunks": int
    },
    
    # Detailed message log (last 50 messages)
    "detailed_messages": [
        {
            "timestamp": str,
            "message": str,
            "progress": int,
            "chunk": int,
            "type": "info" | "success" | "warning" | "error"
        }
    ],
    
    # Per-fund progress tracking
    "fund_progress": {
        "FUND_CODE": {
            "status": "success" | "no_data" | "error",
            "rows": int,
            "timestamp": str,
            "date_range": str,
            "enhanced_message": str,
            "error": str  # if applicable
        }
    },
    
    # Historical data
    "progress_history": [
        {
            "timestamp": str,
            "progress": int,
            "records_downloaded": int
        }
    ],
    
    # Calculated metrics
    "records_per_minute": float,
    "estimated_remaining_minutes": float
}
```

**Message parsing logic:**
- Extracts chunk info from "Fetching data from X to Y" messages
- Extracts fund data and row counts from "✅ Fetched data for..." messages
- **Accumulates** `records_downloaded` by adding row counts from success messages
- Enhances messages with date range information
- Stores progress logs in database for historical tracking

### 3. Frontend Display (`DownloadProgressBar.tsx`)

The component displays:

**Main metrics (lines 140-211):**
- Records Downloaded (with live update indicator)
- Total Records Target
- Elapsed Time
- Estimated Time of Arrival (ETA)

**Chunk Progress (lines 213-230):**
- Chunks Completed: `(chunk_number - 1) / total_chunks`
- Currently processing chunk number
- Chunk number display

**Chunk Details (lines 241-269):**
- Date range of current chunk
- Total records target

**Fund Progress (lines 271-295):**
- Successful funds count
- Failed funds count
- Total records from funds

**Downloaded Records Log (lines 297-331):**
- Last 8 success messages with row counts
- Timestamps for each entry
- Shows real-time as records are fetched

## Current Capabilities ✅

1. **Chunk counts**: ✅ Displayed (current/total)
2. **Downloaded records (live)**: ✅ Displayed with live indicator and updates in real-time
3. **Progress log per chunk**: ✅ Shows date ranges and record counts
4. **Per-fund progress**: ✅ Tracks success/failure and row counts per fund
5. **Enhanced messages**: ✅ Messages include date ranges for context

## Missing/Unclear Information ⚠️

### **Inserted Records vs Downloaded Records**

**Issue**: The system tracks **downloaded** (fetched from API) records but not **inserted** (saved to DB) records separately.

**Current flow:**
```
1. Download Phase:
   - progress_callback called with "✅ Fetched X rows..."
   - records_downloaded accumulates
   
2. Persistence Phase:
   - progress_callback("Saving data to database...", 90, 0)
   - persist_dataframe() called
   - Returns (info_count, breakdown_count) = INSERTED records
   - Final update sets records_downloaded = total_records
```

**Problem**: During download, `records_downloaded` represents **fetched** records. At completion, it's set to **inserted** records. There's no separate tracking of:
- How many records were actually inserted vs downloaded
- If duplicates were skipped (upsert behavior)
- Breakdown of info vs breakdown records during download

**Evidence from code:**
- `downloader.py` line 160: Returns total downloaded DataFrame
- `service.py` lines 56-62: Downloads first, then persists
- `backend/main.py` lines 636-649: Only updates with final counts at end

## Recommendations

### 1. Track Inserted Records Separately

Add a new field to distinguish downloaded vs inserted:

```python
{
    "records_fetched": int,      # From API (during download)
    "records_inserted": int,     # Saved to DB (info + breakdown)
    "records_info": int,         # Info table inserts
    "records_breakdown": int,    # Breakdown table inserts
}
```

### 2. Add Persistence Phase Progress

Currently, persistence is a single message. Add more granular updates:

```python
# In service.py persist_dataframe()
if self.progress_callback:
    self.progress_callback(f"Inserting {len(info_rows)} info records...", 92, 0)
    
# After info insert
if self.progress_callback:
    self.progress_callback(f"✅ Inserted {inserted_info} info records", 95, 0)
    
# After breakdown insert  
if self.progress_callback:
    self.progress_callback(f"✅ Inserted {inserted_breakdown} breakdown records", 98, 0)
```

### 3. Enhanced Chunk Summary

After each chunk completes, send a summary:

```python
# In downloader.py after chunk loop
chunk_summary = f"✅ Chunk {current_chunk}/{total_chunks} complete: {chunk_records} records from {start_date} to {end_date}"
if self.progress_callback:
    self.progress_callback(chunk_summary, progress_percent, current_chunk)
```

### 4. Frontend TypeScript Updates

Update `DownloadProgress` interface to include:

```typescript
export interface DownloadProgress {
  // ... existing fields ...
  
  records_fetched?: number;      // Downloaded from API
  records_inserted?: number;     // Saved to database
  records_info?: number;         // Info table count
  records_breakdown?: number;    // Breakdown table count
  
  // Per-chunk summaries
  chunk_summaries?: Array<{
    chunk_number: number;
    start_date: string;
    end_date: string;
    records_fetched: number;
    duration_seconds: number;
  }>;
}
```

## Summary

**What's working well:**
- ✅ Real-time progress updates (1 second polling)
- ✅ Detailed message logging with timestamps
- ✅ Chunk progress tracking
- ✅ Per-fund success/failure tracking
- ✅ Enhanced messages with date ranges
- ✅ Live record count updates

**What could be improved:**
- ⚠️ Separate tracking of fetched vs inserted records
- ⚠️ More granular persistence phase progress
- ⚠️ Per-chunk summary statistics
- ⚠️ Clearer distinction between download and save phases
- ⚠️ Database persistence progress (currently just "Saving...")

**Current polling intervals:**
- Download progress: 1 second (very responsive)
- Active tasks: 5 seconds
- Database stats: 30 seconds
- Task details: 5 seconds

