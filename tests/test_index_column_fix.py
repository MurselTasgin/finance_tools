#!/usr/bin/env python3
"""
Test script to verify that the index column issue is resolved.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.stocks.data_downloaders import YFinanceDownloader
import pandas as pd

def test_index_column_fix():
    """Test that the index column issue is resolved."""
    print("Testing Index Column Fix")
    print("=" * 40)
    
    yf_tool = YFinanceDownloader()
    
    try:
        # Test single stock download
        print("1. Testing single stock download:")
        result = yf_tool.download("AAPL", period="1mo")
        df = result.as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        
        # Check for unwanted 'index' column
        has_index_column = 'index' in df.columns
        print(f"   Has unwanted 'index' column: {has_index_column}")
        
        if has_index_column:
            print(f"   ❌ ERROR: Found unwanted 'index' column!")
        else:
            print(f"   ✅ No unwanted 'index' column found")
        
        # Check for Date column
        has_date_column = 'Date' in df.columns
        print(f"   Has 'Date' column: {has_date_column}")
        
        # Check column order
        if len(df.columns) >= 2:
            first_two_cols = df.columns[:2].tolist()
            print(f"   First two columns: {first_two_cols}")
            column_order_correct = first_two_cols == ['Date', 'Symbol']
            print(f"   Column order correct: {column_order_correct}")
        
        print()
        
        # Test multiple stocks
        print("2. Testing multiple stocks download:")
        result = yf_tool.download("AAPL, MSFT", period="1mo")
        df = result.as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        
        # Check for unwanted 'index' column
        has_index_column = 'index' in df.columns
        print(f"   Has unwanted 'index' column: {has_index_column}")
        
        if has_index_column:
            print(f"   ❌ ERROR: Found unwanted 'index' column!")
        else:
            print(f"   ✅ No unwanted 'index' column found")
        
        # Check for Date column
        has_date_column = 'Date' in df.columns
        print(f"   Has 'Date' column: {has_date_column}")
        
        # Check column order
        if len(df.columns) >= 2:
            first_two_cols = df.columns[:2].tolist()
            print(f"   First two columns: {first_two_cols}")
            column_order_correct = first_two_cols == ['Date', 'Symbol']
            print(f"   Column order correct: {column_order_correct}")
        
        print()
        
        # Test with date range
        print("3. Testing date range download:")
        result = yf_tool.download(
            symbols=["AAPL", "MSFT"],
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        df = result.as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        
        # Check for unwanted 'index' column
        has_index_column = 'index' in df.columns
        print(f"   Has unwanted 'index' column: {has_index_column}")
        
        if has_index_column:
            print(f"   ❌ ERROR: Found unwanted 'index' column!")
        else:
            print(f"   ✅ No unwanted 'index' column found")
        
        print()
        
        # Display sample data
        print("4. Sample data:")
        result = yf_tool.download("AAPL", period="1mo")
        df = result.as_df()
        
        print("   First 5 rows:")
        print(df.head())
        print()
        
        print("   Column names:")
        for i, col in enumerate(df.columns):
            print(f"   {i+1}. {col}")
        print()
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

def test_various_scenarios():
    """Test various scenarios to ensure no index column appears."""
    print("\n" + "=" * 60)
    print("Testing Various Scenarios")
    print("=" * 60)
    
    yf_tool = YFinanceDownloader()
    
    test_cases = [
        ("Single stock string", "AAPL"),
        ("Multiple stocks string", "AAPL, MSFT"),
        ("Single stock list", ["AAPL"]),
        ("Multiple stocks list", ["AAPL", "MSFT", "GOOGL"]),
        ("Date range", {"symbols": ["AAPL", "MSFT"], "start_date": "2024-01-01", "end_date": "2024-01-31"}),
    ]
    
    for test_name, test_input in test_cases:
        try:
            print(f"Testing: {test_name}")
            
            if isinstance(test_input, dict):
                # Handle date range case
                result = yf_tool.download(**test_input)
            else:
                # Handle simple symbol case
                result = yf_tool.download(test_input, period="1mo")
            
            df = result.as_df()
            
            print(f"   ✅ Success!")
            print(f"   Input: {test_input}")
            print(f"   DataFrame shape: {df.shape}")
            print(f"   Columns: {list(df.columns)}")
            
            # Check for unwanted 'index' column
            has_index_column = 'index' in df.columns
            print(f"   Has unwanted 'index' column: {has_index_column}")
            
            if has_index_column:
                print(f"   ❌ ERROR: Found unwanted 'index' column!")
            else:
                print(f"   ✅ No unwanted 'index' column found")
            
            # Check for Date column
            has_date_column = 'Date' in df.columns
            print(f"   Has 'Date' column: {has_date_column}")
            
            # Check column order
            if len(df.columns) >= 2:
                first_two_cols = df.columns[:2].tolist()
                print(f"   First two columns: {first_two_cols}")
                column_order_correct = first_two_cols == ['Date', 'Symbol']
                print(f"   Column order correct: {column_order_correct}")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            print()

if __name__ == "__main__":
    test_index_column_fix()
    test_various_scenarios() 