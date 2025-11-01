#!/usr/bin/env python3
"""
Test script to verify the new chunking functionality for TefasDownloader.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.etfs import TefasDownloader

def test_tefas_chunking():
    """Test the new chunking functionality."""
    print("Testing TefasDownloader Chunking Functionality")
    print("=" * 60)
    
    tefas_downloader = TefasDownloader()
    
    try:
        # Test 1: Specific fund (should use 30-day chunks)
        print("1. Testing specific fund (30-day chunks):")
        etf_data = tefas_downloader.download_fund_prices(
            funds="NNF",
            startDate="2024-01-01", 
            endDate="2024-01-31",
            kind="YAT"
        )
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {etf_data.shape}")
        if not etf_data.empty:
            print(f"   Columns: {list(etf_data.columns)}")
        else:
            print(f"   ⚠️  Empty DataFrame returned")
        print()
        
        # Test 2: All funds (should use 5-day chunks)
        print("2. Testing all funds (5-day chunks):")
        print("   This will take longer due to smaller chunks and delays...")
        etf_data = tefas_downloader.download_fund_prices(
            funds=None,  # This triggers all funds download
            startDate="2024-01-01", 
            endDate="2024-01-10",  # Short period for testing
            kind="YAT"
        )
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {etf_data.shape}")
        if not etf_data.empty:
            print(f"   Columns: {list(etf_data.columns)}")
            if 'symbol' in etf_data.columns:
                symbols = etf_data['symbol'].unique()
                print(f"   Number of unique symbols: {len(symbols)}")
                print(f"   Sample symbols: {symbols[:5]}")
        else:
            print(f"   ⚠️  Empty DataFrame returned")
        print()
        
        # Test 3: Multiple specific funds (should use 30-day chunks)
        print("3. Testing multiple specific funds (30-day chunks):")
        etf_data = tefas_downloader.download_fund_prices(
            funds=["NNF", "YAC"],
            startDate="2024-01-01", 
            endDate="2024-01-31",
            kind="YAT"
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
        
        # Test 4: All funds with longer period (should use 5-day chunks)
        print("4. Testing all funds with longer period (5-day chunks):")
        print("   This will demonstrate the chunking behavior...")
        etf_data = tefas_downloader.download_fund_prices(
            funds=None,  # All funds
            startDate="2024-01-01", 
            endDate="2024-01-15",  # 15 days = 3 chunks of 5 days each
            kind="YAT"
        )
        
        print(f"   ✅ Success!")
        print(f"   DataFrame shape: {etf_data.shape}")
        if not etf_data.empty:
            print(f"   Columns: {list(etf_data.columns)}")
            if 'date' in etf_data.columns:
                date_range = etf_data['date'].min(), etf_data['date'].max()
                print(f"   Date range: {date_range}")
        else:
            print(f"   ⚠️  Empty DataFrame returned")
        print()
        
        # Test 5: Different fund type with all funds
        print("5. Testing different fund type (BYF) with all funds:")
        etf_data = tefas_downloader.download_fund_prices(
            funds=None,  # All funds
            startDate="2024-01-01", 
            endDate="2024-01-05",  # Very short period for testing
            kind="BYF"
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

def test_chunking_comparison():
    """Compare the chunking behavior between specific funds and all funds."""
    print("\n" + "=" * 60)
    print("Chunking Behavior Comparison")
    print("=" * 60)
    
    tefas_downloader = TefasDownloader()
    
    try:
        # Test with same date range but different fund specifications
        start_date = "2024-01-01"
        end_date = "2024-01-10"
        
        print(f"Testing with date range: {start_date} to {end_date}")
        print()
        
        # Test specific fund (30-day chunks)
        print("A. Specific fund (should use 30-day chunks):")
        etf_data_specific = tefas_downloader.download_fund_prices(
            funds="NNF",
            startDate=start_date, 
            endDate=end_date,
            kind="YAT"
        )
        
        print(f"   Result shape: {etf_data_specific.shape}")
        print()
        
        # Test all funds (5-day chunks)
        print("B. All funds (should use 5-day chunks):")
        etf_data_all = tefas_downloader.download_fund_prices(
            funds=None,
            startDate=start_date, 
            endDate=end_date,
            kind="YAT"
        )
        
        print(f"   Result shape: {etf_data_all.shape}")
        print()
        
        # Compare results
        print("Comparison:")
        print(f"   Specific fund data shape: {etf_data_specific.shape}")
        print(f"   All funds data shape: {etf_data_all.shape}")
        
        if not etf_data_specific.empty and not etf_data_all.empty:
            print(f"   Specific fund unique symbols: {len(etf_data_specific['symbol'].unique())}")
            print(f"   All funds unique symbols: {len(etf_data_all['symbol'].unique())}")
        
        print()
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tefas_chunking()
    test_chunking_comparison() 