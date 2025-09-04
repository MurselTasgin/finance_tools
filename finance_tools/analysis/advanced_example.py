# finance_tools/analysis/advanced_example.py
"""
Advanced example demonstrating all the new modules:
- Signals (EMA crossovers, RSI signals, etc.)
- Patterns (Chart patterns, candlestick patterns, breakouts)
- Suggestions (Buy/sell/hold recommendations)
- Scanner (Stock scanning for opportunities)
- Portfolio (Optimization and suggestions)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os

# Add the parent directory to the path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import all modules
try:
    from finance_tools.analysis.signals import SignalCalculator, calculate_ema_crossover_signals
    from finance_tools.analysis.patterns import PatternDetector, detect_chart_patterns
    from finance_tools.analysis.suggestions import SuggestionEngine, generate_trading_suggestions
    from finance_tools.analysis.scanner import StockScanner, scan_for_signals, scan_for_breakouts
    from finance_tools.analysis.portfolio import PortfolioOptimizer, PortfolioSuggester
    from finance_tools.stocks.data_downloaders.yfinance import get_stock_data_yf
except ImportError:
    # Fallback to relative imports
    from .signals import SignalCalculator, calculate_ema_crossover_signals
    from .patterns import PatternDetector, detect_chart_patterns
    from .suggestions import SuggestionEngine, generate_trading_suggestions
    from .scanner import StockScanner, scan_for_signals, scan_for_breakouts
    from .portfolio import PortfolioOptimizer, PortfolioSuggester
    from ..stocks.data_downloaders.yfinance import get_stock_data_yf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure the DataFrame uses a DatetimeIndex based on 'Date' column if present."""
    if df is None or df.empty:
        return df
    # Prefer 'Date' column if available (downloader formats this)
    if 'Date' in df.columns:
        df = df.copy()
        try:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
        except Exception:
            # Best-effort; leave as-is if conversion fails
            pass
        return df
    # If no 'Date' column, try to convert index
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df = df.copy()
            df.index = pd.to_datetime(df.index)
        except Exception:
            pass
    return df


def download_multiple_stocks(symbols: list, period: str = "6mo") -> dict:
    """Download data for multiple stocks."""
    stock_data = {}
    
    for symbol in symbols:
        try:
            print(f"Downloading data for {symbol}...")
            data = get_stock_data_yf(symbols=symbol, period=period, interval="1d")
            
            if not data.empty:
                # Handle column names
                if 'Open' in data.columns:
                    data = data.rename(columns={
                        'Open': 'open', 'High': 'high', 'Low': 'low',
                        'Close': 'close', 'Volume': 'volume'
                    })
                
                stock_data[symbol] = _ensure_datetime_index(data)
                print(f"✅ Downloaded {len(data)} days of {symbol} data")
            else:
                print(f"❌ No data for {symbol}")
                
        except Exception as e:
            print(f"❌ Error downloading {symbol}: {e}")
    
    return stock_data


def example_signals_analysis():
    """Example of signals analysis."""
    print("\n" + "="*60)
    print("SIGNALS ANALYSIS EXAMPLE")
    print("="*60)
    
    # Download data for a single stock
    symbol = "AAPL"
    data = get_stock_data_yf(symbols=symbol, period="6mo", interval="1d")
    
    if 'Open' in data.columns:
        data = data.rename(columns={
            'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume'
        })
    
    # Ensure datetime index for correct timestamp handling in signals
    data = _ensure_datetime_index(data)

    # Initialize signal calculator
    signal_calculator = SignalCalculator()
    
    # Calculate all signals
    print(f"\nCalculating signals for {symbol}...")
    signals_result = signal_calculator.calculate_all_signals(data)
    
    print(f"\n📊 Signal Analysis Results for {symbol}:")
    print(f"Total signals: {signals_result.summary['total_signals']}")
    print(f"Buy signals: {signals_result.summary['buy_signals']}")
    print(f"Sell signals: {signals_result.summary['sell_signals']}")
    print(f"Average confidence: {signals_result.summary['average_confidence']:.2f}")
    
    # Show strongest signal
    strongest_signal = signals_result.get_strongest_signal()
    if strongest_signal:
        print(f"\n🎯 Strongest Signal:")
        print(f"  Type: {strongest_signal.signal_type.value}")
        print(f"  Direction: {strongest_signal.direction.value}")
        print(f"  Strength: {strongest_signal.strength.value}")
        print(f"  Confidence: {strongest_signal.confidence:.2f}")
        print(f"  Description: {strongest_signal.description}")
    
    # Show recent signals
    recent_signals = [s for s in signals_result.signals if s.timestamp > datetime.now() - timedelta(days=7)]
    if recent_signals:
        print(f"\n📅 Recent Signals (Last 7 days):")
        for signal in recent_signals[:5]:  # Show top 5
            print(f"  {signal.timestamp.strftime('%Y-%m-%d')}: {signal.description}")
    
    return signals_result


def example_patterns_analysis():
    """Example of patterns analysis."""
    print("\n" + "="*60)
    print("PATTERNS ANALYSIS EXAMPLE")
    print("="*60)
    
    # Download data for a single stock
    symbol = "TSLA"
    data = get_stock_data_yf(symbols=symbol, period="1y", interval="1d")
    
    if 'Open' in data.columns:
        data = data.rename(columns={
            'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume'
        })
    
    # Ensure datetime index for pattern timestamps
    data = _ensure_datetime_index(data)

    # Initialize pattern detector
    pattern_detector = PatternDetector()
    
    # Detect all patterns
    print(f"\nDetecting patterns for {symbol}...")
    patterns_result = pattern_detector.detect_all_patterns(data)
    
    print(f"\n📈 Pattern Analysis Results for {symbol}:")
    print(f"Total patterns: {patterns_result.summary['total_patterns']}")
    print(f"Bullish patterns: {patterns_result.summary['bullish_patterns']}")
    print(f"Bearish patterns: {patterns_result.summary['bearish_patterns']}")
    print(f"High reliability patterns: {patterns_result.summary['high_reliability_patterns']}")
    
    # Show detected patterns
    if patterns_result.patterns:
        print(f"\n🔍 Detected Patterns:")
        for pattern in patterns_result.patterns[:5]:  # Show top 5
            print(f"  {pattern.pattern_name}: {pattern.description}")
            print(f"    Direction: {pattern.direction.value}")
            print(f"    Reliability: {pattern.reliability.value}")
            print(f"    Confidence: {pattern.confidence:.2f}")
            if pattern.breakout_price:
                print(f"    Breakout Price: ${pattern.breakout_price:.2f}")
            print()
    
    return patterns_result


def example_suggestions_analysis():
    """Example of suggestions analysis."""
    print("\n" + "="*60)
    print("SUGGESTIONS ANALYSIS EXAMPLE")
    print("="*60)
    
    # Download data for multiple stocks
    symbols = ["AAPL", "MSFT", "GOOGL"]
    stock_data = {}
    
    for symbol in symbols:
        data = get_stock_data_yf(symbols=symbol, period="6mo", interval="1d")
        if 'Open' in data.columns:
            data = data.rename(columns={
                'Open': 'open', 'High': 'high', 'Low': 'low',
                'Close': 'close', 'Volume': 'volume'
            })
        stock_data[symbol] = _ensure_datetime_index(data)
    
    # Initialize suggestion engine
    suggestion_engine = SuggestionEngine()
    
    # Generate suggestions for each stock
    for symbol, data in stock_data.items():
        print(f"\n💡 Generating suggestions for {symbol}...")
        
        try:
            suggestions_result = suggestion_engine.generate_suggestions(data, symbol)
            
            print(f"  Total suggestions: {suggestions_result.summary['total_suggestions']}")
            print(f"  Buy suggestions: {suggestions_result.summary['buy_suggestions']}")
            print(f"  Sell suggestions: {suggestions_result.summary['sell_suggestions']}")
            print(f"  Hold suggestions: {suggestions_result.summary['hold_suggestions']}")
            
            # Show strongest suggestion
            strongest_suggestion = suggestions_result.get_strongest_suggestion()
            if strongest_suggestion:
                print(f"\n  🎯 Strongest Suggestion:")
                print(f"    Type: {strongest_suggestion.suggestion_type.value}")
                print(f"    Strength: {strongest_suggestion.strength.value}")
                print(f"    Confidence: {strongest_suggestion.confidence:.2f}")
                print(f"    Current Price: ${strongest_suggestion.current_price:.2f}")
                
                # Show position recommendation
                pos_rec = strongest_suggestion.position_recommendation
                print(f"    Position Size: {pos_rec.suggested_position_size*100:.1f}%")
                print(f"    Entry Price: ${pos_rec.entry_price:.2f}")
                print(f"    Stop Loss: ${pos_rec.stop_loss:.2f}")
                print(f"    Take Profit: ${pos_rec.take_profit:.2f}")
                print(f"    Risk/Reward: {pos_rec.risk_reward_ratio:.2f}")
                
                # Show reasoning
                print(f"    Reasoning: {'; '.join(strongest_suggestion.reasoning)}")
            
        except Exception as e:
            print(f"  ❌ Error generating suggestions for {symbol}: {e}")
    
    return suggestions_result


def example_scanner_analysis():
    """Example of scanner analysis."""
    print("\n" + "="*60)
    print("SCANNER ANALYSIS EXAMPLE")
    print("="*60)
    
    # Download data for multiple stocks
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX"]
    stock_data = download_multiple_stocks(symbols, period="3mo")
    
    if not stock_data:
        print("❌ No data available for scanning")
        return
    
    # Initialize scanner
    scanner = StockScanner()
    
    # Scan for bullish signals
    print(f"\n🔍 Scanning {len(stock_data)} stocks for bullish signals...")
    from finance_tools.analysis.scanner.scanner_types import SignalDirection, ScannerCriteria, ScannerType
    
    criteria = ScannerCriteria(
        scanner_type=ScannerType.TECHNICAL_SCANNER,
        signal_direction=SignalDirection.BULLISH,
        min_confidence=0.6
    )
    
    scan_result = scanner.scan_stocks(stock_data, criteria)
    
    print(f"\n📊 Scanner Results:")
    print(f"Total scanned: {scan_result.total_scanned}")
    print(f"Total matches: {scan_result.total_matches}")
    print(f"Bullish matches: {scan_result.bullish_matches}")
    print(f"Execution time: {scan_result.execution_time:.2f} seconds")
    
    # Show top matches
    top_matches = scan_result.get_top_matches(5)
    if top_matches:
        print(f"\n🏆 Top Matches:")
        for i, match in enumerate(top_matches, 1):
            print(f"  {i}. {match.symbol}")
            print(f"     Confidence: {match.confidence:.2f}")
            print(f"     Strength: {match.strength}")
            print(f"     Price: ${match.current_price:.2f}")
            print(f"     Description: {match.description}")
            print()
    
    # Scan for breakouts
    print(f"\n🚀 Scanning for breakout patterns...")
    breakout_criteria = ScannerCriteria(
        scanner_type=ScannerType.BREAKOUT_SCANNER,
        signal_direction=SignalDirection.BULLISH,
        min_confidence=0.7
    )
    
    breakout_result = scanner.scan_stocks(stock_data, breakout_criteria)
    
    print(f"Breakout matches: {breakout_result.total_matches}")
    if breakout_result.results:
        print(f"\n💥 Breakout Candidates:")
        for result in breakout_result.results[:3]:
            print(f"  {result.symbol}: {result.description}")
    
    return scan_result


def example_portfolio_analysis():
    """Example of portfolio analysis."""
    print("\n" + "="*60)
    print("PORTFOLIO ANALYSIS EXAMPLE")
    print("="*60)
    
    # Download data for portfolio stocks
    portfolio_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    stock_data = download_multiple_stocks(portfolio_symbols, period="1y")
    
    if not stock_data:
        print("❌ No data available for portfolio analysis")
        return
    
    # Calculate returns for each stock
    returns_data = {}
    for symbol, data in stock_data.items():
        returns = data['close'].pct_change().dropna()
        returns_data[symbol] = returns
    
    # Create returns DataFrame
    returns_df = pd.DataFrame(returns_data)
    
    print(f"\n📈 Portfolio Analysis for {len(portfolio_symbols)} stocks:")
    
    # Calculate basic statistics
    print(f"\n📊 Individual Stock Statistics:")
    for symbol in portfolio_symbols:
        if symbol in returns_df.columns:
            returns = returns_df[symbol].dropna()
            annual_return = returns.mean() * 252
            annual_volatility = returns.std() * np.sqrt(252)
            sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
            
            print(f"  {symbol}:")
            print(f"    Annual Return: {annual_return*100:.2f}%")
            print(f"    Annual Volatility: {annual_volatility*100:.2f}%")
            print(f"    Sharpe Ratio: {sharpe_ratio:.2f}")
    
    # Calculate correlation matrix
    correlation_matrix = returns_df.corr()
    print(f"\n🔗 Correlation Matrix:")
    print(correlation_matrix.round(3))
    
    # Portfolio optimization example
    print(f"\n⚖️ Portfolio Optimization Example:")
    print("(This would require additional optimization libraries like scipy.optimize)")
    print("  - Modern Portfolio Theory optimization")
    print("  - Risk parity allocation")
    print("  - Maximum Sharpe ratio portfolio")
    print("  - Minimum variance portfolio")
    
    return returns_df


def run_all_advanced_examples():
    """Run all advanced examples."""
    print("Advanced Finance Tools Analysis Examples")
    print("=" * 60)
    print("This example demonstrates all the new advanced modules:")
    print("  • Signals Analysis (EMA crossovers, RSI signals, etc.)")
    print("  • Patterns Analysis (Chart patterns, candlestick patterns)")
    print("  • Suggestions Analysis (Buy/sell/hold recommendations)")
    print("  • Scanner Analysis (Stock scanning for opportunities)")
    print("  • Portfolio Analysis (Optimization and risk management)")
    print("=" * 60)
    
    try:
        # Run all examples
        signals_result = example_signals_analysis()
        patterns_result = example_patterns_analysis()
        suggestions_result = example_suggestions_analysis()
        scanner_result = example_scanner_analysis()
        portfolio_result = example_portfolio_analysis()
        
        print("\n" + "="*60)
        print("🎉 All advanced examples completed successfully!")
        print("="*60)
        
        # Summary
        print(f"\n📋 Summary:")
        print(f"  • Signals analyzed: {signals_result.summary['total_signals'] if signals_result else 0}")
        print(f"  • Patterns detected: {patterns_result.summary['total_patterns'] if patterns_result else 0}")
        print(f"  • Suggestions generated: {suggestions_result.summary['total_suggestions'] if suggestions_result else 0}")
        print(f"  • Stocks scanned: {scanner_result.total_scanned if scanner_result else 0}")
        print(f"  • Portfolio stocks analyzed: {len(portfolio_result.columns) if portfolio_result is not None else 0}")
        
    except Exception as e:
        logger.error(f"Error running advanced examples: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    run_all_advanced_examples() 