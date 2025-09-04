#!/usr/bin/env python3
"""
Tefas CLI - Command line interface for downloading Tefas data
"""

import argparse
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance_tools.etfs.tefas import TefasDownloader

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Download Turkish fund data from TEFAS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download specific fund
  python tefas_cli.py --fund NNF --start 2024-01-01 --end 2024-12-31
  
  # Download multiple funds
  python tefas_cli.py --fund NNF,YAC --start 2024-01-01 --end 2024-12-31
  
  # Download all funds (ETF type)
  python tefas_cli.py --type BYF --start 2024-01-01 --end 2024-01-31 --all
  
  # Download with specific columns
  python tefas_cli.py --fund NNF --start 2024-01-01 --end 2024-12-31 --columns date,code,price,stock
        """
    )
    
    parser.add_argument("--fund", "-f", 
                       help="Fund code(s) - comma-separated for multiple funds")
    parser.add_argument("--start", "-s", 
                       default=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                       help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", "-e", 
                       default=datetime.now().strftime("%Y-%m-%d"),
                       help="End date (YYYY-MM-DD)")
    parser.add_argument("--type", "-t", 
                       choices=["YAT", "EMK", "BYF"], 
                       default="YAT",
                       help="Fund type: YAT (Securities), EMK (Pension), BYF (ETF)")
    parser.add_argument("--columns", "-c", 
                       help="Columns to include (comma-separated)")
    parser.add_argument("--all", "-a", 
                       action="store_true",
                       help="Download all funds of the specified type")
    parser.add_argument("--output", "-o", 
                       help="Output CSV file path")
    parser.add_argument("--verbose", "-v", 
                       action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.fund and not args.all:
        print("❌ Error: Must specify either --fund or --all")
        sys.exit(1)
    
    if args.fund and args.all:
        print("❌ Error: Cannot specify both --fund and --all")
        sys.exit(1)
    
    # Parse fund codes
    funds = None
    if args.fund:
        funds = [f.strip().upper() for f in args.fund.split(",")]
    
    # Parse columns
    columns = None
    if args.columns:
        columns = [c.strip() for c in args.columns.split(",")]
    
    # Initialize downloader
    downloader = TefasDownloader()
    
    # Generate output filename if not provided
    if not args.output:
        if funds:
            fund_str = "_".join(funds)
        else:
            fund_str = "all"
        args.output = f"tefas_{args.type}_{fund_str}_{args.start}_{args.end}.csv"
    
    print(f"🏦 Tefas Data Download")
    print(f"   Type: {args.type}")
    print(f"   Date Range: {args.start} to {args.end}")
    print(f"   Funds: {', '.join(funds) if funds else 'ALL'}")
    print(f"   Output: {args.output}")
    print()
    
    try:
        # Download data
        data = downloader.download_fund_prices(
            funds=funds,
            startDate=args.start,
            endDate=args.end,
            columns=columns,
            kind=args.type
        )
        
        if data.empty:
            print("❌ No data downloaded")
            sys.exit(1)
        
        # Save to CSV
        data.to_csv(args.output, index=False)
        
        print(f"✅ Successfully downloaded {len(data)} records")
        print(f"   Saved to: {args.output}")
        
        if args.verbose:
            print(f"\n📊 Data Summary:")
            print(f"   Shape: {data.shape}")
            print(f"   Columns: {list(data.columns)}")
            print(f"   Date range: {data['date'].min()} to {data['date'].max()}")
            
            if 'symbol' in data.columns:
                print(f"   Funds: {sorted(data['symbol'].unique())}")
            elif 'code' in data.columns:
                print(f"   Funds: {sorted(data['code'].unique())}")
            
            print(f"\n📈 Sample Data:")
            print(data.head())
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
