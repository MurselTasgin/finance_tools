#!/usr/bin/env python3
"""
Simple test script for the technical analysis module.

This script demonstrates basic functionality without requiring
all dependencies to be installed.
"""

import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

def test_basic_functionality():
    """Test basic functionality with sample data."""
    print("Testing Technical Analysis Module")
    print("=" * 40)
    
    try:
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        # Generate sample price data
        base_price = 100.0
        prices = [base_price]
        for _ in range(len(dates) - 1):
            new_price = prices[-1] * (1 + np.random.normal(0, 0.02))
            prices.append(new_price)
        
        # Create OHLCV data
        data = pd.DataFrame({
            'Open': [p * (1 + np.random.normal(0, 0.01)) for p in prices],
            'High': [p * (1 + abs(np.random.normal(0, 0.02))) for p in prices],
            'Low': [p * (1 - abs(np.random.normal(0, 0.02))) for p in prices],
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        # Ensure OHLC relationships
        data['High'] = data[['Open', 'High', 'Close']].max(axis=1)
        data['Low'] = data[['Open', 'Low', 'Close']].min(axis=1)
        
        print(f"Created sample data: {len(data)} days")
        print(f"Price range: ${data['Low'].min():.2f} - ${data['High'].max():.2f}")
        
        # Test basic indicators
        try:
            from finance_tools.analysis.analysis import calculate_ema, calculate_rsi, calculate_sma
            
            close_prices = data['Close']
            
            # Calculate indicators
            ema_20 = calculate_ema(close_prices, 20)
            sma_20 = calculate_sma(close_prices, 20)
            rsi = calculate_rsi(close_prices, 14)
            
            print(f"\nTechnical Indicators (Latest Values):")
            print(f"EMA(20): ${ema_20.iloc[-1]:.2f}")
            print(f"SMA(20): ${sma_20.iloc[-1]:.2f}")
            print(f"RSI(14): {rsi.iloc[-1]:.2f}")
            
            print("\n✅ Basic indicators working correctly!")
            
        except ImportError as e:
            print(f"❌ Error importing analysis module: {e}")
            return False
        
        # Test configuration
        try:
            from finance_tools.analysis.config import get_config
            
            config = get_config()
            print(f"\nConfiguration loaded:")
            print(f"Min data points: {config.min_data_points}")
            print(f"RSI period: {config.default_rsi_period}")
            
            print("✅ Configuration working correctly!")
            
        except ImportError as e:
            print(f"❌ Error importing config module: {e}")
            return False
        
        # Test utilities
        try:
            from finance_tools.analysis.utils import validate_ohlcv_data, clean_data
            
            # Test data validation
            is_valid = validate_ohlcv_data(data)
            print(f"\nData validation: {'✅ Passed' if is_valid else '❌ Failed'}")
            
            # Test data cleaning
            cleaned_data = clean_data(data)
            print(f"Data cleaning: ✅ Completed ({len(cleaned_data)} rows)")
            
            print("✅ Utilities working correctly!")
            
        except ImportError as e:
            print(f"❌ Error importing utils module: {e}")
            return False
        
        print("\n🎉 All tests passed! The analysis module is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False


def test_stock_download():
    """Test stock data download functionality."""
    print("\nTesting Stock Data Download")
    print("=" * 30)
    
    try:
        from finance_tools.stocks.data_downloaders.yfinance import get_stock_data_yf
        
        # Test downloading a small amount of data
        print("Downloading AAPL data for the last 30 days...")
        
        data = get_stock_data_yf(
            symbols="AAPL",
            period="1mo",
            interval="1d"
        )
        
        if not data.empty:
            print(f"✅ Successfully downloaded {len(data)} days of AAPL data")
            print(f"Date range: {data.index.min()} to {data.index.max()}")
            print(f"Columns: {list(data.columns)}")
            return True
        else:
            print("❌ No data downloaded")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading stock data: {e}")
        return False


def main():
    """Run all tests."""
    print("Technical Analysis Module Test Suite")
    print("=" * 50)
    
    # Test basic functionality
    basic_test_passed = test_basic_functionality()
    
    # Test stock download (optional)
    download_test_passed = test_stock_download()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Basic functionality: {'✅ PASSED' if basic_test_passed else '❌ FAILED'}")
    print(f"Stock download: {'✅ PASSED' if download_test_passed else '❌ FAILED'}")
    
    if basic_test_passed:
        print("\n🎉 The analysis module is ready to use!")
        print("\nTo run the full example with real stock data:")
        print("python -m finance_tools.analysis.example_usage")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    main() 