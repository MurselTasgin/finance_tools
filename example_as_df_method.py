#!/usr/bin/env python3
"""
Example showing how to use the as_df() method on download results.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.stocks.data_downloaders import YFinanceDownloader
import pandas as pd

def demonstrate_as_df_method():
    """Demonstrate the as_df() method usage."""
    print("Demonstrating as_df() Method")
    print("=" * 50)
    
    # Initialize the downloader
    downloader = YFinanceDownloader()
    
    try:
        # Example 1: Single stock with as_df()
        print("1. Single Stock with as_df():")
        result = downloader.execute(symbols=["AAPL"], period="1mo")
        df = result.as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   First few rows:")
        print(df.head(3))
        print()
        
        # Example 2: Multiple stocks with as_df()
        print("2. Multiple Stocks with as_df():")
        result = downloader.execute(symbols=["AAPL", "MSFT", "GOOGL"], period="1mo")
        df = result.as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Symbols: {df['Symbol'].unique()}")
        print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
        print()
        
        # Example 3: Chain operations with as_df()
        print("3. Chain Operations with as_df():")
        df = downloader.execute(symbols=["AAPL", "MSFT"], period="1mo").as_df()
        
        # Filter by date
        recent_data = df[df['Date'] >= '2024-01-15']
        print(f"   Recent data shape: {recent_data.shape}")
        
        # Group by symbol and get latest prices
        latest_prices = recent_data.groupby('Symbol')['Close'].last()
        print(f"   Latest prices:")
        for symbol, price in latest_prices.items():
            print(f"     {symbol}: ${price:.2f}")
        print()
        
        # Example 4: Data analysis with as_df()
        print("4. Data Analysis with as_df():")
        df = downloader.execute(symbols=["AAPL", "MSFT", "GOOGL"], period="1mo").as_df()
        
        # Calculate daily returns
        df['Daily_Return'] = df.groupby('Symbol')['Close'].pct_change()
        
        # Get summary statistics
        summary_stats = df.groupby('Symbol')['Daily_Return'].describe()
        print("   Daily Return Statistics:")
        print(summary_stats)
        print()
        
        # Example 5: Error handling
        print("5. Error Handling:")
        try:
            # This should work
            df = downloader.execute(symbols=["AAPL"], period="1mo").as_df()
            print(f"   ✅ Success: DataFrame shape {df.shape}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()
        
        # Example 6: Comparison with get_as_df function
        print("6. Comparison with get_as_df function:")
        result = downloader.execute(symbols=["AAPL", "MSFT"], period="1mo")
        
        # Method 1: Using as_df() method
        df1 = result.as_df()
        
        # Method 2: Using get_as_df function
        from finance_tools.utils.dataframe_utils import get_as_df
        df2 = get_as_df(result)
        
        # Both should be identical
        if df1.equals(df2):
            print("   ✅ Both methods return identical results!")
            print(f"   DataFrame shape: {df1.shape}")
        else:
            print("   ❌ Results differ between methods")
        print()
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

def show_advanced_usage():
    """Show advanced usage patterns."""
    print("\n" + "=" * 50)
    print("Advanced Usage Patterns")
    print("=" * 50)
    
    downloader = YFinanceDownloader()
    
    try:
        # Pattern 1: One-liner download and analysis
        print("1. One-liner download and analysis:")
        latest_prices = (
            downloader.execute(symbols=["AAPL", "MSFT", "GOOGL"], period="1mo")
            .as_df()
            .groupby('Symbol')['Close']
            .last()
        )
        print(f"   Latest prices: {latest_prices.to_dict()}")
        print()
        
        # Pattern 2: Filtering and processing
        print("2. Filtering and processing:")
        recent_data = (
            downloader.execute(symbols=["AAPL", "MSFT"], period="1mo")
            .as_df()
            .query("Date >= '2024-01-15'")
        )
        print(f"   Recent data shape: {recent_data.shape}")
        print(f"   Date range: {recent_data['Date'].min()} to {recent_data['Date'].max()}")
        print()
        
        # Pattern 3: Multiple operations
        print("3. Multiple operations:")
        df = downloader.execute(symbols=["AAPL", "MSFT"], period="1mo").as_df()
        
        # Calculate moving averages
        df['MA_5'] = df.groupby('Symbol')['Close'].rolling(5).mean().reset_index(0, drop=True)
        df['MA_10'] = df.groupby('Symbol')['Close'].rolling(10).mean().reset_index(0, drop=True)
        
        # Get latest values
        latest_data = df.groupby('Symbol').tail(1)
        print("   Latest data with moving averages:")
        for _, row in latest_data.iterrows():
            print(f"     {row['Symbol']}: Close=${row['Close']:.2f}, MA5=${row['MA_5']:.2f}, MA10=${row['MA_10']:.2f}")
        print()
        
        # Pattern 4: Error handling with try/except
        print("4. Error handling:")
        try:
            df = downloader.execute(symbols=["INVALID_SYMBOL"], period="1mo").as_df()
            print("   ✅ Should not reach here")
        except Exception as e:
            print(f"   ✅ Correctly caught error: {str(e)[:50]}...")
        print()
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demonstrate_as_df_method()
    show_advanced_usage() 