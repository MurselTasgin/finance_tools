# finance_tools/backend/main.py
import os
# Override database to use test database with data - MUST be set before any imports
os.environ["DATABASE_NAME"] = "test_finance_tools.db"

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import date, datetime, timedelta
import sys
from pathlib import Path

# Add the parent directory to the path to import finance_tools modules
sys.path.append(str(Path(__file__).parent.parent))

from finance_tools.etfs.tefas.repository import DatabaseEngineProvider, TefasRepository
from finance_tools.etfs.tefas.service import TefasPersistenceService
from finance_tools.config import get_config
from finance_tools.logging import get_logger

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
}

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
    global download_progress
    
    if download_progress["is_downloading"]:
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
        
        download_progress = {
            "is_downloading": True,
            "progress": 0,
            "status": "Starting download...",
            "records_downloaded": 0,
            "total_records": 0,
            "start_time": datetime.now().isoformat(),
            "estimated_completion": None,
            "current_phase": "initializing",
        }
        
        # Run download in background
        asyncio.create_task(run_download(start_date, end_date, funds, kind))
        
        return {"message": "Download started"}
    except Exception as e:
        download_progress = {
            "is_downloading": False,
            "progress": 0,
            "status": f"Download failed: {str(e)}"
        }
        logger.error(f"Error starting download: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def progress_callback(status: str, progress: int, current_chunk: int):
    """Progress callback function that updates the global progress state."""
    global download_progress
    download_progress.update({
        "status": status,
        "progress": progress,
        "records_downloaded": current_chunk,
        "current_phase": "downloading",
    })

async def run_download(start_date: str, end_date: str, funds: list = None, kind: str = "BYF"):
    """Run the actual download process using TefasPersistenceService like CLI."""
    global download_progress
    import time
    
    try:
        # Initialize service with progress callback
        service = TefasPersistenceService(progress_callback=progress_callback)
        
        # Phase 1: Download data using the service
        download_progress.update({
            "status": f"Starting download of {kind} fund data from {start_date} to {end_date}...",
            "progress": 0,
            "current_phase": "downloading",
            "records_downloaded": 0,
        })
        
        # Use the same method as CLI
        info_count, breakdown_count = service.download_and_persist(
            start_date=start_date,
            end_date=end_date,
            funds=funds if funds else None,
            kind=kind,
        )
        
        total_records = info_count + breakdown_count
        
        # Update progress with actual counts
        download_progress.update({
            "total_records": total_records,
            "progress": 100,
            "status": f"Download completed successfully! {total_records} total records saved ({info_count} info, {breakdown_count} breakdown).",
            "current_phase": "completed",
            "records_downloaded": total_records,
            "is_downloading": False,
        })
        
    except Exception as e:
        download_progress.update({
            "is_downloading": False,
            "progress": 0,
            "status": f"Download failed: {str(e)}",
            "current_phase": "error",
            "records_downloaded": 0,
            "total_records": 0,
        })
        logger.error(f"Error during download: {e}")
    finally:
        download_progress["is_downloading"] = False

@app.get("/api/database/download-progress")
async def get_download_progress():
    """Get current download progress."""
    return download_progress

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

@app.get("/api/data/plot")
async def get_plot_data(
    xColumn: str = Query(...),
    yColumn: str = Query(...),
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8070)
