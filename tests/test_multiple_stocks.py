#!/usr/bin/env python3
"""
Test script for multiple stocks download functionality.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.stocks.data_downloaders import YFinanceDownloader

def test_multiple_stocks():
    """Test downloading multiple stocks."""
    print("Testing multiple stocks download...")
    
    # Initialize the downloader
    downloader = YFinanceDownloader()
    
    # Test symbols
    symbols = ["AAPL", "MSFT", "GOOGL"]
    
    try:
        # Download data for multiple stocks
        result, metadata = downloader._download_multiple_stocks(
            symbols=symbols,
            start_date="2024-01-01",
            end_date="2024-01-31",
            period="1mo",
            interval="1d",
            include_dividends=False,
            include_splits=False,
            auto_adjust=True
        )
        
        print(f"Download successful!")
        print(f"Result keys: {list(result.keys())}")
        
        if 'data' in result:
            price_data = result['data']
            print(f"Price data shape: {price_data.shape}")
            print(f"Price data columns: {list(price_data.columns)}")
            print(f"Symbols in data: {price_data['Symbol'].unique()}")
            print(f"Date range: {price_data.index.min()} to {price_data.index.max()}")
            
            # Show first few rows
            print("\nFirst 5 rows:")
            print(price_data.head())
        else:
            print("No price data found in result")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_single_stock():
    """Test downloading single stock for comparison."""
    print("\nTesting single stock download...")
    
    downloader = YFinanceDownloader()
    
    try:
        result, metadata = downloader._download_single_stock(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-31",
            period="1mo",
            interval="1d",
            include_dividends=False,
            include_splits=False,
            auto_adjust=True
        )
        
        print(f"Single stock download successful!")
        if 'data' in result:
            price_data = result['data']
            print(f"Price data shape: {price_data.shape}")
            print(f"Price data columns: {list(price_data.columns)}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_stock()
    test_multiple_stocks() 