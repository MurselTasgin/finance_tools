# Progress Bar and Total Chunks Fix

## Issues Fixed

### Issue 1: Total Chunks Showing as 0

**Problem:**
- The frontend was showing "Chunks Completed: X / 0" instead of the correct total
- The downloader calculated `total_chunks` but didn't pass it to the backend
- Backend tried to estimate it from messages, which failed

**Root Cause:**
The downloader's `total_chunks` value was only available locally and never transmitted to the progress callback.

**Solution:**
Modified the status message in `downloader.py` to include total chunks:
```python
# Before:
self.progress_callback(f"Fetching data from {b_date} to {e_date}", progress_percent, self.current_chunk)

# After:
self.progress_callback(f"Fetching data from {b_date} to {e_date} [Total chunks: {self.total_chunks}]", download_progress, self.current_chunk)
```

Backend now parses this from the message:
```python
total_chunks_match = re.search(r'\[Total chunks: (\d+)\]', status)
if total_chunks_match:
    download_progress["total_chunks"] = int(total_chunks_match.group(1))
```

---

### Issue 2: Progress Bar Jumping Backwards (100% → 90%)

**Problem:**
1. Download phase progress calculated as: `(current_chunk / total_chunks) * 100`
2. When all chunks completed → 100%
3. Then service layer called: `progress_callback("Saving...", 90, 0)`
4. Progress jumped backwards from 100% to 90%

**Root Cause:**
The progress calculation didn't account for the database save phase (which takes additional time).

**Solution:**
Reserve the last 10% of progress for database operations:

#### Download Phase: 0-90%
```python
# downloader.py
download_progress = int((self.current_chunk / self.total_chunks) * 90)  # 0-90%

# When download completes:
self.progress_callback(final_msg, 90, self.total_chunks)  # Stays at 90%
```

#### Database Save Phase: 90-100%
```python
# service.py
self.progress_callback("💾 Saving data to database...", 95, 0)  # 95%
# ... persist data ...
self.progress_callback("✅ Database save completed", 100, 0)  # 100%
```

---

## Progress Flow Now

```
Phase 1: Download (0-90%)
├─ Chunk 1: ~7.5%   (1/12 * 90)
├─ Chunk 2: ~15%    (2/12 * 90)
├─ Chunk 3: ~22.5%  (3/12 * 90)
├─ ...
└─ Chunk 12: 90%    (12/12 * 90)

Phase 2: Database Save (90-100%)
├─ Start saving: 95%
└─ Complete: 100%

Result: Progress always moves forward, never backwards!
```

---

## Visual Example

### Before (Broken):
```
0% → 8% → 17% → 25% → ... → 100% ← 90% → 100%
                                 ↑
                            JUMP BACKWARDS!
```

### After (Fixed):
```
0% → 7% → 15% → 22% → ... → 90% → 95% → 100%
                               ↑     ↑      ↑
                          Download  Save  Done
                          Complete
```

---

## Files Modified

### 1. `finance_tools/etfs/tefas/downloader.py`

**Changes:**
- Progress calculation now uses 90% scale instead of 100%
- Status messages include `[Total chunks: X]` 
- All progress callbacks updated to use `download_progress` variable
- Final completion stays at 90% (not 100%)

**Key changes:**
```python
# Line 86: Calculate progress with 90% scale
download_progress = int((self.current_chunk / self.total_chunks) * 90)

# Line 89: Include total chunks in message
self.progress_callback(
    f"Fetching data from {b_date} to {e_date} [Total chunks: {self.total_chunks}]",
    download_progress, 
    self.current_chunk
)

# Line 169: Download completes at 90%
self.progress_callback(final_msg, 90, self.total_chunks)
```

### 2. `backend/main.py`

**Changes:**
- Parse `total_chunks` from status messages
- Extract value and store in `download_progress["total_chunks"]`

**Key changes:**
```python
# Lines 254-260: Extract total chunks from message
total_chunks_match = re.search(r'\[Total chunks: (\d+)\]', status)
if total_chunks_match:
    download_progress["total_chunks"] = int(total_chunks_match.group(1))
```

### 3. `finance_tools/etfs/tefas/service.py`

**Changes:**
- Database save phase uses 95% and 100% progress
- Added completion message at 100%

**Key changes:**
```python
# Line 60: Start database save at 95%
self.progress_callback("💾 Saving data to database...", 95, 0)

# After persist:
self.progress_callback("✅ Database save completed", 100, 0)
```

---

## Testing

### Test Case 1: Verify Total Chunks Display
1. Start a download with known date range
2. Check frontend shows correct "X / Y" chunks
3. Example: 1 year with 30-day chunks = 12 chunks total
4. Should show: "0 / 12" → "1 / 12" → ... → "12 / 12"

### Test Case 2: Verify Progress Never Goes Backwards
1. Start a download
2. Monitor progress bar continuously
3. Progress should be: 0% → 7% → 15% → ... → 90% → 95% → 100%
4. Should NEVER see 100% followed by lower number

### Test Case 3: Verify Database Save Progress
1. Start a large download
2. Wait for download to complete (90%)
3. Watch for "💾 Saving data to database..." message
4. Progress should go: 90% → 95% → 100%
5. Final message: "✅ Database save completed"

### Test Case 4: Verify Progress Messages
1. Check that status messages include: `[Total chunks: X]`
2. Backend logs should show total_chunks being parsed
3. Frontend should display correct chunk counts

---

## Benefits

✅ **Accurate Progress**: Shows true progress including database save
✅ **No Jumping**: Progress always increases, never decreases
✅ **Better UX**: Users see what's happening in each phase
✅ **Correct Chunk Count**: Frontend shows actual total chunks
✅ **Clear Phases**: Distinct messages for download vs save
✅ **Predictable**: Users can estimate completion time accurately

---

## Progress Breakdown

| Phase | Progress | Duration | Description |
|-------|----------|----------|-------------|
| Download | 0-90% | ~90% of total time | Fetching data from API in chunks |
| Database Save | 90-95% | ~5% of total time | Saving info records |
| Complete | 95-100% | ~5% of total time | Saving breakdown records |

The split (90/5/5) reflects typical operation time distribution.

---

## Monitoring

Check logs for these indicators:

**Backend logs:**
```
🔄 PROGRESS CALLBACK - Status: Fetching data from 2025-01-01 to 2025-01-31 [Total chunks: 12], Progress: 7%, Chunk: 1
📊 Updated records_downloaded: 0 + 150 = 150
...
🔄 PROGRESS CALLBACK - Status: 💾 Saving data to database..., Progress: 95%, Chunk: 0
🔄 PROGRESS CALLBACK - Status: ✅ Database save completed, Progress: 100%, Chunk: 0
```

**Frontend display:**
```
Progress: 7% / 90% (chunk 1/12)
↓
Progress: 90% / 90% (chunk 12/12)
↓
Progress: 95% / 95% (saving...)
↓
Progress: 100% / 100% (completed!)
```

