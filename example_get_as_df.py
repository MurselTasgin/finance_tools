#!/usr/bin/env python3
"""
Example showing how to use get_as_df function as a pipe function.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.stocks.data_downloaders import YFinanceDownloader
from finance_tools.utils.dataframe_utils import get_as_df, get_stock_summary, extract_stock_data
import pandas as pd

def demonstrate_get_as_df():
    """Demonstrate the get_as_df function usage."""
    print("Demonstrating get_as_df Function")
    print("=" * 50)
    
    # Initialize the downloader
    downloader = YFinanceDownloader()
    
    try:
        # Example 1: Single stock
        print("1. Single Stock Download:")
        result = downloader.execute(symbols=["AAPL"], period="1mo")
        
        # Method 1: Direct function call
        df1 = get_as_df(result)
        print(f"   DataFrame shape: {df1.shape}")
        print(f"   Columns: {list(df1.columns)}")
        print(f"   First few rows:")
        print(df1.head(3))
        print()
        
        # Method 2: Pipe function (Python 3.12+)
        # df2 = result | get_as_df  # This would work in Python 3.12+
        print("   Note: Pipe operator (|) works in Python 3.12+")
        print()
        
        # Example 2: Multiple stocks
        print("2. Multiple Stocks Download:")
        result = downloader.execute(symbols=["AAPL", "MSFT", "GOOGL"], period="1mo")
        
        df = get_as_df(result)
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Symbols: {df['Symbol'].unique()}")
        print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
        print()
        
        # Show data by symbol
        print("   Data by Symbol:")
        for symbol in df['Symbol'].unique():
            symbol_data = df[df['Symbol'] == symbol]
            print(f"     {symbol}: {len(symbol_data)} rows, Latest Close: ${symbol_data['Close'].iloc[-1]:.2f}")
        print()
        
        # Example 3: Using with summary
        print("3. Stock Summary:")
        summary = get_stock_summary(result)
        print(f"   Summary: {summary}")
        print()
        
        # Example 4: Extract with metadata
        print("4. Extract with Metadata:")
        result_with_meta = extract_stock_data(result, include_metadata=True)
        print(f"   Data shape: {result_with_meta['data'].shape}")
        print(f"   Metadata keys: {list(result_with_meta['metadata'].keys())}")
        print()
        
        # Example 5: Chain operations
        print("5. Chain Operations:")
        df = get_as_df(result)
        
        # Filter by date
        recent_data = df[df['Date'] >= '2024-01-15']
        print(f"   Recent data shape: {recent_data.shape}")
        
        # Group by symbol and get latest
        latest_prices = recent_data.groupby('Symbol')['Close'].last()
        print(f"   Latest prices:")
        for symbol, price in latest_prices.items():
            print(f"     {symbol}: ${price:.2f}")
        print()
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

def show_pipe_usage():
    """Show how to use get_as_df as a pipe function."""
    print("\n" + "=" * 50)
    print("Pipe Function Usage Examples")
    print("=" * 50)
    
    downloader = YFinanceDownloader()
    
    try:
        # Example 1: Single stock with pipe (conceptual)
        print("1. Single Stock with Pipe (conceptual):")
        print("   # In Python 3.12+:")
        print("   df = downloader.execute(symbols=['AAPL']) | get_as_df")
        print("   print(df.head())")
        print()
        
        # Example 2: Multiple stocks with pipe (conceptual)
        print("2. Multiple Stocks with Pipe (conceptual):")
        print("   # In Python 3.12+:")
        print("   df = downloader.execute(symbols=['AAPL', 'MSFT']) | get_as_df")
        print("   print(df.groupby('Symbol')['Close'].mean())")
        print()
        
        # Example 3: Chaining operations (conceptual)
        print("3. Chaining Operations (conceptual):")
        print("   # In Python 3.12+:")
        print("   latest_prices = (")
        print("       downloader.execute(symbols=['AAPL', 'MSFT'])")
        print("       | get_as_df")
        print("       | lambda df: df.groupby('Symbol')['Close'].last()")
        print("   )")
        print()
        
        # Example 4: Actual implementation without pipe
        print("4. Actual Implementation (without pipe):")
        result = downloader.execute(symbols=["AAPL", "MSFT"], period="1mo")
        df = get_as_df(result)
        latest_prices = df.groupby('Symbol')['Close'].last()
        print(f"   Latest prices: {latest_prices.to_dict()}")
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

def demonstrate_data_processing():
    """Demonstrate data processing with get_as_df."""
    print("\n" + "=" * 50)
    print("Data Processing Examples")
    print("=" * 50)
    
    downloader = YFinanceDownloader()
    
    try:
        # Download data
        result = downloader.execute(symbols=["AAPL", "MSFT", "GOOGL"], period="1mo")
        df = get_as_df(result)
        
        print("1. Basic Statistics:")
        print(f"   Total rows: {len(df)}")
        print(f"   Symbols: {df['Symbol'].unique()}")
        print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
        print()
        
        print("2. Price Analysis:")
        # Calculate daily returns
        df['Daily_Return'] = df.groupby('Symbol')['Close'].pct_change()
        
        # Get summary statistics
        summary_stats = df.groupby('Symbol')['Daily_Return'].describe()
        print("   Daily Return Statistics:")
        print(summary_stats)
        print()
        
        print("3. Volume Analysis:")
        if 'Volume' in df.columns:
            avg_volume = df.groupby('Symbol')['Volume'].mean()
            print("   Average Volume by Symbol:")
            for symbol, volume in avg_volume.items():
                print(f"     {symbol}: {volume:,.0f}")
        print()
        
        print("4. Price Trends:")
        # Get latest prices
        latest_prices = df.groupby('Symbol')['Close'].last()
        print("   Latest Prices:")
        for symbol, price in latest_prices.items():
            print(f"     {symbol}: ${price:.2f}")
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demonstrate_get_as_df()
    show_pipe_usage()
    demonstrate_data_processing() 