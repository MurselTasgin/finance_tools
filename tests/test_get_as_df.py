#!/usr/bin/env python3
"""
Test script for get_as_df function.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.stocks.data_downloaders import YFinanceDownloader
from finance_tools.utils.dataframe_utils import get_as_df, get_stock_summary
import pandas as pd

def test_get_as_df():
    """Test the get_as_df function."""
    print("Testing get_as_df Function")
    print("=" * 40)
    
    downloader = YFinanceDownloader()
    
    try:
        # Test 1: Single stock
        print("1. Testing single stock...")
        result = downloader.execute(symbols=["AAPL"], period="1mo")
        df = get_as_df(result)
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Has Symbol column: {'Symbol' in df.columns}")
        print()
        
        # Test 2: Multiple stocks
        print("2. Testing multiple stocks...")
        result = downloader.execute(symbols=["AAPL", "MSFT"], period="1mo")
        df = get_as_df(result)
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Has Symbol column: {'Symbol' in df.columns}")
        print(f"   Symbols: {df['Symbol'].unique()}")
        print(f"   Has Date column: {'Date' in df.columns}")
        print()
        
        # Test 3: Verify data integrity
        print("3. Testing data integrity...")
        if 'Symbol' in df.columns and 'Date' in df.columns:
            # Check that each symbol has data
            for symbol in df['Symbol'].unique():
                symbol_data = df[df['Symbol'] == symbol]
                print(f"   {symbol}: {len(symbol_data)} rows")
                
                # Check for required columns
                required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                missing_cols = [col for col in required_cols if col not in symbol_data.columns]
                if missing_cols:
                    print(f"   ⚠️  Missing columns for {symbol}: {missing_cols}")
                else:
                    print(f"   ✅ All required columns present for {symbol}")
        print()
        
        # Test 4: Test summary function
        print("4. Testing summary function...")
        summary = get_stock_summary(result)
        print(f"   Summary keys: {list(summary.keys())}")
        print(f"   Shape: {summary.get('shape')}")
        print(f"   Symbols: {summary.get('symbols')}")
        print(f"   Date range: {summary.get('date_range')}")
        print()
        
        # Test 5: Test with empty result
        print("5. Testing error handling...")
        try:
            # This should raise an error
            df = get_as_df("invalid_result")
            print("   ❌ Should have raised an error")
        except ValueError as e:
            print(f"   ✅ Correctly raised error: {e}")
        print()
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_pipe_functionality():
    """Test pipe-like functionality."""
    print("\nTesting Pipe Functionality")
    print("=" * 40)
    
    downloader = YFinanceDownloader()
    
    try:
        # Simulate pipe functionality
        result = downloader.execute(symbols=["AAPL", "MSFT"], period="1mo")
        
        # Method 1: Direct function call
        df1 = get_as_df(result)
        
        # Method 2: Simulate pipe (Python 3.12+ would support: result | get_as_df)
        df2 = get_as_df(result)
        
        # Both should be identical
        if df1.equals(df2):
            print("✅ Pipe functionality works correctly!")
            print(f"   DataFrame shape: {df1.shape}")
            print(f"   Both methods return identical results")
        else:
            print("❌ Pipe functionality failed - results differ")
        
    except Exception as e:
        print(f"❌ Pipe test failed: {e}")

if __name__ == "__main__":
    test_get_as_df()
    test_pipe_functionality() 