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
    
    # TEFAS subcommand for ETF data download/persist
    tefas_parser = subparsers.add_parser("tefas", help="Download and insert TEFAS ETF data into DB")
    tefas_parser.add_argument("start", help="Start date (YYYY-MM-DD)")
    tefas_parser.add_argument("end", help="End date (YYYY-MM-DD)")
    tefas_parser.add_argument("--funds", nargs="*", help="Optional fund codes (e.g., NNF NNFTR)")
    tefas_parser.add_argument("--kind", default="BYF", choices=["YAT", "EMK", "BYF"], help="Fund type")
    tefas_parser.add_argument("--db", help="Optional sqlite DB file path; overrides .env")
    tefas_parser.add_argument("--echo", action="store_true", help="Enable SQL echo for debugging")

    # ETF analysis subcommand
    analyze_parser = subparsers.add_parser(
        "etf-analyze", help="Analyze TEFAS ETF data from DB with technical indicators"
    )
    analyze_parser.add_argument("--funds", nargs="*", help="Fund codes to include (e.g., NNF YAC)")
    analyze_parser.add_argument("--start", type=str, help="Start date YYYY-MM-DD")
    analyze_parser.add_argument("--end", type=str, help="End date YYYY-MM-DD")
    analyze_parser.add_argument(
        "--column", type=str, default="price", help="Numeric column to analyze (default: price)"
    )
    analyze_parser.add_argument(
        "--include", nargs="*", default=None, help="Include keywords in title (case-insensitive by default)"
    )
    analyze_parser.add_argument(
        "--exclude", nargs="*", default=None, help="Exclude keywords in title (case-insensitive by default)"
    )
    analyze_parser.add_argument("--case-sensitive", action="store_true", help="Case sensitive keyword match")
    analyze_parser.add_argument(
        "--all-includes", action="store_true", help="Require all include keywords to match"
    )
    # Indicator selections
    analyze_parser.add_argument(
        "--ema", dest="ema_windows", nargs="*", type=int, default=None,
        help="EMA windows (space-separated). Example: --ema 20 50"
    )
    analyze_parser.add_argument(
        "--ema-cross", dest="ema_cross", nargs=2, type=int, default=None, metavar=("SHORT", "LONG"),
        help="EMA crossover (short long). Example: --ema-cross 20 50"
    )
    analyze_parser.add_argument("--rsi", type=int, default=None, help="RSI window (e.g., 14)")
    analyze_parser.add_argument(
        "--macd", nargs=3, type=int, default=None, metavar=("SLOW", "FAST", "SIGN"),
        help="MACD windows (slow fast sign). Example: --macd 26 12 9"
    )
    analyze_parser.add_argument("--db", help="Optional sqlite DB file path; overrides .env")
    analyze_parser.add_argument("--echo", action="store_true", help="Enable SQL echo for debugging")

    # ETF scan subcommand
    scan_parser = subparsers.add_parser(
        "etf-scan", help="Scan TEFAS ETFs and output buy/sell/hold suggestions"
    )
    scan_parser.add_argument("--funds", nargs="*", help="Fund codes to include (e.g., NNF YAC)")
    scan_parser.add_argument("--start", type=str, help="Start date YYYY-MM-DD")
    scan_parser.add_argument("--end", type=str, help="End date YYYY-MM-DD")
    scan_parser.add_argument("--column", type=str, default="price", help="Column to scan (default: price)")
    scan_parser.add_argument("--include", nargs="*", default=None, help="Include keywords in title")
    scan_parser.add_argument("--exclude", nargs="*", default=None, help="Exclude keywords in title")
    scan_parser.add_argument("--case-sensitive", action="store_true", help="Case sensitive keyword match")
    scan_parser.add_argument("--all-includes", action="store_true", help="Require all include keywords to match")
    # Indicator parameters for scanning
    scan_parser.add_argument("--ema-short", type=int, default=20, help="EMA short window (default: 20)")
    scan_parser.add_argument("--ema-long", type=int, default=50, help="EMA long window (default: 50)")
    scan_parser.add_argument(
        "--macd", nargs=3, type=int, default=[26, 12, 9], metavar=("SLOW", "FAST", "SIGN"),
        help="MACD params (default: 26 12 9)"
    )
    scan_parser.add_argument("--rsi", type=int, default=14, help="RSI window (default: 14)")
    scan_parser.add_argument("--rsi-lower", type=float, default=30.0, help="RSI lower threshold (default: 30)")
    scan_parser.add_argument("--rsi-upper", type=float, default=70.0, help="RSI upper threshold (default: 70)")
    # Weighted scan params
    scan_parser.add_argument("--w-ema", type=float, default=1.0, help="Weight for EMA crossover (default: 1.0)")
    scan_parser.add_argument("--w-macd", type=float, default=1.0, help="Weight for MACD (default: 1.0)")
    scan_parser.add_argument("--w-rsi", type=float, default=1.0, help="Weight for RSI (default: 1.0)")
    scan_parser.add_argument("--w-mom", type=float, default=1.0, help="Weight for momentum percent (default: 1.0)")
    scan_parser.add_argument("--w-mom-d", type=float, default=1.0, help="Weight for daily momentum (default: 1.0)")
    scan_parser.add_argument("--w-st", type=float, default=1.0, help="Weight for supertrend (default: 1.0)")
    scan_parser.add_argument("--buy-th", type=float, default=1.0, help="Score threshold for BUY (default: 1.0)")
    scan_parser.add_argument("--sell-th", type=float, default=1.0, help="Score threshold for SELL (default: 1.0)")
    # Enable/disable new indicators
    scan_parser.add_argument("--no-momentum", action="store_true", help="Disable momentum components")
    scan_parser.add_argument("--no-momentum-d", action="store_true", help="Disable daily momentum component")
    scan_parser.add_argument("--no-supertrend", action="store_true", help="Disable supertrend component")
    scan_parser.add_argument("--st-hl-factor", type=float, default=0.05, help="Supertrend synthetic HL factor (default: 0.05)")
    scan_parser.add_argument("--st-atr", type=int, default=10, help="Supertrend ATR period (default: 10)")
    scan_parser.add_argument("--st-mul", type=float, default=3.0, help="Supertrend multiplier (default: 3.0)")
    scan_parser.add_argument("--db", help="Optional sqlite DB file path; overrides .env")
    scan_parser.add_argument("--echo", action="store_true", help="Enable SQL echo for debugging")

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
        elif args.command == "tefas":
            handle_tefas(args)
        elif args.command == "etf-analyze":
            handle_etf_analyze(args)
        elif args.command == "etf-scan":
            handle_etf_scan(args)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def download_stock_data(args: argparse.Namespace) -> None:
    """Download stock data."""
    downloader = YFinanceDownloader()
    result = downloader.download(args.symbol, period=args.period)
    
    if args.output:
        result.data['data'].to_csv(args.output, index=True)
        print(f"Data saved to {args.output}")
    else:
        print(result.data['data'].head())
        print(f"\nShape: {result.data['data'].shape}")


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


def handle_tefas(args: argparse.Namespace) -> None:
    """Handle TEFAS data download and persistence via CLI."""
    from .etfs.tefas.service import TefasPersistenceService
    from .config import get_config
    from pathlib import Path
    import os

    cfg = get_config()

    if args.db:
        db_path = Path(args.db)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        os.environ["DATABASE_TYPE"] = "sqlite"
        os.environ["DATABASE_NAME"] = str(db_path)
        if args.echo:
            os.environ["DATABASE_ECHO"] = "true"
        cfg.reload()

    service = TefasPersistenceService()
    info_count, breakdown_count = service.download_and_persist(
        start_date=args.start,
        end_date=args.end,
        funds=args.funds,
        kind=args.kind,
    )
    print(f"Inserted/updated info rows: {info_count}")
    print(f"Inserted/updated breakdown rows: {breakdown_count}")


def handle_etf_analyze(args: argparse.Namespace) -> None:
    """Run ETF analysis on TEFAS data stored in the DB."""
    # Import here to avoid heavy imports when not used
    from .etfs.analysis import EtfAnalyzer, IndicatorRequest, KeywordFilter
    from datetime import datetime
    from .config import get_config
    import os
    from pathlib import Path

    # Allow DB override similar to tefas command
    cfg = get_config()
    if getattr(args, "db", None):
        db_path = Path(args.db)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        os.environ["DATABASE_TYPE"] = "sqlite"
        os.environ["DATABASE_NAME"] = str(db_path)
        if getattr(args, "echo", False):
            os.environ["DATABASE_ECHO"] = "true"
        cfg.reload()

    # Parse dates
    start = datetime.strptime(args.start, "%Y-%m-%d").date() if args.start else None
    end = datetime.strptime(args.end, "%Y-%m-%d").date() if args.end else None

    # Build indicators
    indicators = {}
    any_selected = any([
        args.ema_windows is not None and len(args.ema_windows) > 0,
        args.ema_cross is not None,
        args.rsi is not None,
        args.macd is not None,
    ])

    if any_selected:
        if args.ema_windows:
            indicators["ema"] = {"windows": [int(w) for w in args.ema_windows]}
        if args.ema_cross:
            short, long_ = args.ema_cross
            indicators["ema_cross"] = {"short": int(short), "long": int(long_)}
        if args.rsi:
            indicators["rsi"] = {"window": int(args.rsi)}
        if args.macd:
            slow, fast, sign = args.macd
            indicators["macd"] = {"window_slow": int(slow), "window_fast": int(fast), "window_sign": int(sign)}
    else:
        # Defaults: EMA-20, EMA-50, crossover(20,50), MACD(26,12,9)
        indicators = {
            "ema": {"windows": [20, 50]},
            "ema_cross": {"short": 20, "long": 50},
            "macd": {"window_slow": 26, "window_fast": 12, "window_sign": 9},
        }

    kf = KeywordFilter(
        include_keywords=args.include,
        exclude_keywords=args.exclude,
        case_sensitive=bool(args.case_sensitive),
        match_all_includes=bool(args.all_includes),
    )

    request = IndicatorRequest(
        codes=args.funds,
        start=start,
        end=end,
        column=args.column or "price",
        indicators=indicators,
        keyword_filter=kf,
    )

    analyzer = EtfAnalyzer()
    results = analyzer.analyze(request)
    if not results:
        print("No results.")
        return
    for r in results:
        print(f"Code: {r.code}")
        # Print last few rows to show computed columns
        print(r.data.tail())


def handle_etf_scan(args: argparse.Namespace) -> None:
    """Scan ETFs and print concise buy/sell/hold suggestions."""
    from .etfs.analysis import EtfAnalyzer, EtfScanner, EtfScanCriteria, KeywordFilter, IndicatorRequest
    from datetime import datetime
    from .config import get_config
    import os
    from pathlib import Path

    # DB override
    cfg = get_config()
    if getattr(args, "db", None):
        db_path = Path(args.db)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        os.environ["DATABASE_TYPE"] = "sqlite"
        os.environ["DATABASE_NAME"] = str(db_path)
        if getattr(args, "echo", False):
            os.environ["DATABASE_ECHO"] = "true"
        cfg.reload()

    # Dates
    start = datetime.strptime(args.start, "%Y-%m-%d").date() if args.start else None
    end = datetime.strptime(args.end, "%Y-%m-%d").date() if args.end else None

    # Retrieve data for the scan window and keywords
    analyzer = EtfAnalyzer()
    indicators = {
        "ema": {"windows": [args.ema_short, args.ema_long]},
        "ema_cross": {"short": args.ema_short, "long": args.ema_long},
        "macd": {"window_slow": int(args.macd[0]), "window_fast": int(args.macd[1]), "window_sign": int(args.macd[2])},
        "rsi": {"window": args.rsi},
    }
    if not args.no_momentum:
        indicators["momentum"] = {"windows": [30, 60, 90, 180, 360]}
    if not args.no_momentum_d:
        indicators["daily_momentum"] = {"windows": [30, 60, 90, 180, 360]}
    if not args.no_supertrend:
        indicators["supertrend"] = {"hl_factor": args.st_hl_factor, "atr_period": args.st_atr, "multiplier": args.st_mul}
    kf = KeywordFilter(
        include_keywords=args.include,
        exclude_keywords=args.exclude,
        case_sensitive=bool(args.case_sensitive),
        match_all_includes=bool(args.all_includes),
    )
    req = IndicatorRequest(codes=args.funds, start=start, end=end, column=args.column, indicators=indicators, keyword_filter=kf)
    results = analyzer.analyze(req)
    if not results:
        print("No results.")
        return

    # Build input for scanner and run
    code_to_df = {r.code: r.data for r in results}
    scanner = EtfScanner()
    criteria = EtfScanCriteria(
        column=args.column,
        ema_short=int(args.ema_short),
        ema_long=int(args.ema_long),
        macd_slow=int(args.macd[0]),
        macd_fast=int(args.macd[1]),
        macd_sign=int(args.macd[2]),
        rsi_window=int(args.rsi),
        rsi_lower=float(args.rsi_lower),
        rsi_upper=float(args.rsi_upper),
        w_ema_cross=float(args.w_ema),
        w_macd=float(args.w_macd),
        w_rsi=float(args.w_rsi),
        w_momentum=float(args.w_mom) if not args.no_momentum else 0.0,
        w_momentum_daily=float(args.w_mom_d) if not args.no_momentum_d else 0.0,
        w_supertrend=float(args.w_st) if not args.no_supertrend else 0.0,
        score_buy_threshold=float(args.buy_th),
        score_sell_threshold=float(args.sell_th),
    )
    scan_results = scanner.scan(code_to_df, criteria)
    for sr in scan_results:
        reasons = '; '.join(sr.suggestion.reasons)
        print(f"{sr.code}: {sr.suggestion.recommendation.upper()} [score={sr.score:.2f}] - {reasons}")


if __name__ == "__main__":
    main() 