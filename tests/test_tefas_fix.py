#!/usr/bin/env python3
"""
Test script to verify the TefasDownloader fix.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.etfs import TefasDownloader

def test_tefas_downloader():
    """Test the fixed TefasDownloader."""
    print("Testing TefasDownloader Fix")
    print("=" * 50)
    
    tefas_downloader = TefasDownloader()
    
    # Test parameters
    fund_type = "YAT"
    start_date = "2024-01-01"  # Use a more recent date
    end_date = "2024-01-31"
    fund_name = "NNF"
    
    try:
        print(f"Testing with parameters:")
        print(f"  Fund name: {fund_name}")
        print(f"  Fund type: {fund_type}")
        print(f"  Start date: {start_date}")
        print(f"  End date: {end_date}")
        print()
        
        # Test 1: Single fund as string
        print("1. Testing single fund as string:")
        etf_data = tefas_downloader.download_fund_prices(
            funds=fund_name, 
            startDate=start_date, 
            endDate=end_date, 
            columns=None, 
            kind=fund_type
        )
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {etf_data.shape}")
        if not etf_data.empty:
            print(f"   Columns: {list(etf_data.columns)}")
            print(f"   Sample data:")
            print(etf_data.head())
        else:
            print(f"   ⚠️  Empty DataFrame returned")
        print()
        
        # Test 2: Single fund as list
        print("2. Testing single fund as list:")
        etf_data = tefas_downloader.download_fund_prices(
            funds=[fund_name], 
            startDate=start_date, 
            endDate=end_date, 
            columns=None, 
            kind=fund_type
        )
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {etf_data.shape}")
        if not etf_data.empty:
            print(f"   Columns: {list(etf_data.columns)}")
        else:
            print(f"   ⚠️  Empty DataFrame returned")
        print()
        
        # Test 3: Multiple funds
        print("3. Testing multiple funds:")
        etf_data = tefas_downloader.download_fund_prices(
            funds=["NNF", "YAC"], 
            startDate=start_date, 
            endDate=end_date, 
            columns=None, 
            kind=fund_type
        )
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {etf_data.shape}")
        if not etf_data.empty:
            print(f"   Columns: {list(etf_data.columns)}")
            if 'symbol' in etf_data.columns:
                symbols = etf_data['symbol'].unique()
                print(f"   Symbols found: {symbols}")
        else:
            print(f"   ⚠️  Empty DataFrame returned")
        print()
        
        # Test 4: Specific columns
        print("4. Testing with specific columns:")
        etf_data = tefas_downloader.download_fund_prices(
            funds=fund_name, 
            startDate=start_date, 
            endDate=end_date, 
            columns=["date", "code", "price"], 
            kind=fund_type
        )
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {etf_data.shape}")
        if not etf_data.empty:
            print(f"   Columns: {list(etf_data.columns)}")
            print(f"   Sample data:")
            print(etf_data.head())
        else:
            print(f"   ⚠️  Empty DataFrame returned")
        print()
        
        # Test 5: Different fund type
        print("5. Testing different fund type (BYF):")
        etf_data = tefas_downloader.download_fund_prices(
            funds=fund_name, 
            startDate=start_date, 
            endDate=end_date, 
            columns=None, 
            kind="BYF"
        )
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {etf_data.shape}")
        if not etf_data.empty:
            print(f"   Columns: {list(etf_data.columns)}")
        else:
            print(f"   ⚠️  Empty DataFrame returned")
        print()
        
        # Test 6: Short date range
        print("6. Testing short date range:")
        etf_data = tefas_downloader.download_fund_prices(
            funds=fund_name, 
            startDate="2024-01-15", 
            endDate="2024-01-20", 
            columns=None, 
            kind=fund_type
        )
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {etf_data.shape}")
        if not etf_data.empty:
            print(f"   Columns: {list(etf_data.columns)}")
        else:
            print(f"   ⚠️  Empty DataFrame returned")
        print()
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

def test_crawler_direct():
    """Test the crawler directly to compare."""
    print("\n" + "=" * 50)
    print("Testing Crawler Directly")
    print("=" * 50)
    
    from finance_tools.etfs.tefas.crawler import Crawler
    
    crawler = Crawler()
    
    try:
        print("Testing crawler.fetch directly:")
        
        # Test direct crawler call
        data = crawler.fetch(
            start="2024-01-01",
            end="2024-01-31",
            name="NNF",
            kind="YAT"
        )
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {data.shape}")
        if not data.empty:
            print(f"   Columns: {list(data.columns)}")
            print(f"   Sample data:")
            print(data.head())
        else:
            print(f"   ⚠️  Empty DataFrame returned")
        print()
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tefas_downloader()
    test_crawler_direct() 