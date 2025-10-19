# Download Manager Fix - Show All Running Tasks

## Problem

Tasks showing as "Running" in the **Download History** tab were not appearing in the **Download Manager** tab.

### Root Cause

1. **Download History** fetches from the **database** (`download_history` table)
   - Shows all tasks with any status, including "running"
   
2. **Download Manager** fetches from **in-memory** `active_tasks` dictionary
   - Only shows tasks currently in memory
   
3. **Mismatch occurs when**:
   - Server restarts (memory cleared but DB still has "running" tasks)
   - Tasks fail silently and get cleaned up from memory but not updated in DB
   - Tasks complete but DB update fails

## Solution Implemented

### 1. Startup Handler (✅ Completed)

Added `@app.on_event("startup")` handler in `backend/main.py`:

```python
@app.on_event("startup")
async def startup_event():
    """Clean up orphaned 'running' tasks on server startup."""
    # Find all tasks with 'running' status and mark them as 'failed'
    # with error message: "Task interrupted by server restart or crash"
```

**What it does**:
- Runs once when server starts
- Finds all tasks with status="running" in database
- Marks them as "failed" with appropriate error message
- Prevents old interrupted tasks from showing as "running"

### 2. Repository Method (✅ Completed)

Added `cleanup_orphaned_running_tasks()` to `finance_tools/etfs/tefas/repository.py`:

```python
def cleanup_orphaned_running_tasks(self) -> int:
    """
    Mark all 'running' tasks as 'failed' if they're not in active memory.
    Returns number of tasks cleaned up.
    """
    running_tasks = self.session.query(DownloadHistory)\
        .filter(DownloadHistory.status == 'running')\
        .all()
    
    for task in running_tasks:
        task.status = 'failed'
        task.end_time = datetime.utcnow()
        task.error_message = 'Task interrupted by server restart or crash'
    
    self.session.commit()
    return len(running_tasks)
```

### 3. Enhanced Active Tasks Endpoint (✅ Completed)

Modified `/api/database/tasks` in `backend/main.py` to fetch from **both** sources:

```python
@app.get("/api/database/tasks")
async def get_active_tasks(session = Depends(get_db_session)):
    """Get list of active download tasks from both memory and database."""
    # 1. Get tasks from memory (in-memory active_tasks dict)
    # 2. Get tasks from database (status='running')
    # 3. Merge them (avoid duplicates)
    # 4. Add 'source' field to track origin
```

**Benefits**:
- Shows ALL truly running tasks
- Combines memory and database sources
- Prevents lost tasks from disappearing
- Adds 'source' field ('memory' or 'database') for debugging

### 4. Frontend Compatibility (✅ Already Compatible)

The existing frontend components already handle multiple tasks:

**`DownloadManager.tsx` (lines 211-240)**:
```typescript
{activeTasks?.tasks.map((task, index) => (
  <Box key={task.task_id || index}>
    {/* Shows task details */}
  </Box>
))}
```

**`EnhancedDownloadManager.tsx` (lines 365-439)**:
```typescript
{activeTasks.tasks.map((task) => (
  <Card key={task.task_id} variant="outlined">
    {/* Shows task details with cancel button */}
  </Card>
))}
```

Both components iterate over the `tasks` array, so they'll automatically display all tasks returned by the API.

## How It Works Now

### Scenario 1: Normal Operation
```
User starts download
  ↓
Task added to active_tasks (memory) + database (status='running')
  ↓
Frontend polls /api/database/tasks
  ↓
Shows task in Download Manager (source='memory')
  ↓
Task completes
  ↓
Database updated (status='completed')
  ↓
Task removed from memory
  ↓
Download Manager no longer shows it
```

### Scenario 2: Server Restart During Download
```
Task is running (in memory + DB status='running')
  ↓
Server restarts
  ↓
Memory cleared (active_tasks = {})
  ↓
Startup handler runs
  ↓
Finds "running" task in DB
  ↓
Marks as "failed" with error message
  ↓
Download History shows it as "Failed"
  ↓
Download Manager doesn't show it (correct behavior)
```

### Scenario 3: Task Lost from Memory (Edge Case)
```
Task somehow lost from active_tasks (bug, cleanup error, etc.)
  ↓
But still marked as 'running' in database
  ↓
Frontend polls /api/database/tasks
  ↓
Endpoint queries both memory AND database
  ↓
Finds task in database with status='running'
  ↓
Shows in Download Manager (source='database')
  ↓
User can see and potentially cancel it
```

## API Response Changes

### Before:
```json
{
  "active_tasks": 1,
  "tasks": [
    {
      "task_id": "abc-123",
      "status": "running",
      "start_time": "2025-10-19T10:00:00",
      // ... other fields
    }
  ]
}
```

### After (with source field):
```json
{
  "active_tasks": 2,
  "tasks": [
    {
      "task_id": "abc-123",
      "status": "running",
      "start_time": "2025-10-19T10:00:00",
      "source": "memory",  // ← NEW
      // ... other fields
    },
    {
      "task_id": "def-456",
      "status": "running",
      "start_time": "2025-10-19T09:50:00",
      "source": "database",  // ← NEW (orphaned task)
      // ... other fields
    }
  ]
}
```

## Testing

### Test Case 1: Normal Download
1. Start a download from the UI
2. Check Download Manager - should show the running task
3. Check Download History - should show the task as "Running"
4. Wait for completion
5. Download Manager should clear
6. Download History should show as "Completed"

### Test Case 2: Server Restart During Download
1. Start a download
2. While it's running, restart the backend server
3. On startup, check logs for: "Cleaned up X orphaned 'running' tasks"
4. Check Download Manager - should be empty
5. Check Download History - task should show as "Failed" with message "Task interrupted by server restart or crash"

### Test Case 3: Multiple Simultaneous Downloads
1. Start multiple downloads (if supported)
2. Check Download Manager - should show all running tasks
3. Each should have its own progress display
4. Check that cancel works for each

## Benefits

✅ **No Lost Tasks**: All running tasks are now visible
✅ **Clean Startup**: Old interrupted tasks are properly marked as failed
✅ **Accurate Status**: Download Manager reflects true system state
✅ **Debugging**: `source` field helps identify where task info came from
✅ **Graceful Degradation**: Works even if memory and DB are out of sync

## Files Modified

1. `backend/main.py`:
   - Added `startup_event()` handler
   - Modified `get_active_tasks()` endpoint
   - Added `startup_cleanup_done` flag

2. `finance_tools/etfs/tefas/repository.py`:
   - Added `cleanup_orphaned_running_tasks()` method

## No Frontend Changes Required

The frontend components (`DownloadManager.tsx`, `EnhancedDownloadManager.tsx`) already iterate over the `tasks` array, so they automatically handle multiple tasks and will display all running tasks without any code changes.

## Monitoring

Check server logs on startup for:
```
🚀 Server startup: Cleaning up orphaned 'running' tasks...
✅ Cleaned up N orphaned 'running' tasks
```

Or:
```
✅ No orphaned 'running' tasks found
```

Check API logs when fetching active tasks:
```
📊 API - get_active_tasks returning: 2 tasks (1 from memory, 1 from database)
```

