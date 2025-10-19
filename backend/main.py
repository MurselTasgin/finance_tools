# finance_tools/backend/main.py
import os
from pathlib import Path
# Override database to use test database with data - MUST be set before any imports
parent_dir = Path(__file__).parent.parent
os.environ["DATABASE_NAME"] = os.path.join(parent_dir, "test_finance_tools.db")

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import threading
import time
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import date, datetime, timedelta
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Add the parent directory to the path to import finance_tools modules
sys.path.append(str(Path(__file__).parent.parent))

from finance_tools.etfs.tefas.repository import DatabaseEngineProvider, TefasRepository
from finance_tools.etfs.tefas.service import TefasPersistenceService
from finance_tools.stocks.service import StockPersistenceService
from finance_tools.stocks.repository import StockRepository
from finance_tools.config import get_config
from finance_tools.logging import get_logger

print(f"Database name: {os.environ['DATABASE_NAME']}")

app = FastAPI(
    title="Finance Tools API",
    description="API for ETF data management and analysis",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3002", 
        "http://127.0.0.1:3002"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = get_logger("api")

# Global state for download progress
download_progress = {
    "is_downloading": False,
    "progress": 0,
    "status": "",
    "records_downloaded": 0,
    "total_records": 0,
    "start_time": None,
    "estimated_completion": None,
    "current_phase": "",
    "task_id": None,
    "error": None,
    "last_activity": None,  # Last time progress was updated
    "progress_history": [],  # Last 5 minutes of progress updates
    "records_per_minute": 0,  # Current processing rate
    "estimated_remaining_minutes": None,  # Estimated time to completion
}

# Thread pool executor for background tasks
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="download_worker")

# Store active tasks
active_tasks = {}

# Store cancellation flags for tasks
cancellation_flags = {}

# Track if startup cleanup has been done
startup_cleanup_done = False

def get_db_session():
    """Dependency to get database session."""
    db_provider = DatabaseEngineProvider()
    db_provider.ensure_initialized()
    SessionLocal = db_provider.get_session_factory()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@app.on_event("startup")
async def startup_event():
    """Clean up orphaned 'running' tasks on server startup."""
    global startup_cleanup_done
    if startup_cleanup_done:
        return
    
    logger.info("🚀 Server startup: Cleaning up orphaned 'running' tasks...")
    try:
        db_provider = DatabaseEngineProvider()
        db_provider.ensure_initialized()
        SessionLocal = db_provider.get_session_factory()
        with SessionLocal() as session:
            repo = TefasRepository(session)
            
            # Find all tasks with 'running' status
            orphaned_count = repo.cleanup_orphaned_running_tasks()
            
            if orphaned_count > 0:
                logger.info(f"✅ Cleaned up {orphaned_count} orphaned 'running' tasks")
            else:
                logger.info("✅ No orphaned 'running' tasks found")
    except Exception as e:
        logger.error(f"❌ Failed to clean up orphaned tasks on startup: {e}")
    
    startup_cleanup_done = True

@app.get("/")
async def root():
    return {"message": "Finance Tools API is running"}


@app.get("/api/database/stats")
async def get_database_stats(session = Depends(get_db_session)):
    """Get database statistics."""
    try:
        repo = TefasRepository(session)
        
        # Get total records count
        total_records = repo.get_total_records_count()
        
        # Get unique funds count
        fund_count = repo.get_unique_funds_count()
        
        # Get date range
        date_range = repo.get_date_range()
        
        # Get last download date (from most recent record date)
        last_download = repo.get_last_download_date()
        
        return {
            "totalRecords": total_records,
            "fundCount": fund_count,
            "dateRange": {
                "start": date_range["start"].isoformat() if date_range["start"] else None,
                "end": date_range["end"].isoformat() if date_range["end"] else None,
            },
            "lastDownloadDate": last_download.isoformat() if last_download else None,
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/database/download")
async def download_data(request: dict):
    """Initiate data download from TEFAS."""
    global download_progress, active_tasks
    import uuid
    
    # Check if there's a stuck download (running for more than 30 minutes)
    if download_progress["is_downloading"]:
        start_time = download_progress.get("start_time")
        if start_time:
            from datetime import datetime as dt, timedelta
            start_dt = dt.fromisoformat(start_time)
            if dt.now() - start_dt > timedelta(minutes=30):
                # Reset stuck download
                with progress_lock:
                    download_progress = {
                        "is_downloading": False,
                        "progress": 0,
                        "status": "Ready",
                        "records_downloaded": 0,
                        "total_records": 0,
                        "start_time": None,
                        "estimated_completion": None,
                        "current_phase": "ready",
                        "task_id": None,
                        "error": "Previous download timed out and was reset",
                    }
                # Clean up stuck tasks
                cleanup_completed_tasks()
            else:
                raise HTTPException(status_code=400, detail="Download already in progress")
        else:
            raise HTTPException(status_code=400, detail="Download already in progress")
    
    try:
        start_date = request.get("startDate")
        end_date = request.get("endDate")
        funds = request.get("funds", [])  # Optional fund codes
        kind = request.get("kind", "BYF")  # Fund type: YAT, EMK, or BYF
        
        if not start_date or not end_date:
            raise HTTPException(status_code=400, detail="startDate and endDate are required")
        
        if kind not in ["YAT", "EMK", "BYF"]:
            raise HTTPException(status_code=400, detail="kind must be one of: YAT, EMK, BYF")
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        with progress_lock:
            download_progress = {
                "is_downloading": True,
                "progress": 0,
                "status": "Starting download...",
                "records_downloaded": 0,
                "total_records": 0,
                "start_time": datetime.now().isoformat(),
                "estimated_completion": None,
                "current_phase": "initializing",
                "task_id": task_id,
                "error": None,
            }
        
        # Create cancellation flag for this task
        cancellation_flags[task_id] = {"cancelled": False}
        
        # Run download in background thread
        logger.info(f"🚀 Submitting download task to thread pool - Task ID: {task_id}")
        future = executor.submit(run_download_sync, start_date, end_date, funds, kind, task_id)
        
        # Store task reference
        active_tasks[task_id] = {
            "future": future,
            "start_time": datetime.now(),
            "start_date": start_date,
            "end_date": end_date,
            "funds": funds,
            "kind": kind,
        }
        
        logger.info(f"📋 Task stored in active_tasks - Task ID: {task_id}, Active tasks count: {len(active_tasks)}")
        logger.info(f"📊 Download progress state after task creation: {download_progress}")
        
        # Download history record will be created in the background thread
        
        return {"message": "Download started", "task_id": task_id}
    except Exception as e:
        with progress_lock:
            download_progress = {
                "is_downloading": False,
                "progress": 0,
                "status": f"Download failed: {str(e)}",
                "error": str(e),
            }
        logger.error(f"Error starting download: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Thread lock for safe access to global progress state
progress_lock = threading.Lock()

def progress_callback(status: str, progress: int, current_chunk: int):
    """Progress callback function that updates the global progress state."""
    global download_progress
    logger.info(f"🔄 PROGRESS CALLBACK - Status: {status}, Progress: {progress}%, Chunk: {current_chunk}")
    logger.info(f"🔄 PROGRESS CALLBACK - Current is_downloading: {download_progress.get('is_downloading', False)}")
    with progress_lock:
        now = datetime.now()
        now_iso = now.isoformat()
        
        # Initialize detailed progress fields
        if "detailed_messages" not in download_progress:
            download_progress["detailed_messages"] = []
        if "current_chunk_info" not in download_progress:
            download_progress["current_chunk_info"] = {}
        if "fund_progress" not in download_progress:
            download_progress["fund_progress"] = {}
        if "total_chunks" not in download_progress:
            download_progress["total_chunks"] = 0
        
        # Parse status message to extract detailed information
        chunk_info = {}
        fund_data = {}
        
        # Extract chunk information from status messages
        if "Fetching data from" in status and "to" in status:
            # Extract date range and total chunks from status like "Fetching data from 2024-01-01 to 2024-01-05 [Total chunks: 12]"
            import re
            date_match = re.search(r'from (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})', status)
            # Extract total chunks if present
            total_chunks_match = re.search(r'\[Total chunks: (\d+)\]', status)
            
            if date_match:
                # Update total_chunks if found in message
                if total_chunks_match:
                    download_progress["total_chunks"] = int(total_chunks_match.group(1))
                
                chunk_info = {
                    "start_date": date_match.group(1),
                    "end_date": date_match.group(2),
                    "chunk_number": current_chunk,
                    "total_chunks": download_progress.get("total_chunks", 0)
                }
        elif "using" in status and "chunk" in status and "chunks" in status:
            # Extract total chunks from status like "Fetching specific funds - using 30-day chunks"
            # We can estimate total chunks based on the chunk size mentioned
            import re
            chunk_size_match = re.search(r'using (\d+)-day chunks', status)
            if chunk_size_match:
                chunk_size = int(chunk_size_match.group(1))
                # This is an estimation - we'll update it as we get more information
                if download_progress.get("total_chunks", 0) == 0:
                    # Rough estimation based on typical date ranges
                    download_progress["total_chunks"] = max(1, current_chunk * 2)
        
        # Extract fund-specific data from status messages
        if "✅ Fetched data for" in status and "rows" in status:
            # Extract fund name and row count from messages like "✅ Fetched data for FUND_NAME: 150 rows"
            import re
            fund_match = re.search(r'✅ Fetched data for ([^:]+): (\d+) rows', status)
            if fund_match:
                fund_name = fund_match.group(1).strip()
                row_count = int(fund_match.group(2))
                
                # Get current chunk info to include date range
                current_chunk_info = download_progress.get("current_chunk_info", {})
                start_date = current_chunk_info.get("start_date", "unknown")
                end_date = current_chunk_info.get("end_date", "unknown")
                
                # Create enhanced message with date range
                enhanced_message = f"✅ Fetched {row_count} rows for {fund_name} (date range: {start_date} to {end_date})"
                
                fund_data[fund_name] = {
                    "status": "success",
                    "rows": row_count,
                    "timestamp": now_iso,
                    "date_range": f"{start_date} to {end_date}",
                    "enhanced_message": enhanced_message
                }
                # Update total records downloaded
                old_count = download_progress.get("records_downloaded", 0)
                download_progress["records_downloaded"] = old_count + row_count
                logger.info(f"📊 Updated records_downloaded: {old_count} + {row_count} = {download_progress['records_downloaded']}")
                
                # Update the status message to include date range
                status = enhanced_message
        elif "⚠️ No data found for" in status:
            # Extract fund name from warning messages
            import re
            fund_match = re.search(r'⚠️ No data found for ([^"]+)', status)
            if fund_match:
                fund_name = fund_match.group(1).strip()
                
                # Get current chunk info to include date range
                current_chunk_info = download_progress.get("current_chunk_info", {})
                start_date = current_chunk_info.get("start_date", "unknown")
                end_date = current_chunk_info.get("end_date", "unknown")
                
                # Create enhanced message with date range
                enhanced_message = f"⚠️ No data found for {fund_name} (date range: {start_date} to {end_date})"
                
                fund_data[fund_name] = {
                    "status": "no_data",
                    "rows": 0,
                    "timestamp": now_iso,
                    "date_range": f"{start_date} to {end_date}",
                    "enhanced_message": enhanced_message
                }
                
                # Update the status message to include date range
                status = enhanced_message
        elif "❌ Error fetching data for" in status:
            # Extract fund name and error from error messages
            import re
            error_match = re.search(r'❌ Error fetching data for ([^:]+): (.+)', status)
            if error_match:
                fund_name = error_match.group(1).strip()
                error_msg = error_match.group(2).strip()
                
                # Get current chunk info to include date range
                current_chunk_info = download_progress.get("current_chunk_info", {})
                start_date = current_chunk_info.get("start_date", "unknown")
                end_date = current_chunk_info.get("end_date", "unknown")
                
                # Create enhanced message with date range
                enhanced_message = f"❌ Error fetching data for {fund_name} (date range: {start_date} to {end_date}): {error_msg}"
                
                fund_data[fund_name] = {
                    "status": "error",
                    "rows": 0,
                    "error": error_msg,
                    "timestamp": now_iso,
                    "date_range": f"{start_date} to {end_date}",
                    "enhanced_message": enhanced_message
                }
                
                # Update the status message to include date range
                status = enhanced_message
        elif "✅ Fetched data:" in status and "rows" in status:
            # For all funds download
            import re
            all_funds_match = re.search(r'✅ Fetched data: (\d+) rows', status)
            if all_funds_match:
                row_count = int(all_funds_match.group(1))
                
                # Get current chunk info to include date range
                current_chunk_info = download_progress.get("current_chunk_info", {})
                start_date = current_chunk_info.get("start_date", "unknown")
                end_date = current_chunk_info.get("end_date", "unknown")
                
                # Create enhanced message with date range
                enhanced_message = f"✅ Fetched {row_count} rows for all funds (date range: {start_date} to {end_date})"
                
                fund_data["all_funds"] = {
                    "status": "success",
                    "rows": row_count,
                    "timestamp": now_iso,
                    "date_range": f"{start_date} to {end_date}",
                    "enhanced_message": enhanced_message
                }
                # Update total records downloaded
                old_count = download_progress.get("records_downloaded", 0)
                download_progress["records_downloaded"] = old_count + row_count
                logger.info(f"📊 Updated records_downloaded (all funds): {old_count} + {row_count} = {download_progress['records_downloaded']}")
                
                # Update the status message to include date range
                status = enhanced_message
        elif "✅ Download completed!" in status and "Total records:" in status:
            # Extract total records from completion message
            import re
            completion_match = re.search(r'Total records: (\d+)', status)
            if completion_match:
                total_records = int(completion_match.group(1))
                download_progress["total_records"] = total_records
                download_progress["records_downloaded"] = total_records
        
        # Determine message type based on content
        message_type = "info"
        if "✅" in status:
            message_type = "success"
        elif "⚠️" in status:
            message_type = "warning"
        elif "❌" in status:
            message_type = "error"
        elif "Fetching data from" in status:
            message_type = "info"
        
        # Add to detailed messages log (keep last 50 messages)
        download_progress["detailed_messages"].append({
            "timestamp": now_iso,
            "message": status,
            "progress": progress,
            "chunk": current_chunk,
            "type": message_type
        })
        
        # Keep only last 50 messages
        if len(download_progress["detailed_messages"]) > 50:
            download_progress["detailed_messages"] = download_progress["detailed_messages"][-50:]
        
        # Store progress log in database
        try:
            from finance_tools.etfs.tefas.repository import TefasRepository, DatabaseEngineProvider
            db_provider = DatabaseEngineProvider()
            db_provider.ensure_initialized()
            with db_provider.get_session_factory()() as session:
                repo = TefasRepository(session)
                
                # Extract fund name and records count from enhanced message
                fund_name = None
                records_count = None
                
                # Use the enhanced message for better parsing
                if "✅ Fetched" in status and "rows" in status and "date range:" in status:
                    import re
                    # Parse enhanced message: "✅ Fetched 150 rows for FUND_NAME (date range: 2025-01-01 to 2025-01-05)"
                    enhanced_match = re.search(r'✅ Fetched (\d+) rows for ([^(]+) \(date range: ([^)]+)\)', status)
                    if enhanced_match:
                        records_count = int(enhanced_match.group(1))
                        fund_name = enhanced_match.group(2).strip()
                    else:
                        # Fallback to original parsing
                        fund_match = re.search(r'✅ Fetched data for ([^:]+): (\d+) rows', status)
                        if fund_match:
                            fund_name = fund_match.group(1).strip()
                            records_count = int(fund_match.group(2))
                elif "✅ Fetched" in status and "all funds" in status and "date range:" in status:
                    import re
                    # Parse enhanced message: "✅ Fetched 150 rows for all funds (date range: 2025-01-01 to 2025-01-05)"
                    enhanced_match = re.search(r'✅ Fetched (\d+) rows for all funds \(date range: ([^)]+)\)', status)
                    if enhanced_match:
                        records_count = int(enhanced_match.group(1))
                        fund_name = "all_funds"
                    else:
                        # Fallback to original parsing
                        all_funds_match = re.search(r'✅ Fetched data: (\d+) rows', status)
                        if all_funds_match:
                            records_count = int(all_funds_match.group(1))
                            fund_name = "all_funds"
                elif "⚠️ No data found for" in status and "date range:" in status:
                    import re
                    # Parse enhanced message: "⚠️ No data found for FUND_NAME (date range: 2025-01-01 to 2025-01-05)"
                    enhanced_match = re.search(r'⚠️ No data found for ([^(]+) \(date range: ([^)]+)\)', status)
                    if enhanced_match:
                        fund_name = enhanced_match.group(1).strip()
                    else:
                        # Fallback to original parsing
                        fund_match = re.search(r'⚠️ No data found for ([^"]+)', status)
                        if fund_match:
                            fund_name = fund_match.group(1).strip()
                elif "❌ Error fetching data for" in status and "date range:" in status:
                    import re
                    # Parse enhanced message: "❌ Error fetching data for FUND_NAME (date range: 2025-01-01 to 2025-01-05): error details"
                    enhanced_match = re.search(r'❌ Error fetching data for ([^(]+) \(date range: ([^)]+)\): (.+)', status)
                    if enhanced_match:
                        fund_name = enhanced_match.group(1).strip()
                    else:
                        # Fallback to original parsing
                        error_match = re.search(r'❌ Error fetching data for ([^:]+): (.+)', status)
                        if error_match:
                            fund_name = error_match.group(1).strip()
                
                repo.create_progress_log_entry(
                    task_id=download_progress.get("task_id", "unknown"),
                    timestamp=now,
                    message=status,
                    message_type=message_type,
                    progress_percent=progress,
                    chunk_number=current_chunk,
                    records_count=records_count,
                    fund_name=fund_name
                )
        except Exception as e:
            logger.error(f"❌ Failed to store progress log: {e}")
        
        # Update chunk info
        if chunk_info:
            download_progress["current_chunk_info"] = chunk_info
        
        # Update fund progress
        if fund_data:
            download_progress["fund_progress"].update(fund_data)
        
        # Add to progress history (keep last 5 minutes)
        if "progress_history" not in download_progress:
            download_progress["progress_history"] = []
        
        download_progress["progress_history"].append({
            "timestamp": now_iso,
            "progress": progress,
            "records_downloaded": download_progress.get("records_downloaded", 0)
        })
        
        # Keep only last 5 minutes of history
        cutoff_time = now - timedelta(minutes=5)
        download_progress["progress_history"] = [
            entry for entry in download_progress["progress_history"]
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]
        
        # Initialize new fields if they don't exist
        if "records_per_minute" not in download_progress:
            download_progress["records_per_minute"] = 0
        if "estimated_remaining_minutes" not in download_progress:
            download_progress["estimated_remaining_minutes"] = None
        
        # Calculate records per minute from recent history
        if len(download_progress["progress_history"]) >= 2:
            recent_entries = download_progress["progress_history"][-5:]  # Last 5 entries
            if len(recent_entries) >= 2:
                time_diff = (datetime.fromisoformat(recent_entries[-1]["timestamp"]) - 
                           datetime.fromisoformat(recent_entries[0]["timestamp"])).total_seconds() / 60
                records_diff = recent_entries[-1]["records_downloaded"] - recent_entries[0]["records_downloaded"]
                if time_diff > 0:
                    download_progress["records_per_minute"] = records_diff / time_diff
                else:
                    download_progress["records_per_minute"] = 0
        
        # Calculate estimated remaining time
        if download_progress["records_per_minute"] > 0 and download_progress["total_records"] > 0:
            remaining_records = download_progress["total_records"] - download_progress.get("records_downloaded", 0)
            download_progress["estimated_remaining_minutes"] = remaining_records / download_progress["records_per_minute"]
        
        download_progress.update({
            "status": status,
            "progress": progress,
            "current_phase": "downloading",
            "last_activity": now_iso,
        })

def cleanup_completed_tasks():
    """Clean up completed tasks from active_tasks."""
    global active_tasks, cancellation_flags
    completed_tasks = []
    
    for task_id, task_info in active_tasks.items():
        if task_info["future"].done():
            completed_tasks.append(task_id)
            logger.info(f"🧹 Task {task_id} is completed, marking for cleanup")
    
    for task_id in completed_tasks:
        del active_tasks[task_id]
        if task_id in cancellation_flags:
            del cancellation_flags[task_id]
        logger.info(f"🧹 Cleaned up completed task {task_id}, remaining active tasks: {len(active_tasks)}")

def is_task_cancelled(task_id: str) -> bool:
    """Check if a task has been cancelled."""
    return task_id in cancellation_flags and cancellation_flags[task_id]["cancelled"]

def run_download_sync(start_date: str, end_date: str, funds: list = None, kind: str = "BYF", task_id: str = None):
    """Synchronous version of download process for thread execution."""
    global download_progress, active_tasks, cancellation_flags
    
    if task_id is None:
        task_id = download_progress.get("task_id", "unknown")
    
    logger.info(f"🚀 DOWNLOAD TASK STARTED - Task ID: {task_id}, Date Range: {start_date} to {end_date}, Kind: {kind}, Funds: {funds or 'All'}")
    
    # Check if task was cancelled before starting
    if is_task_cancelled(task_id):
        logger.info(f"❌ Task {task_id} was cancelled before starting")
        return
    
    try:
        # Create download history record at the start
        try:
            from finance_tools.etfs.tefas.repository import TefasRepository, DatabaseEngineProvider
            from datetime import date
            db_provider = DatabaseEngineProvider()
            db_provider.ensure_initialized()
            with db_provider.get_session_factory()() as session:
                repo = TefasRepository(session)
                repo.create_download_record(
                    task_id=task_id,
                    start_date=date.fromisoformat(start_date),
                    end_date=date.fromisoformat(end_date),
                    kind=kind,
                    funds=funds or []
                )
            logger.info(f"📝 Download history record created for Task ID: {task_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create download history record for Task ID {task_id}: {e}")
        
        # Initialize service with progress callback
        service = TefasPersistenceService(progress_callback=progress_callback)
        
        # Phase 1: Download data using the service
        logger.info(f"📊 Starting data download for Task ID: {task_id}")
        with progress_lock:
            download_progress.update({
                "is_downloading": True,
                "status": f"Starting download of {kind} fund data from {start_date} to {end_date}...",
                "progress": 0,
                "current_phase": "downloading",
                "records_downloaded": 0,
            })
        
        # Check for cancellation before starting download
        if is_task_cancelled(task_id):
            logger.info(f"❌ Task {task_id} was cancelled before download")
            return
        
        # Use the same method as CLI
        logger.info(f"🔄 Executing download_and_persist for Task ID: {task_id}")
        info_count, breakdown_count = service.download_and_persist(
            start_date=start_date,
            end_date=end_date,
            funds=funds if funds else None,
            kind=kind,
        )
        
        # Check for cancellation after download
        if is_task_cancelled(task_id):
            logger.info(f"❌ Task {task_id} was cancelled after download")
            return
        
        total_records = info_count + breakdown_count
        logger.info(f"📈 Download completed for Task ID: {task_id} - Info records: {info_count}, Breakdown records: {breakdown_count}, Total: {total_records}")
        
        # Update progress with actual counts
        with progress_lock:
            logger.info(f"🔄 Setting is_downloading to False due to successful completion for task {task_id}")
            download_progress.update({
                "total_records": total_records,
                "progress": 100,
                "status": f"Download completed successfully! {total_records} total records saved ({info_count} info, {breakdown_count} breakdown).",
                "current_phase": "completed",
                "records_downloaded": total_records,
                "is_downloading": False,
            })
        
        # Update download history record
        try:
            from finance_tools.etfs.tefas.repository import TefasRepository, DatabaseEngineProvider
            db_provider = DatabaseEngineProvider()
            db_provider.ensure_initialized()
            with db_provider.get_session_factory()() as session:
                repo = TefasRepository(session)
                repo.update_download_record(
                    task_id=task_id,
                    status="completed",
                    records_downloaded=total_records,
                    total_records=total_records
                )
            logger.info(f"✅ Download history updated successfully for Task ID: {task_id}")
        except Exception as e:
            logger.error(f"❌ Failed to update download history record for Task ID {task_id}: {e}")
        
        logger.info(f"🎉 DOWNLOAD TASK COMPLETED SUCCESSFULLY - Task ID: {task_id}, Total Records: {total_records}")
        
    except Exception as e:
        logger.error(f"💥 DOWNLOAD TASK FAILED - Task ID: {task_id}, Error: {str(e)}")
        with progress_lock:
            logger.info(f"🔄 Setting is_downloading to False due to error for task {task_id}")
            download_progress.update({
                "is_downloading": False,
                "progress": 0,
                "status": f"Download failed: {str(e)}",
                "current_phase": "error",
                "records_downloaded": 0,
                "total_records": 0,
                "error": str(e),
            })
        
        # Update download history record with error
        try:
            from finance_tools.etfs.tefas.repository import TefasRepository, DatabaseEngineProvider
            db_provider = DatabaseEngineProvider()
            db_provider.ensure_initialized()
            with db_provider.get_session_factory()() as session:
                repo = TefasRepository(session)
                repo.update_download_record(
                    task_id=task_id,
                    status="failed",
                    records_downloaded=0,
                    total_records=0,
                    error_message=str(e)
                )
            logger.info(f"📝 Download history updated with error for Task ID: {task_id}")
        except Exception as history_error:
            logger.error(f"❌ Failed to update download history record with error for Task ID {task_id}: {history_error}")
        
        logger.error(f"❌ DOWNLOAD TASK FAILED - Task ID: {task_id}, Error: {e}")
    finally:
        # Clean up completed tasks
        cleanup_completed_tasks()

async def run_download(start_date: str, end_date: str, funds: list = None, kind: str = "BYF"):
    """Legacy async function - kept for compatibility but not used."""
    # This function is no longer used but kept for compatibility
    pass

@app.get("/api/database/download-progress")
async def get_download_progress():
    """Get current download progress."""
    with progress_lock:
        # Clean up completed tasks before returning status
        cleanup_completed_tasks()
        logger.info(f"📊 API - get_download_progress returning records_downloaded: {download_progress.get('records_downloaded', 0)}")
        logger.info(f"📊 API - get_download_progress returning total_records: {download_progress.get('total_records', 0)}")
        return download_progress.copy()

@app.get("/api/database/tasks")
async def get_active_tasks(session = Depends(get_db_session)):
    """Get list of active download tasks from both memory and database."""
    with progress_lock:
        cleanup_completed_tasks()
        
        # Get tasks from memory
        memory_tasks = {
            task_id: {
                "task_id": task_id,
                "start_time": task_info["start_time"].isoformat(),
                "start_date": task_info["start_date"],
                "end_date": task_info["end_date"],
                "funds": task_info["funds"],
                "kind": task_info["kind"],
                "status": "running" if not task_info["future"].done() else "completed",
                "duration_seconds": (datetime.now() - task_info["start_time"]).total_seconds(),
                "is_stuck": (datetime.now() - task_info["start_time"]).total_seconds() > 1800,  # 30 minutes
                "source": "memory"
            }
            for task_id, task_info in active_tasks.items()
        }
        
        # Get running tasks from database
        try:
            from finance_tools.etfs.tefas.models import DownloadHistory
            repo = TefasRepository(session)
            
            db_running_tasks = session.query(DownloadHistory)\
                .filter(DownloadHistory.status == 'running')\
                .all()
            
            for db_task in db_running_tasks:
                # Only add if not already in memory tasks
                if db_task.task_id not in memory_tasks:
                    duration_seconds = (datetime.now() - db_task.start_time).total_seconds()
                    memory_tasks[db_task.task_id] = {
                        "task_id": db_task.task_id,
                        "start_time": db_task.start_time.isoformat(),
                        "start_date": db_task.start_date.isoformat(),
                        "end_date": db_task.end_date.isoformat(),
                        "funds": db_task.funds or [],
                        "kind": db_task.kind,
                        "status": "running",
                        "duration_seconds": duration_seconds,
                        "is_stuck": duration_seconds > 1800,  # 30 minutes
                        "source": "database"
                    }
        except Exception as e:
            logger.error(f"❌ Failed to fetch running tasks from database: {e}")
        
        result = {
            "active_tasks": len(memory_tasks),
            "tasks": list(memory_tasks.values())
        }
        logger.info(f"📊 API - get_active_tasks returning: {len(result['tasks'])} tasks ({len([t for t in result['tasks'] if t['source'] == 'memory'])} from memory, {len([t for t in result['tasks'] if t['source'] == 'database'])} from database)")
        return result

@app.post("/api/database/cancel-task/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a specific download task."""
    global download_progress, active_tasks, cancellation_flags
    
    with progress_lock:
        if task_id not in active_tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Set cancellation flag
        if task_id in cancellation_flags:
            cancellation_flags[task_id]["cancelled"] = True
            logger.info(f"🚫 Cancellation flag set for task {task_id}")
        
        # Try to cancel the future (this only works if task hasn't started)
        task_info = active_tasks[task_id]
        future = task_info["future"]
        cancelled = future.cancel()
        
        if cancelled:
            # Task was cancelled before starting
            del active_tasks[task_id]
            if task_id in cancellation_flags:
                del cancellation_flags[task_id]
            logger.info(f"✅ Task {task_id} cancelled before starting")
        else:
            # Task is already running, but we've set the cancellation flag
            logger.info(f"🚫 Task {task_id} is running but cancellation flag set")
        
        # Reset download progress if this was the current task
        if download_progress.get("task_id") == task_id:
            download_progress = {
                "is_downloading": False,
                "progress": 0,
                "status": "Task cancelled by user",
                "records_downloaded": 0,
                "total_records": 0,
                "start_time": None,
                "estimated_completion": None,
                "current_phase": "cancelled",
                "task_id": None,
                "error": None,
            }
        
        # Update database record
        try:
            from finance_tools.etfs.tefas.repository import TefasRepository, DatabaseEngineProvider
            db_provider = DatabaseEngineProvider()
            db_provider.ensure_initialized()
            with db_provider.get_session_factory()() as session:
                repo = TefasRepository(session)
                repo.update_download_record(
                    task_id=task_id,
                    status="cancelled",
                    records_downloaded=0,
                    total_records=0,
                    error_message="Cancelled by user"
                )
            logger.info(f"✅ Database updated for cancelled task {task_id}")
        except Exception as e:
            logger.error(f"❌ Failed to update database for cancelled task {task_id}: {e}")
        
        return {"message": "Task cancellation requested", "task_id": task_id}

@app.get("/api/data/records")
async def get_records(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=1000),
    search: str = Query(""),
    sortBy: Optional[str] = Query(None),
    sortDir: Optional[str] = Query("asc"),
    filters: List[str] = Query([]),
    session = Depends(get_db_session)
):
    """Get paginated records with filtering and sorting."""
    try:
        repo = TefasRepository(session)
        
        # Parse filters
        filter_conditions = []
        for i in range(0, len(filters), 4):
            if i + 3 < len(filters):
                column = filters[i]
                operator = filters[i + 1]
                value = filters[i + 2]
                value2 = filters[i + 3] if i + 3 < len(filters) else None
                filter_conditions.append({
                    "column": column,
                    "operator": operator,
                    "value": value,
                    "value2": value2
                })
        
        # Get records
        records, total = repo.get_paginated_records(
            page=page,
            page_size=pageSize,
            search=search,
            sort_by=sortBy,
            sort_dir=sortDir,
            filters=filter_conditions
        )
        
        # Convert to list of dicts
        records_list = []
        for record in records:
            records_list.append({
                "id": record.id,
                "code": record.code,
                "title": record.title,
                "date": record.date.isoformat() if record.date else None,
                "price": float(record.price) if record.price else None,
                "market_cap": float(record.market_cap) if record.market_cap else None,
                "number_of_investors": int(record.number_of_investors) if record.number_of_investors else None,
                "number_of_shares": float(record.number_of_shares) if record.number_of_shares else None,
            })
        
        total_pages = (total + pageSize - 1) // pageSize
        
        return {
            "data": records_list,
            "total": total,
            "page": page,
            "pageSize": pageSize,
            "totalPages": total_pages,
        }
    except Exception as e:
        logger.error(f"Error getting records: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/columns")
async def get_columns(session = Depends(get_db_session)):
    """Get available column names."""
    return [
        "id",
        "code", 
        "title",
        "date",
        "price",
        "market_cap",
        "number_of_investors",
        "number_of_shares"
    ]

@app.get("/api/data/funds")
async def get_funds(session = Depends(get_db_session)):
    """Get list of unique funds."""
    try:
        repo = TefasRepository(session)
        funds = repo.get_unique_funds()
        return funds
    except Exception as e:
        logger.error(f"Error getting funds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/plot")
async def get_plot_data(
    xColumn: str = Query(...),
    yColumn: str = Query(...),
    fundCode: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    filters: List[str] = Query([]),
    session = Depends(get_db_session)
):
    """Get data for plotting."""
    try:
        repo = TefasRepository(session)
        
        # Parse filters
        filter_conditions = []
        for i in range(0, len(filters), 4):
            if i + 3 < len(filters):
                column = filters[i]
                operator = filters[i + 1]
                value = filters[i + 2]
                value2 = filters[i + 3] if i + 3 < len(filters) else None
                filter_conditions.append({
                    "column": column,
                    "operator": operator,
                    "value": value,
                    "value2": value2
                })
        
        # Add fund filter if specified
        if fundCode:
            filter_conditions.append({
                "column": "code",
                "operator": "equals",
                "value": fundCode
            })
        
        # Add date range filters if specified
        if startDate:
            filter_conditions.append({
                "column": "date",
                "operator": "greater_than_or_equal",
                "value": startDate
            })
        
        if endDate:
            filter_conditions.append({
                "column": "date",
                "operator": "less_than_or_equal",
                "value": endDate
            })
        
        # Get plot data
        plot_data = repo.get_plot_data(
            x_column=xColumn,
            y_column=yColumn,
            filters=filter_conditions
        )
        
        return plot_data
    except Exception as e:
        logger.error(f"Error getting plot data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/database/download-history")
async def get_download_history(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=100),
    search: str = Query(""),
    status: Optional[str] = Query(None),
    session = Depends(get_db_session)
):
    """
    Get unified download history with pagination and filtering.
    Returns both TEFAS and Stock downloads from shared table.
    """
    try:
        repo = TefasRepository(session)
        downloads, total = repo.get_download_history(
            page=page,
            page_size=pageSize,
            search=search,
            status_filter=status
        )
        
        return {
            "downloads": [
                {
                    "id": d.id,
                    "task_id": d.task_id,
                    "data_type": getattr(d, 'data_type', 'tefas'),  # New: data type field
                    "start_date": d.start_date.isoformat(),
                    "end_date": d.end_date.isoformat(),
                    "kind": d.kind,
                    "funds": d.funds if (d.funds and d.funds != "null") else [],  # Handle JSON null
                    "symbols": getattr(d, 'symbols', None) if (getattr(d, 'symbols', None) and getattr(d, 'symbols', None) != "null") else [],  # Handle JSON null
                    "status": d.status,
                    "start_time": d.start_time.isoformat(),
                    "end_time": d.end_time.isoformat() if d.end_time else None,
                    "records_downloaded": d.records_downloaded,
                    "total_records": d.total_records,
                    "items_completed": getattr(d, 'items_completed', 0),  # New: Generic counter
                    "items_failed": getattr(d, 'items_failed', 0),  # New: Generic counter
                    "error_message": d.error_message,
                }
                for d in downloads
            ],
            "total": total,
            "page": page,
            "pageSize": pageSize
        }
    except Exception as e:
        logger.error(f"Error getting download history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/database/download-statistics")
async def get_download_statistics(session = Depends(get_db_session)):
    """Get download statistics."""
    try:
        repo = TefasRepository(session)
        stats = repo.get_download_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting download statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/database/download-task-details/{task_id}")
async def get_download_task_details(task_id: str, session = Depends(get_db_session)):
    """Get detailed information about a specific download task."""
    try:
        repo = TefasRepository(session)
        details = repo.get_download_task_details(task_id)
        if not details:
            raise HTTPException(status_code=404, detail="Download task not found")
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting download task details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/database/data-distribution")
async def get_data_distribution(
    groupBy: str = Query("monthly", regex="^(daily|monthly|yearly)$"),
    session = Depends(get_db_session)
):
    """Get data distribution for charts."""
    try:
        repo = TefasRepository(session)
        distribution = repo.get_data_distribution(group_by=groupBy)
        return {"distribution": distribution}
    except Exception as e:
        logger.error(f"Error getting data distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/database/fund-type-distribution")
async def get_fund_type_distribution(session = Depends(get_db_session)):
    """Get fund type distribution for pie charts."""
    try:
        repo = TefasRepository(session)
        distribution = repo.get_fund_type_distribution()
        return {"distribution": distribution}
    except Exception as e:
        logger.error(f"Error getting fund type distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STOCK DATA ENDPOINTS
# ============================================================================

# Global state for stock downloads
stock_download_progress = {
    "is_downloading": False,
    "progress": 0,
    "status": "",
    "records_downloaded": 0,
    "total_records": 0,
    "start_time": None,
    "estimated_completion": None,
    "current_phase": "",
    "task_id": None,
    "error": None,
    "symbols_completed": 0,
    "symbols_total": 0,
}

stock_progress_lock = threading.Lock()
stock_active_tasks = {}
stock_cancellation_flags = {}


def stock_progress_callback(status: str, progress: int, current_symbol: int):
    """
    Progress callback for stock downloads.
    Updates both in-memory state and saves progress logs to database.
    """
    global stock_download_progress
    logger.info(f"🔄 STOCK PROGRESS - Status: {status}, Progress: {progress}%, Symbol: {current_symbol}")

    with stock_progress_lock:
        now = datetime.now()

        # Extract record count if present
        import re
        records_count = None
        symbol_name = None

        # Extract record count from success messages
        if "Downloaded" in status and "records" in status:
            logger.info(f"📊 STOCK PROGRESS - Processing download message: '{status}'")
            # Pattern to match "✅ Downloaded AAPL: 150 records" or "✅ Downloaded SYMBOL: NUMBER records"
            records_match = re.search(r'Downloaded\s+[A-Z]+:\s*(\d+)\s+records', status)
            if records_match:
                count = int(records_match.group(1))
                records_count = count
                old_count = stock_download_progress.get("records_downloaded", 0)
                stock_download_progress["records_downloaded"] = old_count + count
                logger.info(f"📊 STOCK PROGRESS - Updated records_downloaded: {old_count} + {count} = {stock_download_progress['records_downloaded']}")
            else:
                # Fallback pattern for different message formats
                fallback_match = re.search(r'Downloaded.*?(\d+)\s+records', status)
                if fallback_match:
                    count = int(fallback_match.group(1))
                    records_count = count
                    old_count = stock_download_progress.get("records_downloaded", 0)
                    stock_download_progress["records_downloaded"] = old_count + count
                    logger.info(f"📊 STOCK PROGRESS - Fallback: Updated records_downloaded: {old_count} + {count} = {stock_download_progress['records_downloaded']}")
                else:
                    # Debug: Log the status message if no pattern matches
                    logger.warning(f"📊 STOCK PROGRESS - Could not parse record count from status: '{status}'")

        # Extract symbol name from status messages
        if "Downloading" in status or "Downloaded" in status:
            # Extract symbol like "📊 Downloading AAPL (1/3)..." or "✅ Downloaded AAPL: 250 records"
            symbol_match = re.search(r'(?:Downloading|Downloaded)\s+([A-Z]+)', status)
            if symbol_match:
                symbol_name = symbol_match.group(1)

        # Update in-memory progress state
        stock_download_progress.update({
            "status": status,
            "progress": progress,
            "current_phase": "downloading" if progress < 90 else "saving",
            "last_activity": now.isoformat(),
        })

        # Debug: Log current state
        logger.info(f"📊 STOCK PROGRESS - Current state: records_downloaded={stock_download_progress.get('records_downloaded', 0)}, progress={stock_download_progress.get('progress', 0)}%")
        
        # Determine message type
        message_type = "info"
        if "✅" in status or "completed" in status.lower():
            message_type = "success"
        elif "⚠️" in status or "warning" in status.lower() or "No data" in status:
            message_type = "warning"
        elif "❌" in status or "error" in status.lower() or "Error" in status:
            message_type = "error"
        
        # Save progress log to database
        task_id = stock_download_progress.get("task_id")
        if task_id:
            try:
                db_provider = DatabaseEngineProvider()
                with db_provider.get_session_factory()() as session:
                    repo = StockRepository(session)
                    repo.create_progress_log_entry(
                        task_id=task_id,
                        timestamp=now,
                        message=status,
                        message_type=message_type,
                        progress_percent=progress,
                        symbol_number=current_symbol,
                        records_count=records_count,
                        symbol=symbol_name
                    )
                    logger.info(f"✅ Saved progress log to database for task {task_id}")
            except Exception as e:
                logger.error(f"❌ Failed to save progress log to database: {e}")


def is_stock_task_cancelled(task_id: str) -> bool:
    """Check if a stock task has been cancelled."""
    return task_id in stock_cancellation_flags and stock_cancellation_flags[task_id]["cancelled"]


def run_stock_download_sync(symbols: List[str], start_date: str, end_date: str, interval: str = '1d', task_id: str = None):
    """Synchronous function to run stock download in background thread."""
    global stock_download_progress
    
    try:
        logger.info(f"🚀 Starting stock download task {task_id}")
        
        # Create download history record
        try:
            db_provider = DatabaseEngineProvider()
            db_provider.ensure_initialized()
            with db_provider.get_session_factory()() as session:
                repo = StockRepository(session)
                from datetime import datetime as dt
                repo.create_download_record(
                    task_id=task_id,
                    symbols=symbols,
                    start_date=dt.strptime(start_date, "%Y-%m-%d").date(),
                    end_date=dt.strptime(end_date, "%Y-%m-%d").date(),
                    interval=interval
                )
            logger.info(f"✅ Created download history record for Task ID {task_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create download history record: {e}")
        
        # Initialize service with progress callback
        service = StockPersistenceService(progress_callback=stock_progress_callback)
        
        # Phase 1: Download and persist
        logger.info(f"📊 Starting stock data download for Task ID: {task_id}")
        with stock_progress_lock:
            stock_download_progress.update({
                "is_downloading": True,
                "status": f"Starting download of {len(symbols)} stocks from {start_date} to {end_date}...",
                "progress": 0,
                "current_phase": "downloading",
                "records_downloaded": 0,
                "symbols_completed": 0,
                "symbols_total": len(symbols),
            })
        
        # Check for cancellation before starting
        if is_stock_task_cancelled(task_id):
            logger.info(f"❌ Task {task_id} was cancelled before download")
            return
        
        # Execute download
        logger.info(f"🔄 Executing download_and_persist for Task ID: {task_id}")
        price_count, info_count = service.download_and_persist(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            include_info=True
        )
        
        # Check for cancellation after download
        if is_stock_task_cancelled(task_id):
            logger.info(f"❌ Task {task_id} was cancelled after download")
            return
        
        total_records = price_count + info_count
        logger.info(f"📈 Download completed - Price records: {price_count}, Info records: {info_count}")
        
        # Update progress with completion
        with stock_progress_lock:
            stock_download_progress.update({
                "total_records": total_records,
                "progress": 100,
                "status": f"Download completed! {price_count} price records, {info_count} info records saved.",
                "current_phase": "completed",
                "records_downloaded": price_count,
                "symbols_completed": len(symbols),
                "is_downloading": False,
            })
        
        # Update download history record
        try:
            db_provider = DatabaseEngineProvider()
            with db_provider.get_session_factory()() as session:
                repo = StockRepository(session)
                repo.update_download_record(
                    task_id=task_id,
                    status="completed",
                    records_downloaded=price_count,
                    total_records=total_records,
                    symbols_completed=len(symbols),
                    symbols_failed=0
                )
            logger.info(f"✅ Download history updated for Task ID: {task_id}")
        except Exception as e:
            logger.error(f"❌ Failed to update download history: {e}")
        
        logger.info(f"🎉 STOCK DOWNLOAD COMPLETED - Task ID: {task_id}")
        
    except Exception as e:
        logger.error(f"💥 STOCK DOWNLOAD FAILED - Task ID: {task_id}, Error: {str(e)}")
        with stock_progress_lock:
            stock_download_progress.update({
                "is_downloading": False,
                "progress": 0,
                "status": f"Download failed: {str(e)}",
                "current_phase": "error",
                "error": str(e),
            })
        
        # Update download history with error
        try:
            db_provider = DatabaseEngineProvider()
            with db_provider.get_session_factory()() as session:
                repo = StockRepository(session)
                repo.update_download_record(
                    task_id=task_id,
                    status="failed",
                    error_message=str(e)
                )
        except Exception as history_error:
            logger.error(f"❌ Failed to update download history: {history_error}")


@app.post("/api/stocks/download")
async def download_stock_data(request: dict):
    """
    Initiate stock data download.
    
    Body:
    {
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "startDate": "2024-01-01",
        "endDate": "2024-12-31",
        "interval": "1d"
    }
    """
    global stock_download_progress, stock_active_tasks, stock_cancellation_flags
    
    try:
        # Check if download is already in progress
        with stock_progress_lock:
            if stock_download_progress.get("is_downloading"):
                raise HTTPException(status_code=400, detail="Stock download already in progress")
        
        symbols = request.get("symbols", [])
        start_date = request.get("startDate")
        end_date = request.get("endDate")
        interval = request.get("interval", "1d")
        
        if not symbols:
            raise HTTPException(status_code=400, detail="symbols list is required")
        if not start_date or not end_date:
            raise HTTPException(status_code=400, detail="startDate and endDate are required")
        
        # Generate unique task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        with stock_progress_lock:
            stock_download_progress = {
                "is_downloading": True,
                "progress": 0,
                "status": "Starting download...",
                "records_downloaded": 0,
                "total_records": 0,
                "start_time": datetime.now().isoformat(),
                "estimated_completion": None,
                "current_phase": "initializing",
                "task_id": task_id,
                "error": None,
                "symbols_completed": 0,
                "symbols_total": len(symbols),
            }
        
        # Create cancellation flag
        stock_cancellation_flags[task_id] = {"cancelled": False}
        
        # Run download in background
        logger.info(f"🚀 Submitting stock download task - Task ID: {task_id}")
        future = executor.submit(run_stock_download_sync, symbols, start_date, end_date, interval, task_id)
        
        # Store task reference
        stock_active_tasks[task_id] = {
            "future": future,
            "start_time": datetime.now(),
            "symbols": symbols,
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval,
        }
        
        return {
            "message": "Stock download started",
            "task_id": task_id,
            "symbols": symbols,
            "interval": interval
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting stock download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks/download-progress")
async def get_stock_download_progress():
    """Get current stock download progress."""
    with stock_progress_lock:
        return stock_download_progress.copy()


@app.get("/api/stocks/stats")
async def get_stock_stats(session = Depends(get_db_session)):
    """Get statistics about stored stock data."""
    try:
        repo = StockRepository(session)
        
        total_records = repo.get_total_records_count()
        unique_symbols = repo.get_unique_symbols_count()
        date_range = repo.get_date_range()
        download_stats = repo.get_download_statistics()
        
        return {
            "totalRecords": total_records,
            "symbolCount": unique_symbols,
            "dateRange": {
                "start": date_range["start"].isoformat() if date_range["start"] else None,
                "end": date_range["end"].isoformat() if date_range["end"] else None,
            },
            "downloads": download_stats,
        }
    except Exception as e:
        logger.error(f"Error getting stock stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def cleanup_executor():
    """Cleanup function to shutdown thread pool executor."""
    global executor
    if executor:
        executor.shutdown(wait=True)

if __name__ == "__main__":
    import uvicorn
    import atexit
    
    # Register cleanup function
    atexit.register(cleanup_executor)
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8070)
    finally:
        cleanup_executor()
