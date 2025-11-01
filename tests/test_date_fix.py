#!/usr/bin/env python3
"""
Test script to verify the date formatting fix.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.stocks.data_downloaders import YFinanceDownloader

def test_date_formatting_fix():
    """Test that the date formatting fix works."""
    print("Testing Date Formatting Fix")
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
        
        if 'Date' in df.columns:
            sample_dates = df['Date'].head(3).tolist()
            print(f"   Sample dates: {sample_dates}")
            
            # Check if dates are in YYYY-MM-DD format
            date_format_correct = all(len(str(date)) == 10 and str(date).count('-') == 2 for date in sample_dates)
            print(f"   Date format correct: {date_format_correct}")
        
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
        
        if 'Date' in df.columns:
            sample_dates = df['Date'].head(3).tolist()
            print(f"   Sample dates: {sample_dates}")
            
            # Check if dates are in YYYY-MM-DD format
            date_format_correct = all(len(str(date)) == 10 and str(date).count('-') == 2 for date in sample_dates)
            print(f"   Date format correct: {date_format_correct}")
        
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
        
        if 'Date' in df.columns:
            sample_dates = df['Date'].head(3).tolist()
            print(f"   Sample dates: {sample_dates}")
            
            # Check if dates are in YYYY-MM-DD format
            date_format_correct = all(len(str(date)) == 10 and str(date).count('-') == 2 for date in sample_dates)
            print(f"   Date format correct: {date_format_correct}")
        
        print()
        
        # Display sample data
        print("4. Sample data:")
        result = yf_tool.download("AAPL", period="1mo")
        df = result.as_df()
        
        print("   First 5 rows:")
        print(df.head())
        print()
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_date_formatting_fix() 