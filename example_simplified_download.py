#!/usr/bin/env python3
"""
Example showing how to use the simplified download function with various input formats.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.stocks.data_downloaders import YFinanceDownloader
import pandas as pd

def demonstrate_simplified_download():
    """Demonstrate the simplified download function with various input formats."""
    print("Demonstrating Simplified Download Function")
    print("=" * 60)
    
    # Initialize the downloader
    yf_tool = YFinanceDownloader()
    
    try:
        # Example 1: Single stock as string
        print("1. Single stock as string:")
        result = yf_tool.download("AAPL", period="1mo")
        df = result.as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Metadata keys: {list(result.metadata.keys())}")
        print()
        
        # Example 2: Multiple stocks as comma-separated string
        print("2. Multiple stocks as comma-separated string:")
        result = yf_tool.download("AAPL, MSFT, GOOGL", period="1mo")
        df = result.as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Symbols: {df['Symbol'].unique()}")
        print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
        print()
        
        # Example 3: Single stock as list
        print("3. Single stock as list:")
        result = yf_tool.download(["AAPL"], period="1mo")
        df = result.as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print()
        
        # Example 4: Multiple stocks as list
        print("4. Multiple stocks as list:")
        result = yf_tool.download(["AAPL", "MSFT", "GOOGL"], period="1mo")
        df = result.as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Symbols: {df['Symbol'].unique()}")
        print()
        
        # Example 5: Using as_df() method
        print("5. Using as_df() method:")
        df = yf_tool.download("AAPL, MSFT").as_df()
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Latest prices:")
        latest_prices = df.groupby('Symbol')['Close'].last()
        for symbol, price in latest_prices.items():
            print(f"     {symbol}: ${price:.2f}")
        print()
        
        # Example 6: Accessing metadata
        print("6. Accessing metadata:")
        result = yf_tool.download("AAPL", period="1mo")
        
        print(f"   Execution time: {result.metadata.get('execution_time', 'N/A'):.2f} seconds")
        print(f"   Symbols requested: {result.metadata.get('symbols_requested', [])}")
        print(f"   Period: {result.metadata.get('period', 'N/A')}")
        print(f"   Interval: {result.metadata.get('interval', 'N/A')}")
        print()
        
        # Example 7: Error handling
        print("7. Error handling:")
        try:
            result = yf_tool.download("INVALID_SYMBOL_12345", period="1mo")
            if result.metadata.get('error'):
                print(f"   ✅ Correctly caught error: {result.metadata['error']}")
            else:
                print("   ❌ Should have caught error")
        except Exception as e:
            print(f"   ✅ Exception caught: {e}")
        print()
        
        # Example 8: Chain operations
        print("8. Chain operations:")
        df = yf_tool.download("AAPL, MSFT", period="1mo").as_df()
        
        # Filter by date
        recent_data = df[df['Date'] >= '2024-01-15']
        print(f"   Recent data shape: {recent_data.shape}")
        
        # Calculate returns
        recent_data['Daily_Return'] = recent_data.groupby('Symbol')['Close'].pct_change()
        avg_returns = recent_data.groupby('Symbol')['Daily_Return'].mean()
        print(f"   Average daily returns:")
        for symbol, ret in avg_returns.items():
            print(f"     {symbol}: {ret:.4f}")
        print()
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

def show_various_input_formats():
    """Show various input formats that work with the download function."""
    print("\n" + "=" * 60)
    print("Various Input Formats")
    print("=" * 60)
    
    yf_tool = YFinanceDownloader()
    
    # Test different input formats
    test_cases = [
        ("Single string", "AAPL"),
        ("Comma-separated string", "AAPL, MSFT"),
        ("Single list", ["AAPL"]),
        ("Multiple list", ["AAPL", "MSFT", "GOOGL"]),
        ("Mixed case", "aapl, MSFT, googl"),
        ("With spaces", " AAPL , MSFT , GOOGL "),
    ]
    
    for test_name, symbols in test_cases:
        try:
            print(f"Testing: {test_name}")
            result = yf_tool.download(symbols, period="1mo")
            df = result.as_df()
            
            print(f"   ✅ Success!")
            print(f"   Input: {symbols}")
            print(f"   Parsed symbols: {result.metadata.get('symbols_requested', [])}")
            print(f"   DataFrame shape: {df.shape}")
            if 'Symbol' in df.columns:
                print(f"   Symbols in data: {df['Symbol'].unique()}")
            print()
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            print()

def demonstrate_advanced_usage():
    """Demonstrate advanced usage patterns."""
    print("\n" + "=" * 60)
    print("Advanced Usage Patterns")
    print("=" * 60)
    
    yf_tool = YFinanceDownloader()
    
    try:
        # Pattern 1: One-liner with custom parameters
        print("1. One-liner with custom parameters:")
        df = yf_tool.download(
            symbols="AAPL, MSFT, GOOGL",
            period="1mo",
            interval="1d",
            include_dividends=True,
            auto_adjust=True
        ).as_df()
        
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        print()
        
        # Pattern 2: Date range download
        print("2. Date range download:")
        df = yf_tool.download(
            symbols=["AAPL", "MSFT"],
            start_date="2024-01-01",
            end_date="2024-01-31"
        ).as_df()
        
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
        print()
        
        # Pattern 3: Data analysis
        print("3. Data analysis:")
        result = yf_tool.download("AAPL, MSFT, GOOGL", period="1mo")
        df = result.as_df()
        
        # Calculate statistics
        stats = df.groupby('Symbol')['Close'].agg(['mean', 'std', 'min', 'max'])
        print("   Price Statistics:")
        print(stats)
        print()
        
        # Pattern 4: Error handling with try/except
        print("4. Error handling:")
        try:
            result = yf_tool.download("INVALID", period="1mo")
            if result.metadata.get('error'):
                print(f"   ✅ Error handled: {result.metadata['error']}")
            else:
                print("   ❌ Should have error")
        except Exception as e:
            print(f"   ✅ Exception caught: {e}")
        print()
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demonstrate_simplified_download()
    show_various_input_formats()
    demonstrate_advanced_usage() 