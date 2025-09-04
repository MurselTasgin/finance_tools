#!/usr/bin/env python3
"""
Tefas Data Download Script

This script provides an easy way to download Turkish fund data from TEFAS.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.etfs.tefas import TefasDownloader

def download_tefas_data():
    """Download Tefas data with user-friendly interface."""
    print("🏦 Tefas Data Downloader")
    print("=" * 50)
    
    # Initialize the downloader
    downloader = TefasDownloader()
    
    # Get user input
    print("\n📋 Fund Types:")
    print("  YAT - Securities Mutual Funds")
    print("  EMK - Pension Funds") 
    print("  BYF - Exchange Traded Funds")
    
    fund_type = input("\nEnter fund type (YAT/EMK/BYF) [YAT]: ").strip().upper() or "YAT"
    
    if fund_type not in ["YAT", "EMK", "BYF"]:
        print("❌ Invalid fund type. Using YAT as default.")
        fund_type = "YAT"
    
    # Get date range
    print(f"\n📅 Date Range for {fund_type} funds:")
    start_date = input("Start date (YYYY-MM-DD) [2024-01-01]: ").strip() or "2024-01-01"
    end_date = input("End date (YYYY-MM-DD) [2024-12-31]: ").strip() or "2024-12-31"
    
    # Get fund selection
    print(f"\n🎯 Fund Selection:")
    print("  - Enter specific fund code(s) separated by commas (e.g., NNF,YAC)")
    print("  - Leave empty to download ALL funds (this may take a while)")
    
    fund_input = input("Fund codes (comma-separated) or press Enter for all: ").strip()
    
    if fund_input:
        funds = [f.strip().upper() for f in fund_input.split(",")]
        print(f"📊 Will download data for: {', '.join(funds)}")
    else:
        funds = None
        print("📊 Will download data for ALL funds")
    
    # Get column selection
    print(f"\n📋 Available columns:")
    print("  date, code, price, number_of_shares, stock, bond, precious_metals, private_sector_bond")
    print("  foreign_security, money_market, other, total")
    
    column_input = input("Columns (comma-separated) or press Enter for all: ").strip()
    
    if column_input:
        columns = [c.strip() for c in column_input.split(",")]
        print(f"📊 Will include columns: {', '.join(columns)}")
    else:
        columns = None
        print("📊 Will include all columns")
    
    # Confirm and download
    print(f"\n🚀 Starting download...")
    print(f"   Fund Type: {fund_type}")
    print(f"   Date Range: {start_date} to {end_date}")
    print(f"   Funds: {', '.join(funds) if funds else 'ALL'}")
    print(f"   Columns: {', '.join(columns) if columns else 'ALL'}")
    
    try:
        # Download the data
        data = downloader.download_fund_prices(
            funds=funds,
            startDate=start_date,
            endDate=end_date,
            columns=columns,
            kind=fund_type
        )
        
        if not data.empty:
            print(f"\n✅ Download completed successfully!")
            print(f"   Total records: {len(data)}")
            print(f"   Date range: {data['date'].min()} to {data['date'].max()}")
            print(f"   Unique funds: {data['symbol'].nunique() if 'symbol' in data.columns else data['code'].nunique()}")
            
            # Show sample data
            print(f"\n📈 Sample Data:")
            print(data.head(10))
            
            # Ask if user wants to save
            save_option = input(f"\n💾 Save to CSV? (y/n) [y]: ").strip().lower() or "y"
            
            if save_option == "y":
                filename = f"tefas_{fund_type}_{start_date}_{end_date}.csv"
                data.to_csv(filename, index=False)
                print(f"💾 Data saved to: {filename}")
            
            # Ask if user wants to see statistics
            stats_option = input(f"\n📊 Show statistics? (y/n) [y]: ").strip().lower() or "y"
            
            if stats_option == "y":
                print(f"\n📊 Data Statistics:")
                print(f"   Shape: {data.shape}")
                print(f"   Columns: {list(data.columns)}")
                
                if 'price' in data.columns:
                    print(f"   Price range: {data['price'].min():.4f} - {data['price'].max():.4f}")
                
                if 'symbol' in data.columns:
                    print(f"   Funds included: {sorted(data['symbol'].unique())}")
                elif 'code' in data.columns:
                    print(f"   Funds included: {sorted(data['code'].unique())}")
                
                print(f"\n📅 Date distribution:")
                date_counts = data['date'].value_counts().sort_index()
                print(f"   First 5 dates: {date_counts.head().to_dict()}")
                print(f"   Last 5 dates: {date_counts.tail().to_dict()}")
        else:
            print("❌ No data was downloaded. Please check your parameters.")
            
    except Exception as e:
        print(f"❌ Error during download: {e}")
        import traceback
        traceback.print_exc()

def quick_download_examples():
    """Show quick download examples."""
    print("\n🚀 Quick Download Examples:")
    print("=" * 50)
    
    downloader = TefasDownloader()
    
    # Example 1: Single fund
    print("\n1. Single Fund (NNF):")
    try:
        data = downloader.download_fund_prices(
            funds="NNF",
            startDate="2024-01-01",
            endDate="2024-01-31",
            kind="YAT"
        )
        print(f"   ✅ Downloaded {len(data)} records")
        if not data.empty:
            print(f"   Sample: {data.head(2).to_string()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Example 2: Multiple funds
    print("\n2. Multiple Funds (NNF, YAC):")
    try:
        data = downloader.download_fund_prices(
            funds=["NNF", "YAC"],
            startDate="2024-01-01",
            endDate="2024-01-31",
            kind="YAT"
        )
        print(f"   ✅ Downloaded {len(data)} records")
        if not data.empty:
            print(f"   Funds: {data['symbol'].unique()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Example 3: All funds (small date range)
    print("\n3. All Funds (1 week):")
    try:
        data = downloader.download_fund_prices(
            funds=None,
            startDate="2024-01-01",
            endDate="2024-01-07",
            kind="YAT"
        )
        print(f"   ✅ Downloaded {len(data)} records")
        if not data.empty:
            print(f"   Unique funds: {data['symbol'].nunique()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Interactive download")
    print("2. Quick examples")
    
    choice = input("Enter choice (1/2) [1]: ").strip() or "1"
    
    if choice == "1":
        download_tefas_data()
    elif choice == "2":
        quick_download_examples()
    else:
        print("Invalid choice. Running interactive download...")
        download_tefas_data()

