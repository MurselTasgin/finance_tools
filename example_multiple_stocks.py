#!/usr/bin/env python3
"""
Example: Download multiple stocks data using finance-tools.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.stocks.data_downloaders import YFinanceDownloader

def main():
    """Main example function."""
    print("Finance Tools - Multiple Stocks Download Example")
    print("=" * 50)
    
    # Initialize the downloader
    downloader = YFinanceDownloader()
    
    # Define symbols to download
    symbols = ["AAPL", "MSFT", "GOOGL"]
    
    print(f"Downloading data for: {', '.join(symbols)}")
    print(f"Period: Last 1 month")
    print()
    
    try:
        # Execute the download
        result = downloader.execute(
            symbols=symbols,
            period="1mo",
            interval="1d",
            include_dividends=False,
            include_splits=False,
            auto_adjust=True,
            format_type="dataframe"
        )
        
        if result.success:
            print("✅ Download successful!")
            print()
            
            # Get the data from the result dictionary
            price_data = result.data['data']
            
            print(f"📊 Data Summary:")
            print(f"   Shape: {price_data.shape}")
            print(f"   Columns: {list(price_data.columns)}")
            print(f"   Symbols: {price_data['Symbol'].unique()}")
            print(f"   Date range: {price_data.index.min().strftime('%Y-%m-%d')} to {price_data.index.max().strftime('%Y-%m-%d')}")
            print()
            
            # Show sample data
            print("📈 Sample Data:")
            print(price_data.head(10))
            print()
            
            # Show data by symbol
            print("📋 Data by Symbol:")
            for symbol in symbols:
                symbol_data = price_data[price_data['Symbol'] == symbol]
                if not symbol_data.empty:
                    print(f"   {symbol}: {len(symbol_data)} rows")
                    print(f"      Latest Close: ${symbol_data['Close'].iloc[-1]:.2f}")
                    print(f"      Date range: {symbol_data.index.min().strftime('%Y-%m-%d')} to {symbol_data.index.max().strftime('%Y-%m-%d')}")
                else:
                    print(f"   {symbol}: No data available")
                print()
            
        else:
            print("❌ Download failed!")
            print(f"Error: {result.error}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 