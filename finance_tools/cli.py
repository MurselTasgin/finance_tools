# finance_tools/cli.py
"""
Command-line interface for finance-tools.

This module provides a CLI for accessing finance-tools functionality
from the command line.
"""

import argparse
import sys
from typing import Optional

from .stocks.data_downloaders import YFinanceDownloader, FinancialNewsDownloader


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Finance Tools - A comprehensive financial analysis toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  finance-tools stock-data AAPL --period 1y
  finance-tools news AAPL --limit 10
  finance-tools technical AAPL --indicators RSI,MACD
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Stock data command
    stock_parser = subparsers.add_parser("stock-data", help="Download stock data")
    stock_parser.add_argument("symbol", help="Stock symbol (e.g., AAPL)")
    stock_parser.add_argument("--period", default="1y", help="Data period (e.g., 1d, 1w, 1m, 1y)")
    stock_parser.add_argument("--output", help="Output file path (CSV)")
    
    # News command
    news_parser = subparsers.add_parser("news", help="Get financial news")
    news_parser.add_argument("symbol", help="Stock symbol (e.g., AAPL)")
    news_parser.add_argument("--limit", type=int, default=10, help="Number of news articles")
    news_parser.add_argument("--output", help="Output file path (JSON)")
    
    # Technical analysis command
    tech_parser = subparsers.add_parser("technical", help="Technical analysis")
    tech_parser.add_argument("symbol", help="Stock symbol (e.g., AAPL)")
    tech_parser.add_argument("--indicators", help="Comma-separated indicators (e.g., RSI,MACD,BB)")
    tech_parser.add_argument("--period", default="1y", help="Data period")
    tech_parser.add_argument("--output", help="Output file path (CSV)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "stock-data":
            download_stock_data(args)
        elif args.command == "news":
            download_news(args)
        elif args.command == "technical":
            perform_technical_analysis(args)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def download_stock_data(args: argparse.Namespace) -> None:
    """Download stock data."""
    downloader = YFinanceDownloader()
    data = downloader.download_data(args.symbol, period=args.period)
    
    if args.output:
        data.to_csv(args.output, index=True)
        print(f"Data saved to {args.output}")
    else:
        print(data.head())
        print(f"\nShape: {data.shape}")


def download_news(args: argparse.Namespace) -> None:
    """Download financial news."""
    downloader = FinancialNewsDownloader()
    news = downloader.get_news(args.symbol, limit=args.limit)
    
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(news, f, indent=2)
        print(f"News saved to {args.output}")
    else:
        for i, article in enumerate(news, 1):
            print(f"{i}. {article.get('title', 'No title')}")
            print(f"   {article.get('url', 'No URL')}")
            print()


def perform_technical_analysis(args: argparse.Namespace) -> None:
    """Perform technical analysis."""
    from .stocks.data_downloaders import TechnicalAnalysisDownloader
    
    downloader = TechnicalAnalysisDownloader()
    indicators = args.indicators.split(",") if args.indicators else ["RSI", "MACD"]
    
    data = downloader.analyze_technical_indicators(
        args.symbol, 
        indicators=indicators,
        period=args.period
    )
    
    if args.output:
        data.to_csv(args.output, index=True)
        print(f"Technical analysis saved to {args.output}")
    else:
        print(data.tail())


if __name__ == "__main__":
    main() 