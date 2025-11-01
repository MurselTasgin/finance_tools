#!/usr/bin/env python3
"""
Test script to verify stock progress tracking functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.main import stock_progress_callback, stock_download_progress, stock_progress_lock

def test_stock_progress_callback():
    """Test the stock progress callback functionality."""

    # Reset the global state
    with stock_progress_lock:
        stock_download_progress = {
            "is_downloading": True,
            "progress": 0,
            "status": "",
            "records_downloaded": 0,
            "total_records": 0,
            "start_time": None,
            "estimated_completion": None,
            "current_phase": "",
            "task_id": "test_task",
            "error": None,
            "symbols_completed": 0,
            "symbols_total": 3,
        }

    # Test 1: Downloading message
    stock_progress_callback("📊 Downloading AAPL (1/3)...", 25, 1)

    with stock_progress_lock:
        print(f"After downloading message: records_downloaded = {stock_download_progress.get('records_downloaded', 0)}")
        assert stock_download_progress.get('records_downloaded', 0) == 0, "Should be 0 for downloading message"

    # Test 2: Success message with record count
    stock_progress_callback("✅ Downloaded AAPL: 150 records", 33, 1)

    with stock_progress_lock:
        print(f"After success message: records_downloaded = {stock_download_progress.get('records_downloaded', 0)}")
        assert stock_download_progress.get('records_downloaded', 0) == 150, f"Should be 150, got {stock_download_progress.get('records_downloaded', 0)}"

    # Test 3: Another success message
    stock_progress_callback("✅ Downloaded MSFT: 200 records", 66, 2)

    with stock_progress_lock:
        print(f"After second success message: records_downloaded = {stock_download_progress.get('records_downloaded', 0)}")
        assert stock_download_progress.get('records_downloaded', 0) == 350, f"Should be 350, got {stock_download_progress.get('records_downloaded', 0)}"

    # Test 4: Completion message
    stock_progress_callback("✅ Download completed! 350 price records, 3 info records saved.", 100, 3)

    with stock_progress_lock:
        print(f"After completion message: records_downloaded = {stock_download_progress.get('records_downloaded', 0)}")
        assert stock_download_progress.get('records_downloaded', 0) == 350, f"Should be 350, got {stock_download_progress.get('records_downloaded', 0)}"

    print("✅ All tests passed! Stock progress callback is working correctly.")

if __name__ == "__main__":
    test_stock_progress_callback()
