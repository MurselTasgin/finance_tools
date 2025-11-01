#!/usr/bin/env python3
"""
Test script to verify DataFrame return format.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.stocks.data_downloaders import YFinanceDownloader
import pandas as pd

def test_dataframe_return():
    """Test that data is returned as DataFrame directly."""
    print("Testing DataFrame return format...")
    
    # Initialize the downloader
    downloader = YFinanceDownloader()
    
    try:
        # Test single stock
        print("\n1. Testing single stock download...")
        result = downloader.execute(
            symbols=["AAPL"],
            period="1mo",
            interval="1d",
            return_format="dataframe"
        )
        
        if result.success:
            print(f"✅ Single stock success!")
            print(f"   Data type: {type(result.data)}")
            print(f"   Is dict: {isinstance(result.data, dict)}")
            if isinstance(result.data, dict) and 'data' in result.data:
                print(f"   Shape: {result.data['data'].shape}")
                print(f"   Columns: {list(result.data['data'].columns)}")
        else:
            print(f"❌ Single stock failed: {result.error}")
        
        # Test multiple stocks
        print("\n2. Testing multiple stocks download...")
        result = downloader.execute(
            symbols=["AAPL", "MSFT"],
            period="1mo",
            interval="1d",
            return_format="dataframe"
        )
        
        if result.success:
            print(f"✅ Multiple stocks success!")
            print(f"   Data type: {type(result.data)}")
            print(f"   Is dict: {isinstance(result.data, dict)}")
            if isinstance(result.data, dict) and 'data' in result.data:
                print(f"   Shape: {result.data['data'].shape}")
                print(f"   Columns: {list(result.data['data'].columns)}")
                print(f"   Symbols: {result.data['data']['Symbol'].unique()}")
        else:
            print(f"❌ Multiple stocks failed: {result.error}")
        
        # Test different formats
        print("\n3. Testing different return formats...")
        formats = ["dataframe", "dict", "json"]
        
        for fmt in formats:
            result = downloader.execute(
                symbols=["AAPL"],
                period="1mo",
                interval="1d",
                return_format=fmt
            )
            
            if result.success:
                print(f"✅ {fmt} format success!")
                print(f"   Data type: {type(result.data)}")
            else:
                print(f"❌ {fmt} format failed: {result.error}")
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dataframe_return() 