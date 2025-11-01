#!/usr/bin/env python3
"""
Test script to verify date formatting and column ordering in yfinance downloads.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.stocks.data_downloaders import YFinanceDownloader
import pandas as pd

def test_date_formatting():
    """Test date formatting and column ordering."""
    print("Testing Date Formatting and Column Ordering")
    print("=" * 60)
    
    yf_tool = YFinanceDownloader()
    
    try:
        # Test 1: Single stock
        print("1. Single stock download:")
        result = yf_tool.download("AAPL", period="1mo")
        df = result.as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        
        # Check date format
        if 'Date' in df.columns:
            sample_dates = df['Date'].head(3).tolist()
            print(f"   Sample dates: {sample_dates}")
            
            # Verify date format is YYYY-MM-DD
            date_format_correct = all(len(date) == 10 and date.count('-') == 2 for date in sample_dates)
            print(f"   Date format correct (YYYY-MM-DD): {date_format_correct}")
        
        # Check column order
        if len(df.columns) >= 2:
            first_two_cols = df.columns[:2].tolist()
            print(f"   First two columns: {first_two_cols}")
            column_order_correct = first_two_cols == ['Date', 'Symbol']
            print(f"   Column order correct (Date, Symbol first): {column_order_correct}")
        
        print()
        
        # Test 2: Multiple stocks
        print("2. Multiple stocks download:")
        result = yf_tool.download("AAPL, MSFT", period="1mo")
        df = result.as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        
        # Check symbols
        if 'Symbol' in df.columns:
            symbols = df['Symbol'].unique()
            print(f"   Symbols: {symbols}")
        
        # Check date format
        if 'Date' in df.columns:
            sample_dates = df['Date'].head(3).tolist()
            print(f"   Sample dates: {sample_dates}")
            
            # Verify date format is YYYY-MM-DD
            date_format_correct = all(len(date) == 10 and date.count('-') == 2 for date in sample_dates)
            print(f"   Date format correct (YYYY-MM-DD): {date_format_correct}")
        
        # Check column order
        if len(df.columns) >= 2:
            first_two_cols = df.columns[:2].tolist()
            print(f"   First two columns: {first_two_cols}")
            column_order_correct = first_two_cols == ['Date', 'Symbol']
            print(f"   Column order correct (Date, Symbol first): {column_order_correct}")
        
        print()
        
        # Test 3: Date range download
        print("3. Date range download:")
        result = yf_tool.download(
            symbols=["AAPL", "MSFT"],
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        df = result.as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        
        # Check date range
        if 'Date' in df.columns:
            date_range = df['Date'].min(), df['Date'].max()
            print(f"   Date range: {date_range}")
        
        # Check column order
        if len(df.columns) >= 2:
            first_two_cols = df.columns[:2].tolist()
            print(f"   First two columns: {first_two_cols}")
            column_order_correct = first_two_cols == ['Date', 'Symbol']
            print(f"   Column order correct (Date, Symbol first): {column_order_correct}")
        
        print()
        
        # Test 4: Verify data integrity
        print("4. Data integrity check:")
        result = yf_tool.download("AAPL, MSFT, GOOGL", period="1mo")
        df = result.as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        
        # Check for required columns
        required_cols = ['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        print(f"   Missing required columns: {missing_cols}")
        
        # Check data types
        if 'Date' in df.columns:
            date_type = df['Date'].dtype
            print(f"   Date column type: {date_type}")
        
        if 'Symbol' in df.columns:
            symbol_type = df['Symbol'].dtype
            print(f"   Symbol column type: {symbol_type}")
        
        # Check for any NaN values in key columns
        key_cols = ['Date', 'Symbol', 'Close']
        nan_counts = {col: df[col].isna().sum() for col in key_cols if col in df.columns}
        print(f"   NaN counts in key columns: {nan_counts}")
        
        print()
        
        # Test 5: Sample data display
        print("5. Sample data:")
        result = yf_tool.download("AAPL", period="1mo")
        df = result.as_df()
        
        print("   First 5 rows:")
        print(df.head())
        print()
        
        print("   Last 5 rows:")
        print(df.tail())
        print()
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

def test_various_formats():
    """Test various input formats with date formatting."""
    print("\n" + "=" * 60)
    print("Testing Various Input Formats with Date Formatting")
    print("=" * 60)
    
    yf_tool = YFinanceDownloader()
    
    test_cases = [
        ("Single string", "AAPL"),
        ("Comma-separated string", "AAPL, MSFT"),
        ("Single list", ["AAPL"]),
        ("Multiple list", ["AAPL", "MSFT"]),
    ]
    
    for test_name, symbols in test_cases:
        try:
            print(f"Testing: {test_name}")
            result = yf_tool.download(symbols, period="1mo")
            df = result.as_df()
            
            print(f"   ✅ Success!")
            print(f"   Input: {symbols}")
            print(f"   DataFrame shape: {df.shape}")
            
            # Check column order
            if len(df.columns) >= 2:
                first_two_cols = df.columns[:2].tolist()
                print(f"   First two columns: {first_two_cols}")
                column_order_correct = first_two_cols == ['Date', 'Symbol']
                print(f"   Column order correct: {column_order_correct}")
            
            # Check date format
            if 'Date' in df.columns:
                sample_date = df['Date'].iloc[0]
                print(f"   Sample date: {sample_date}")
                date_format_correct = len(sample_date) == 10 and sample_date.count('-') == 2
                print(f"   Date format correct (YYYY-MM-DD): {date_format_correct}")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            print()

if __name__ == "__main__":
    test_date_formatting()
    test_various_formats() 