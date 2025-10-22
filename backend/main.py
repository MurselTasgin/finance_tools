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
import uuid
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

# Global state for analysis task progress
analysis_progress = {
    "is_running": False,
    "progress": 0,
    "progress_percent": 0,
    "status": "",
    "progress_message": "",
    "current_step": 0,
    "total_steps": 0,
    "analysis_type": None,
    "task_id": None,
    "error": None,
    "start_time": None,
}

# Store active analysis tasks
active_analysis_tasks = {}

# Store cancellation flags for analysis tasks
analysis_cancellation_flags = {}

# Locks for thread-safe access to analysis state
analysis_progress_lock = threading.Lock()

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
                # Don't increment records_downloaded here to avoid double counting
                # The final count will be set after download completion
                logger.info(f"📊 Downloaded {row_count} rows for {fund_name} (not adding to total yet to avoid double counting)")
                
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
                # Don't increment records_downloaded here to avoid double counting
                # The final count will be set after download completion
                logger.info(f"📊 Downloaded {row_count} rows for all funds (not adding to total yet to avoid double counting)")
                
                # Update the status message to include date range
                status = enhanced_message
        elif "✅ Download completed!" in status and "Total records:" in status:
            # Extract total records from completion message
            import re
            completion_match = re.search(r'Total records: (\d+)', status)
            if completion_match:
                total_records = int(completion_match.group(1))
                download_progress["total_records"] = total_records
                # Don't set records_downloaded here - it will be set properly in run_download_sync
                logger.info(f"📊 Download completed with {total_records} total records (records_downloaded will be set properly later)")
        
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
                "records_downloaded": info_count,  # Only count info records as "downloaded records"
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
                    records_downloaded=info_count,  # Only count info records as "downloaded records"
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


# ===== ANALYTICS API ENDPOINTS =====

# Import analytics service
from finance_tools.analytics.service import AnalyticsService

# Global analytics service instance
analytics_service = AnalyticsService()

# Helper function to check if an analysis task was cancelled
def is_analysis_cancelled(task_id: str) -> bool:
    """Check if an analysis task has been cancelled."""
    return task_id in analysis_cancellation_flags and analysis_cancellation_flags[task_id]["cancelled"]


# Thread function for running analysis in background
def run_analysis_sync(analysis_type: str, analysis_name: str, parameters: dict, task_id: str, session_factory):
    """
    Synchronous function to run analysis in background thread.
    
    Supports all analysis types:
    - 'etf_technical': ETF technical analysis
    - 'etf_scan': ETF scan analysis
    - 'stock_technical': Stock technical analysis
    """
    global analysis_progress, active_analysis_tasks, analysis_progress_lock
    
    logger.info(f"🚀 ANALYSIS TASK STARTED - Task ID: {task_id}, Type: {analysis_type}")
    
    if is_analysis_cancelled(task_id):
        logger.info(f"❌ Analysis task {task_id} was cancelled before starting")
        return
    
    start_time = time.time()
    result_id = None
    
    def log_progress(message: str, progress_percent: int, message_type: str = 'info'):
        """Helper function to log progress to database and update global state"""
        try:
            from finance_tools.etfs.tefas.models import AnalysisProgressLog
            
            # Log to database
            progress_log = AnalysisProgressLog(
                task_id=task_id,
                timestamp=datetime.utcnow(),
                message=message,
                message_type=message_type,
                progress_percent=progress_percent,
            )
            session.add(progress_log)
            session.commit()
            
            # Update global progress
            with analysis_progress_lock:
                analysis_progress.update({
                    "is_running": True,
                    "progress": progress_percent,
                    "progress_percent": progress_percent,
                    "progress_message": message,
                    "analysis_type": analysis_type,
                    "task_id": task_id,
                    "start_time": datetime.now().isoformat(),
                    "error": None,
                })
            
            logger.info(f"📝 [{progress_percent}%] {message}")
        except Exception as e:
            logger.error(f"❌ Failed to log progress: {e}")
    
    try:
        session = session_factory()
        
        try:
            from finance_tools.etfs.tefas.models import AnalysisTask
            
            # Create analysis task record with enhanced parameters for ETF scan
            enhanced_parameters = parameters.copy()
            if analysis_type == 'etf_scan' and 'scanners' in parameters:
                # Add scanner details to parameters for ETF scan analysis
                enhanced_parameters.update({
                    'scanners': parameters.get('scanners', []),
                    'scanner_configs': parameters.get('scanner_configs', {}),
                    'weights': parameters.get('weights', {}),
                    'actual_parameters': parameters.get('actual_parameters', {}),
                    'scanner_summary': parameters.get('scanner_summary', {})
                })
            
            db_task = AnalysisTask(
                task_id=task_id,
                analysis_type=analysis_type,
                analysis_name=analysis_name,
                parameters=enhanced_parameters,
                status='running',
                progress_percent=0,
                progress_message='Initializing...',
                start_time=datetime.utcnow(),
            )
            session.add(db_task)
            session.commit()
            logger.info(f"✅ Created analysis task record for Task ID: {task_id}")
            
            # Log initial progress
            log_progress("Analysis task initialized", 5, 'info')
            
        except Exception as e:
            logger.error(f"❌ Failed to create analysis task record: {e}")
            raise
        
        try:
            if is_analysis_cancelled(task_id):
                raise Exception("Task was cancelled")
            
            analysis_result = None
            
            if analysis_type == 'etf_technical':
                logger.info(f"📊 Starting ETF technical analysis...")
                log_progress("Starting ETF technical analysis", 10, 'info')
                
                analysis_result = analytics_service.run_etf_technical_analysis(
                    db_session=session,
                    codes=parameters.get('codes'),
                    start_date=parameters.get('start_date'),
                    end_date=parameters.get('end_date'),
                    column=parameters.get('column', 'price'),
                    ema_short=parameters.get('ema_short', 20),
                    ema_long=parameters.get('ema_long', 50),
                    rsi_window=parameters.get('rsi_window', 14),
                    macd_fast=parameters.get('macd_fast', 12),
                    macd_slow=parameters.get('macd_slow', 26),
                    macd_sign=parameters.get('macd_sign', 9),
                    save_results=False,  # Don't save here - backend will save after this returns
                )
                
                log_progress("ETF technical analysis completed", 80, 'success')
                
            elif analysis_type == 'etf_scan':
                logger.info(f"📊 Starting ETF scan analysis...")
                log_progress("Starting ETF scan analysis", 10, 'info')
                
                # Extract scanner configurations from frontend parameters
                scanner_configs = parameters.get('scanner_configs', {})
                scanners = parameters.get('scanners', [])
                weights = parameters.get('weights', {})
                
                # Extract individual scanner parameters for backward compatibility
                ema_config = scanner_configs.get('ema_cross', {})
                macd_config = scanner_configs.get('macd', {})
                rsi_config = scanner_configs.get('rsi', {})
                supertrend_config = scanner_configs.get('supertrend', {})
                momentum_config = scanner_configs.get('momentum', {})
                daily_momentum_config = scanner_configs.get('daily_momentum', {})
                
                logger.info(f"📊 ETF Scan Parameters - Scanners: {scanners}, Configs: {scanner_configs}")
                
                analysis_result = analytics_service.run_etf_scan_analysis(
                    db_session=session,
                    fund_type=parameters.get('fund_type'),
                    specific_codes=parameters.get('specific_codes'),
                    start_date=parameters.get('start_date'),
                    end_date=parameters.get('end_date'),
                    column=parameters.get('column', 'price'),
                    # EMA parameters from scanner config
                    ema_short=ema_config.get('short', parameters.get('ema_short', 20)),
                    ema_long=ema_config.get('long', parameters.get('ema_long', 50)),
                    # RSI parameters from scanner config
                    rsi_window=rsi_config.get('window', parameters.get('rsi_window', 14)),
                    rsi_lower=rsi_config.get('lower', parameters.get('rsi_lower', 30)),
                    rsi_upper=rsi_config.get('upper', parameters.get('rsi_upper', 70)),
                    # MACD parameters from scanner config
                    macd_fast=macd_config.get('fast', parameters.get('macd_fast', 12)),
                    macd_slow=macd_config.get('slow', parameters.get('macd_slow', 26)),
                    macd_sign=macd_config.get('signal', parameters.get('macd_sign', 9)),
                    # Use the structured parameters from frontend
                    weights=weights,
                    score_threshold=parameters.get('score_threshold', 0.0),
                    include_keywords=parameters.get('include_keywords', []),
                    exclude_keywords=parameters.get('exclude_keywords', []),
                    case_sensitive=parameters.get('case_sensitive', False),
                    scanners=scanners,
                    scanner_configs=scanner_configs,
                    save_results=False,  # Don't save here - backend will save after this returns
                )
                
                log_progress("ETF scan analysis completed", 80, 'success')
                
            elif analysis_type == 'stock_technical':
                logger.info(f"📊 Starting stock technical analysis...")
                log_progress("Starting stock technical analysis", 10, 'info')
                
                analysis_result = analytics_service.run_stock_technical_analysis(
                    db_session=session,
                    symbols=parameters.get('symbols', []),
                    start_date=parameters.get('start_date'),
                    end_date=parameters.get('end_date'),
                    indicators=parameters.get('indicators', ['ema', 'rsi', 'macd']),
                    ema_short=parameters.get('ema_short', 12),
                    ema_long=parameters.get('ema_long', 26),
                    rsi_period=parameters.get('rsi_period', 14),
                    bb_period=parameters.get('bb_period', 20),
                    bb_std=parameters.get('bb_std', 2),
                    save_results=False,  # Don't save here - backend will save after this returns
                )
                
                log_progress("Stock technical analysis completed", 80, 'success')
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            if is_analysis_cancelled(task_id):
                raise Exception("Task was cancelled")
            
            # Save results to database
            execution_time_ms = int((time.time() - start_time) * 1000)
            log_progress("Saving analysis results", 90, 'info')
            
            try:
                from finance_tools.etfs.tefas.models import AnalysisResult
                import math
                import copy
                
                # Helper function to clean NaN and Inf values for JSON serialization
                def clean_for_json(obj):
                    """Clean data for JSON serialization by replacing nan and inf values."""
                    if isinstance(obj, dict):
                        return {k: clean_for_json(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [clean_for_json(item) for item in obj]
                    elif isinstance(obj, float):
                        if math.isnan(obj):
                            return None
                        elif math.isinf(obj):
                            return None
                        else:
                            return obj
                    else:
                        return obj
                
                # Use the complete analysis_result from the service (which already has all fields properly formatted)
                # Don't reconstruct it here - just use it directly to preserve components, indicators_snapshot, etc.
                if analysis_result:
                    # The analytics_service already returns properly formatted data
                    # Just use it as-is to preserve all fields (components, indicators_snapshot, reasons)
                    # But clean NaN/Inf values for JSON compliance
                    results_data = clean_for_json(copy.deepcopy(analysis_result))
                else:
                    # Fallback if no result
                    results_data = {
                        'analysis_type': analysis_type,
                        'analysis_name': analysis_name,
                        'parameters': parameters,
                        'execution_time_ms': execution_time_ms,
                        'timestamp': datetime.utcnow().isoformat(),
                        'results': [],
                        'result_count': 0,
                    }
                
                # Save analysis result
                db_result = AnalysisResult(
                    analysis_type=analysis_type,
                    analysis_name=analysis_name,
                    parameters=parameters,
                    results_data=results_data,
                    result_count=analysis_result.get('result_count', 0) if analysis_result else 0,
                    execution_time_ms=execution_time_ms,
                    status='completed',
                    created_at=datetime.utcnow(),
                )
                session.add(db_result)
                session.commit()
                result_id = db_result.id
                logger.info(f"✅ Saved analysis result with ID: {result_id} (preserving all fields from analytics_service)")
                
            except Exception as e:
                logger.error(f"❌ Failed to save analysis result: {e}")
                raise
            
            # Update task status to completed
            try:
                from finance_tools.etfs.tefas.models import AnalysisTask
                db_task = session.query(AnalysisTask).filter_by(task_id=task_id).first()
                if db_task:
                    db_task.status = 'completed'
                    db_task.progress_percent = 100
                    db_task.progress_message = 'Analysis completed successfully'
                    db_task.end_time = datetime.utcnow()
                    db_task.result_id = result_id
                    
                    # Update task parameters with enhanced scanner details if available
                    if analysis_type == 'etf_scan' and analysis_result and 'parameters' in analysis_result:
                        enhanced_params = analysis_result['parameters']
                        if 'scanners' in enhanced_params or 'scanner_configs' in enhanced_params:
                            db_task.parameters = enhanced_params
                            logger.info(f"✅ Updated task parameters with scanner details for Task ID: {task_id}")
                    
                    session.commit()
                    logger.info(f"✅ Updated task status to completed for Task ID: {task_id}")
            except Exception as e:
                logger.error(f"❌ Failed to update task status: {e}")
            
            # Final progress update
            log_progress("Analysis completed successfully", 100, 'success')
            
            logger.info(f"✅ ANALYSIS COMPLETED - Task ID: {task_id}, Time: {execution_time_ms}ms, Results: {analysis_result.get('result_count', 0) if analysis_result else 0}")
            
        finally:
            session.close()
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ ANALYSIS FAILED - Task ID: {task_id}, Error: {error_msg}")
        
        # Update task status to failed
        try:
            session = session_factory()
            from finance_tools.etfs.tefas.models import AnalysisTask
            
            db_task = session.query(AnalysisTask).filter_by(task_id=task_id).first()
            if db_task:
                db_task.status = 'failed'
                db_task.progress_percent = 100
                db_task.progress_message = f'Analysis failed: {error_msg}'
                db_task.error_message = error_msg
                db_task.error_type = type(e).__name__
                db_task.end_time = datetime.utcnow()
                session.commit()
                logger.info(f"✅ Updated task status to failed for Task ID: {task_id}")
            session.close()
        except Exception as update_error:
            logger.error(f"❌ Failed to update task status after error: {update_error}")
        
        # Update global progress
        with analysis_progress_lock:
            analysis_progress.update({
                "is_running": False,
                "progress": 100,
                "progress_percent": 100,
                "progress_message": f"Analysis failed: {error_msg}",
                "error": error_msg,
            })
    
    finally:
        # Clean up task from active tasks
        if task_id in active_analysis_tasks:
            del active_analysis_tasks[task_id]
            logger.info(f"🧹 Cleaned up active task reference for Task ID: {task_id}")


# Analysis Task Management Endpoints

@app.post("/api/analytics/run")
async def start_analysis_task(request: Dict[str, Any]):
    """
    Start an analysis task in background.
    
    Request body:
    {
        "analysis_type": "etf_technical|etf_scan|stock_technical",
        "analysis_name": "Human readable name",
        "parameters": { ... analysis-specific parameters ... }
    }
    """
    global analysis_progress, active_analysis_tasks, analysis_cancellation_flags, analysis_progress_lock
    
    try:
        analysis_type = request.get("analysis_type")
        analysis_name = request.get("analysis_name", "Analysis")
        parameters = request.get("parameters", {})
        
        if not analysis_type:
            raise HTTPException(status_code=400, detail="analysis_type is required")
        
        task_id = str(uuid.uuid4())
        
        with analysis_progress_lock:
            analysis_progress.update({
                "is_running": True,
                "progress": 0,
                "progress_percent": 0,
                "status": "Starting analysis...",
                "progress_message": "Initializing...",
                "analysis_type": analysis_type,
                "task_id": task_id,
                "start_time": datetime.now().isoformat(),
                "error": None,
            })
        
        analysis_cancellation_flags[task_id] = {"cancelled": False}
        
        db_provider = DatabaseEngineProvider()
        db_provider.ensure_initialized()
        session_factory = db_provider.get_session_factory()
        
        logger.info(f"🚀 Submitting analysis task - Task ID: {task_id}, Type: {analysis_type}")
        future = executor.submit(run_analysis_sync, analysis_type, analysis_name, parameters, task_id, session_factory)
        
        active_analysis_tasks[task_id] = {
            "future": future,
            "start_time": datetime.now(),
            "analysis_type": analysis_type,
            "analysis_name": analysis_name,
            "parameters": parameters,
        }
        
        logger.info(f"📋 Analysis task stored - Task ID: {task_id}, Active tasks: {len(active_analysis_tasks)}")
        
        return {
            "task_id": task_id,
            "message": "Analysis started in background",
            "analysis_type": analysis_type,
            "analysis_name": analysis_name,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting analysis task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/progress")
async def get_analysis_progress():
    """Get current analysis progress."""
    with analysis_progress_lock:
        return analysis_progress.copy()


@app.get("/api/analytics/tasks")
async def get_active_analysis_tasks():
    """Get list of active analysis tasks."""
    try:
        active_count = len(active_analysis_tasks)
        tasks_list = []
        
        for task_id, task_info in active_analysis_tasks.items():
            tasks_list.append({
                "task_id": task_id,
                "analysis_type": task_info.get("analysis_type"),
                "analysis_name": task_info.get("analysis_name"),
                "start_time": task_info.get("start_time").isoformat() if task_info.get("start_time") else None,
            })
        
        return {
            "active_tasks": active_count,
            "tasks": tasks_list,
        }
    
    except Exception as e:
        logger.error(f"Error getting active analysis tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/history")
async def get_analysis_history(
    analysis_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    page: int = 1,
    session = Depends(get_db_session)
):
    """Get analysis task history with filtering and pagination."""
    try:
        from finance_tools.etfs.tefas.models import AnalysisTask
        from sqlalchemy import desc
        
        query = session.query(AnalysisTask)
        
        if analysis_type:
            query = query.filter_by(analysis_type=analysis_type)
        if status:
            query = query.filter_by(status=status)
        
        total = query.count()
        offset = (page - 1) * limit
        tasks = query.order_by(desc(AnalysisTask.created_at)).offset(offset).limit(limit).all()
        
        tasks_data = []
        for task in tasks:
            exec_time = None
            if task.start_time and task.end_time:
                exec_time = int((task.end_time - task.start_time).total_seconds() * 1000)
            
            tasks_data.append({
                "id": task.id,
                "task_id": task.task_id,
                "analysis_type": task.analysis_type,
                "analysis_name": task.analysis_name,
                "status": task.status,
                "progress_percent": task.progress_percent,
                "progress_message": task.progress_message,
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "end_time": task.end_time.isoformat() if task.end_time else None,
                "execution_time_ms": exec_time,
                "error_message": task.error_message,
                "result_id": task.result_id,
            })
        
        return {
            "tasks": tasks_data,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }
    
    except Exception as e:
        logger.error(f"Error getting analysis history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analytics/cancel/{task_id}")
async def cancel_analysis_task(task_id: str):
    """Cancel a running analysis task."""
    global analysis_cancellation_flags
    
    try:
        if task_id not in analysis_cancellation_flags:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        analysis_cancellation_flags[task_id]["cancelled"] = True
        logger.info(f"🛑 Set cancellation flag for analysis task {task_id}")
        
        try:
            from finance_tools.etfs.tefas.models import AnalysisTask
            
            db_provider = DatabaseEngineProvider()
            db_provider.ensure_initialized()
            session_factory = db_provider.get_session_factory()
            
            with session_factory() as session:
                db_task = session.query(AnalysisTask).filter_by(task_id=task_id).first()
                if db_task and db_task.status == 'running':
                    db_task.status = 'cancelled'
                    db_task.progress_message = 'Task was cancelled by user'
                    db_task.end_time = datetime.utcnow()
                    session.commit()
                    logger.info(f"✅ Updated task status to cancelled for Task ID: {task_id}")
        except Exception as e:
            logger.error(f"❌ Failed to update task status after cancellation: {e}")
        
        return {
            "message": "Analysis task cancelled",
            "task_id": task_id,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling analysis task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/task-details/{task_id}")
async def get_analysis_task_details(task_id: str, session = Depends(get_db_session)):
    """Get detailed information about an analysis task."""
    try:
        from finance_tools.etfs.tefas.models import AnalysisTask, AnalysisProgressLog
        
        task = session.query(AnalysisTask).filter_by(task_id=task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        logs = session.query(AnalysisProgressLog).filter_by(task_id=task_id)            .order_by(AnalysisProgressLog.timestamp).all()
        
        logs_data = []
        for log in logs:
            logs_data.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "message": log.message,
                "message_type": log.message_type,
                "progress_percent": log.progress_percent,
            })
        
        exec_time = None
        if task.start_time and task.end_time:
            exec_time = int((task.end_time - task.start_time).total_seconds() * 1000)
        elif task.start_time:
            exec_time = int((datetime.utcnow() - task.start_time).total_seconds() * 1000)
        
        task_info = {
            "id": task.id,
            "task_id": task.task_id,
            "analysis_type": task.analysis_type,
            "analysis_name": task.analysis_name,
            "status": task.status,
            "progress_percent": task.progress_percent,
            "progress_message": task.progress_message,
            "start_time": task.start_time.isoformat() if task.start_time else None,
            "end_time": task.end_time.isoformat() if task.end_time else None,
            "execution_time_ms": exec_time,
            "error_message": task.error_message,
            "result_id": task.result_id,
            "parameters": task.parameters,  # Include parameters for scanner details
        }
        
        stats = {
            "total_logs": len(logs),
            "success_logs": sum(1 for log in logs if log.message_type == 'success'),
            "error_logs": sum(1 for log in logs if log.message_type == 'error'),
        }
        
        return {
            "task_info": task_info,
            "progress_logs": logs_data,
            "statistics": stats,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis task details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analytics/etf/technical")
async def run_etf_technical_analysis(
    request: Dict[str, Any],
    session = Depends(get_db_session)
):
    """
    Run ETF technical analysis.

    Request body:
    {
        "codes": ["NNF", "YAC"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "column": "price",
        "indicators": {
            "ema": {"windows": [20, 50]},
            "rsi": {"window": 14}
        },
        "include_keywords": ["fon"],
        "exclude_keywords": ["emeklilik"],
        "case_sensitive": false,
        "user_id": "user123"
    }
    """
    try:
        result = analytics_service.run_etf_technical_analysis(
            db_session=session,
            **request
        )
        return result
    except Exception as e:
        logger.error(f"Error in ETF technical analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analytics/etf/scan")
async def run_etf_scan_analysis(
    request: Dict[str, Any],
    session = Depends(get_db_session)
):
    """
    Run ETF scan analysis for buy/sell/hold recommendations.

    Request body:
    {
        "codes": ["NNF", "YAC"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "column": "price",
        "ema_short": 20,
        "ema_long": 50,
        "rsi_window": 14,
        "rsi_lower": 30.0,
        "rsi_upper": 70.0,
        "buy_threshold": 1.0,
        "sell_threshold": 1.0,
        "user_id": "user123"
    }
    """
    try:
        result = analytics_service.run_etf_scan_analysis(
            db_session=session,
            **request
        )
        return result
    except Exception as e:
        logger.error(f"Error in ETF scan analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analytics/stock/technical")
async def run_stock_technical_analysis(
    request: Dict[str, Any],
    session = Depends(get_db_session)
):
    """
    Run stock technical analysis.

    Request body:
    {
        "symbols": ["AAPL", "MSFT"],
        "indicators": ["EMA", "RSI", "MACD"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "ema_periods": [12, 26, 50],
        "rsi_period": 14,
        "user_id": "user123"
    }
    """
    try:
        result = analytics_service.run_stock_technical_analysis(
            db_session=session,
            **request
        )
        return result
    except Exception as e:
        logger.error(f"Error in stock technical analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/capabilities")
async def get_analytics_capabilities():
    """
    Get available analytics capabilities and functions.
    """
    try:
        capabilities = {
            "etf_analytics": {
                "technical_analysis": {
                    "description": "Technical indicators for ETF data (EMA, RSI, MACD, momentum, supertrend)",
                    "supported_columns": ["price", "market_cap", "number_of_investors", "number_of_shares"],
                    "supported_indicators": {
                        "ema": {"windows": "List of EMA windows (e.g., [20, 50])"},
                        "rsi": {"window": "RSI calculation window (e.g., 14)"},
                        "macd": {"window_slow": 26, "window_fast": 12, "window_sign": 9},
                        "momentum": {"windows": "List of momentum windows (e.g., [30, 60, 90, 180, 360])"},
                        "daily_momentum": {"windows": "List of daily momentum windows"},
                        "supertrend": {"hl_factor": 0.05, "atr_period": 10, "multiplier": 3.0}
                    },
                    "filtering": {
                        "include_keywords": "List of keywords to include in fund titles",
                        "exclude_keywords": "List of keywords to exclude from fund titles",
                        "case_sensitive": "Boolean for case-sensitive matching"
                    }
                },
                "scan_analysis": {
                    "description": "ETF scanning with weighted scoring for buy/sell/hold recommendations",
                    "scoring_weights": {
                        "w_ema_cross": "EMA crossover weight",
                        "w_macd": "MACD weight",
                        "w_rsi": "RSI weight",
                        "w_momentum": "Momentum weight",
                        "w_momentum_daily": "Daily momentum weight",
                        "w_supertrend": "Supertrend weight"
                    },
                    "thresholds": {
                        "buy_threshold": "Minimum score for BUY recommendation",
                        "sell_threshold": "Maximum score for SELL recommendation (negative)"
                    }
                }
            },
            "stock_analytics": {
                "technical_analysis": {
                    "description": "Technical indicators for stock data",
                    "supported_indicators": [
                        "EMA", "SMA", "RSI", "MACD", "BB", "STOCH", "MOMENTUM", "ROC", "ATR", "CCI"
                    ],
                    "configurable_parameters": {
                        "ema_periods": "EMA calculation periods",
                        "rsi_period": "RSI calculation period",
                        "macd_fast": "MACD fast EMA period",
                        "macd_slow": "MACD slow EMA period",
                        "macd_signal": "MACD signal line period",
                        "bb_period": "Bollinger Bands period",
                        "bb_std": "Bollinger Bands standard deviation multiplier"
                    }
                }
            },
            "caching": {
                "enabled": True,
                "ttl_hours": 24,
                "description": "Analysis results are cached for 24 hours to improve performance"
            },
            "history_tracking": {
                "enabled": True,
                "description": "All analysis executions are tracked for user history and favorites"
            }
        }

        return capabilities

    except Exception as e:
        logger.error(f"Error getting analytics capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/history")
async def get_analysis_history(
    user_id: Optional[str] = None,
    analysis_type: Optional[str] = None,
    limit: int = 50,
    session = Depends(get_db_session)
):
    """
    Get analysis history.

    Query parameters:
    - user_id: Filter by user ID (optional)
    - analysis_type: Filter by analysis type (optional)
    - limit: Maximum number of records (default: 50)
    """
    try:
        history = analytics_service.get_analysis_history(
            db_session=session,
            user_id=user_id,
            analysis_type=analysis_type,
            limit=limit
        )
        return {"history": history}
    except Exception as e:
        logger.error(f"Error getting analysis history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/cache")
async def get_cached_results(
    analysis_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    session = Depends(get_db_session)
):
    """
    Get cached analysis results with pagination and filtering.

    Query parameters:
    - analysis_type: Filter by analysis type (optional)
    - status: Filter by status (completed, failed, etc.)
    - search: Search in analysis name or parameters
    - page: Page number (default: 1)
    - limit: Results per page (default: 20, max: 100)
    """
    try:
        from finance_tools.etfs.tefas.models import AnalysisResult
        from sqlalchemy import desc, or_, func
        
        # Limit max page size
        limit = min(limit, 100)
        offset = (page - 1) * limit
        
        # Build query
        query = session.query(AnalysisResult)
        
        # Apply filters
        if analysis_type:
            query = query.filter(AnalysisResult.analysis_type == analysis_type)
        
        if status:
            query = query.filter(AnalysisResult.status == status)
        
        # Apply search if provided
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    AnalysisResult.analysis_name.ilike(search_pattern),
                    func.json_extract(AnalysisResult.parameters, '$.codes').like(search_pattern),
                    func.json_extract(AnalysisResult.parameters, '$.specific_codes').like(search_pattern),
                    func.json_extract(AnalysisResult.parameters, '$.symbols').like(search_pattern),
                )
            )
        
        # Only return non-expired results
        now = datetime.utcnow()
        query = query.filter(
            (AnalysisResult.expires_at.is_(None)) | (AnalysisResult.expires_at > now)
        )
        
        # Get total count before pagination
        total = query.count()
        
        # Order by most recent first and apply pagination
        results = query.order_by(desc(AnalysisResult.created_at)).offset(offset).limit(limit).all()
        
        cached_results = [
            {
                "id": result.id,
                "analysis_type": result.analysis_type,
                "analysis_name": result.analysis_name,
                "parameters": result.parameters,
                "result_count": result.result_count,
                "execution_time_ms": result.execution_time_ms,
                "status": result.status,
                "created_at": result.created_at.isoformat(),
                "expires_at": result.expires_at.isoformat() if result.expires_at else None
            }
            for result in results
        ]
        
        return {
            "results": cached_results,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error getting cached results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/results/{result_id}")
async def get_analysis_result(result_id: int, session = Depends(get_db_session)):
    """
    Get analysis results by result ID.
    """
    try:
        from finance_tools.etfs.tefas.models import AnalysisResult
        import math
        
        # Helper function to clean NaN and Inf values for JSON serialization
        def clean_for_json(obj):
            """Clean data for JSON serialization by replacing nan and inf values."""
            if isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            elif isinstance(obj, float):
                if math.isnan(obj):
                    return None
                elif math.isinf(obj):
                    return None
                else:
                    return obj
            else:
                return obj
        
        result = session.query(AnalysisResult).filter_by(id=result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail=f"Analysis result {result_id} not found")
        
        # Clean the data before returning to handle any NaN values in old records
        cleaned_results = clean_for_json(result.results_data.get('results', []) if result.results_data else [])
        cleaned_metadata = clean_for_json(result.results_data.get('metadata', {}) if result.results_data else {})
        
        return {
            "id": result.id,
            "analysis_type": result.analysis_type,
            "analysis_name": result.analysis_name,
            "parameters": result.parameters,
            "results": cleaned_results,
            "result_count": result.result_count,
            "execution_time_ms": result.execution_time_ms,
            "timestamp": result.created_at.isoformat(),
            "metadata": cleaned_metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis result {result_id}: {e}")
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
