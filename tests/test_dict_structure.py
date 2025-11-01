#!/usr/bin/env python3
"""
Test script to verify the new dictionary structure with 'data' key.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.stocks.data_downloaders import YFinanceDownloader
import pandas as pd

def test_dict_structure():
    """Test that data is returned as dictionary with 'data' key."""
    print("Testing dictionary structure with 'data' key...")
    
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
            print(f"   Result data type: {type(result.data)}")
            print(f"   Result data keys: {list(result.data.keys()) if isinstance(result.data, dict) else 'N/A'}")
            
            if isinstance(result.data, dict) and 'data' in result.data:
                df = result.data['data']
                print(f"   DataFrame shape: {df.shape}")
                print(f"   DataFrame columns: {list(df.columns)}")
                print(f"   DataFrame head:")
                print(df.head(3))
            else:
                print(f"   ❌ Expected dict with 'data' key, got: {type(result.data)}")
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
            print(f"   Result data type: {type(result.data)}")
            print(f"   Result data keys: {list(result.data.keys()) if isinstance(result.data, dict) else 'N/A'}")
            
            if isinstance(result.data, dict) and 'data' in result.data:
                df = result.data['data']
                print(f"   DataFrame shape: {df.shape}")
                print(f"   DataFrame columns: {list(df.columns)}")
                print(f"   Symbols in data: {df['Symbol'].unique()}")
                print(f"   DataFrame head:")
                print(df.head(3))
            else:
                print(f"   ❌ Expected dict with 'data' key, got: {type(result.data)}")
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
                if fmt == "dataframe":
                    print(f"   Is DataFrame: {isinstance(result.data, pd.DataFrame)}")
                elif fmt == "dict":
                    print(f"   Is dict: {isinstance(result.data, dict)}")
                elif fmt == "json":
                    print(f"   Is str: {isinstance(result.data, str)}")
            else:
                print(f"❌ {fmt} format failed: {result.error}")
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dict_structure() 