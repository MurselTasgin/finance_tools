# finance_tools/analysis/example_usage.py
"""
Example usage of the technical analysis module with real stock data.

This file demonstrates how to use the analysis module to calculate
various technical indicators, signals, patterns, and generate trading
suggestions using actual stock data from Yahoo Finance.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os
from typing import Dict, Any

# Add the parent directory to the path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import analysis modules
try:
    from finance_tools.analysis.analysis import (
        calculate_ema, calculate_sma, calculate_rsi, calculate_macd,
        calculate_bollinger_bands, calculate_momentum, calculate_supertrend,
        calculate_atr, calculate_stochastic, calculate_roc, calculate_cci,
        calculate_adx, calculate_obv, calculate_vwap, calculate_support_resistance,
        TechnicalAnalysis
    )
    from finance_tools.analysis.utils import (
        validate_ohlcv_data, clean_data, prepare_data_for_analysis,
        format_analysis_results, calculate_performance_metrics,
        create_summary_report, export_results
    )
    from finance_tools.analysis.config import get_config, AnalysisConfig
    
    # Import new advanced modules
    from finance_tools.analysis.signals import (
        SignalCalculator, calculate_ema_crossover_signals, calculate_price_ma_signals,
        calculate_momentum_signals, calculate_volume_signals, calculate_multi_timeframe_signals
    )
    from finance_tools.analysis.patterns import (
        PatternDetector, detect_chart_patterns, detect_candlestick_patterns,
        detect_breakout_patterns, detect_divergence_patterns, detect_harmonic_patterns
    )
    from finance_tools.analysis.suggestions import (
        SuggestionEngine, generate_trading_suggestions, analyze_risk_reward,
        calculate_position_size, generate_portfolio_suggestions
    )
    from finance_tools.analysis.scanner import (
        StockScanner, scan_for_signals, scan_for_patterns, scan_for_breakouts,
        scan_for_momentum, scan_for_volume_anomalies, scan_multiple_timeframes
    )
    from finance_tools.analysis.portfolio import (
        PortfolioOptimizer, PortfolioSuggester, optimize_portfolio,
        suggest_portfolio_allocation, suggest_rebalancing, suggest_risk_management
    )
    
    from finance_tools.stocks.data_downloaders.yfinance import get_stock_data_yf, YFinanceDownloader
except ImportError:
    # Fallback to relative imports if running as module
    from .analysis import (
        calculate_ema, calculate_sma, calculate_rsi, calculate_macd,
        calculate_bollinger_bands, calculate_momentum, calculate_supertrend,
        calculate_atr, calculate_stochastic, calculate_roc, calculate_cci,
        calculate_adx, calculate_obv, calculate_vwap, calculate_support_resistance,
        TechnicalAnalysis
    )
    from .utils import (
        validate_ohlcv_data, clean_data, prepare_data_for_analysis,
        format_analysis_results, calculate_performance_metrics,
        create_summary_report, export_results
    )
    from .config import get_config, AnalysisConfig
    
    # Import new advanced modules
    from .signals import (
        SignalCalculator, calculate_ema_crossover_signals, calculate_price_ma_signals,
        calculate_momentum_signals, calculate_volume_signals, calculate_multi_timeframe_signals
    )
    from .patterns import (
        PatternDetector, detect_chart_patterns, detect_candlestick_patterns,
        detect_breakout_patterns, detect_divergence_patterns, detect_harmonic_patterns
    )
    from .suggestions import (
        SuggestionEngine, generate_trading_suggestions, analyze_risk_reward,
        calculate_position_size, generate_portfolio_suggestions
    )
    from .scanner import (
        StockScanner, scan_for_signals, scan_for_patterns, scan_for_breakouts,
        scan_for_momentum, scan_for_volume_anomalies, scan_multiple_timeframes
    )
    from .portfolio import (
        PortfolioOptimizer, PortfolioSuggester, optimize_portfolio,
        suggest_portfolio_allocation, suggest_rebalancing, suggest_risk_management
    )
    
    from ..stocks.data_downloaders.yfinance import get_stock_data_yf, YFinanceDownloader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_stock_data(symbol: str, period: str = "1y", start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Download actual stock data using the finance_tools.stocks module.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "TSLA", "MSFT")
        period: Data period ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    
    Returns:
        pd.DataFrame: OHLCV stock data
    """
    try:
        logger.info(f"Downloading data for {symbol}...")
        
        # Download stock data
        data = get_stock_data_yf(
            symbols=symbol,
            start_date=start_date,
            end_date=end_date,
            period=period,
            interval="1d"
        )
        
        if data.empty:
            raise ValueError(f"No data downloaded for {symbol}")
        
        # Ensure we have the required OHLCV columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Check what columns we actually have
        print(f"Available columns: {data.columns.tolist()}")
        
        # Try different column name mappings
        column_mappings = [
            # Standard Yahoo Finance column names
            {'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close', 'Volume': 'Volume'},
            # Lowercase column names
            {'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'},
            # Alternative column names that might be returned
            {'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close', 'Volume': 'Volume'},
        ]
        
        data_renamed = None
        for mapping in column_mappings:
            if all(col in data.columns for col in mapping.values()):
                data_renamed = data.rename(columns={v: k for k, v in mapping.items()})
                break
        
        if data_renamed is None:
            # If no exact match, try to find columns that contain the required names
            available_cols = data.columns.tolist()
            print(f"Available columns: {available_cols}")
            
            # Try to map columns by partial matching
            mapping = {}
            for req_col in required_columns:
                for avail_col in available_cols:
                    if req_col.lower() in avail_col.lower():
                        mapping[avail_col] = req_col
                        break
            
            if len(mapping) >= 4:  # At least OHLC
                data_renamed = data.rename(columns=mapping)
            else:
                raise ValueError(f"Missing required columns. Available columns: {available_cols}")
        
        data = data_renamed
        
        # Convert column names to lowercase for consistency
        data = data.rename(columns={
            'Open': 'open', 'High': 'high', 'Low': 'low', 
            'Close': 'close', 'Volume': 'volume'
        })
        
        # Set the date as index if it's a column
        if 'Date' in data.columns:
            data = data.set_index('Date')
        
        # Add symbol column
        data['Symbol'] = symbol
        
        logger.info(f"Successfully downloaded {len(data)} days of data for {symbol}")
        logger.info(f"Date range: {data.index.min()} to {data.index.max()}")
        logger.info(f"Price range: ${data['low'].min():.2f} - ${data['high'].max():.2f}")
        
        return data
        
    except Exception as e:
        logger.error(f"Error downloading data for {symbol}: {e}")
        raise


def example_signals_analysis():
    """Example of analyzing trading signals with real data."""
    print("\n=== Trading Signals Analysis Example ===")
    
    # Download real stock data
    symbol = "AAPL"
    data = download_stock_data(symbol, period="6mo")
    data = prepare_data_for_analysis(data, symbol=symbol)
    
    # Initialize signal calculator
    signal_calc = SignalCalculator()
    
    print(f"\nAnalyzing trading signals for {symbol}")
    print(f"Current price: ${data['close'].iloc[-1]:.2f}")
    
    # Calculate all signals
    print("\n--- EMA Crossover Signals ---")
    ema_signals = calculate_ema_crossover_signals(data)
    for signal in ema_signals:
        print(f"{signal.signal_type.value}: {signal.direction.value} ({signal.strength.value})")
        print(f"  Details: {signal.description}")
    
    print("\n--- Price vs MA Signals ---")
    price_ma_signals = calculate_price_ma_signals(data)
    for signal in price_ma_signals:
        print(f"{signal.signal_type.value}: {signal.direction.value} ({signal.strength.value})")
        print(f"  Details: {signal.description}")
    
    print("\n--- Momentum Signals ---")
    momentum_signals = calculate_momentum_signals(data)
    for signal in momentum_signals:
        print(f"{signal.signal_type.value}: {signal.direction.value} ({signal.strength.value})")
        print(f"  Details: {signal.description}")
    
    print("\n--- Volume Signals ---")
    volume_signals = calculate_volume_signals(data)
    for signal in volume_signals:
        print(f"{signal.signal_type.value}: {signal.direction.value} ({signal.strength.value})")
        print(f"  Details: {signal.description}")
    
    # Get comprehensive signal analysis
    all_signals = signal_calc.calculate_all_signals(data)
    print(f"\n--- Signal Summary ---")
    print(f"Total signals detected: {len(all_signals.signals)}")
    
    buy_signals = [s for s in all_signals.signals if s.direction.value == 'buy']
    sell_signals = [s for s in all_signals.signals if s.direction.value == 'sell']
    
    print(f"Buy signals: {len(buy_signals)}")
    print(f"Sell signals: {len(sell_signals)}")
    
    return data, all_signals


def example_pattern_analysis():
    """Example of analyzing price patterns with real data."""
    print("\n=== Price Pattern Analysis Example ===")
    
    # Download real stock data
    symbol = "TSLA"
    data = download_stock_data(symbol, period="1y")
    data = prepare_data_for_analysis(data, symbol=symbol)
    
    # Initialize pattern detector
    pattern_detector = PatternDetector()
    
    print(f"\nAnalyzing price patterns for {symbol}")
    print(f"Current price: ${data['close'].iloc[-1]:.2f}")
    
    # Detect chart patterns
    print("\n--- Chart Patterns ---")
    chart_patterns = detect_chart_patterns(data)
    for pattern in chart_patterns:
        print(f"{pattern.pattern_type.value}: {pattern.direction.value} ({pattern.reliability.value})")
        print(f"  Confidence: {pattern.confidence:.2f}")
        print(f"  Description: {pattern.description}")
    
    # Detect candlestick patterns
    print("\n--- Candlestick Patterns ---")
    candlestick_patterns = detect_candlestick_patterns(data)
    for pattern in candlestick_patterns:
        print(f"{pattern.pattern_type.value}: {pattern.direction.value} ({pattern.reliability.value})")
        print(f"  Confidence: {pattern.confidence:.2f}")
        print(f"  Description: {pattern.description}")
    
    # Detect breakout patterns
    print("\n--- Breakout Patterns ---")
    breakout_patterns = detect_breakout_patterns(data)
    for pattern in breakout_patterns:
        print(f"{pattern.pattern_type.value}: {pattern.direction.value} ({pattern.reliability.value})")
        print(f"  Confidence: {pattern.confidence:.2f}")
        print(f"  Description: {pattern.description}")
    
    # Detect divergence patterns
    print("\n--- Divergence Patterns ---")
    divergence_patterns = detect_divergence_patterns(data)
    for pattern in divergence_patterns:
        print(f"{pattern.pattern_type.value}: {pattern.direction.value} ({pattern.reliability.value})")
        print(f"  Confidence: {pattern.confidence:.2f}")
        print(f"  Description: {pattern.description}")
    
    # Get comprehensive pattern analysis
    all_patterns = pattern_detector.detect_all_patterns(data)
    print(f"\n--- Pattern Summary ---")
    print(f"Total patterns detected: {len(all_patterns.patterns)}")
    
    bullish_patterns = [p for p in all_patterns.patterns if p.direction.value == 'bullish']
    bearish_patterns = [p for p in all_patterns.patterns if p.direction.value == 'bearish']
    
    print(f"Bullish patterns: {len(bullish_patterns)}")
    print(f"Bearish patterns: {len(bearish_patterns)}")
    
    return data, all_patterns


def example_trading_suggestions():
    """Example of generating trading suggestions with real data."""
    print("\n=== Trading Suggestions Example ===")
    
    # Download real stock data
    symbol = "NVDA"
    data = download_stock_data(symbol, period="6mo")
    data = prepare_data_for_analysis(data, symbol=symbol)
    
    # Initialize suggestion engine
    suggestion_engine = SuggestionEngine()
    
    print(f"\nGenerating trading suggestions for {symbol}")
    print(f"Current price: ${data['close'].iloc[-1]:.2f}")
    
    # Generate comprehensive trading suggestions
    suggestions = generate_trading_suggestions(data, symbol)
    
    print(f"\n--- Trading Recommendation ---")
    if suggestions.suggestions:
        strongest_suggestion = suggestions.get_strongest_suggestion()
        print(f"Action: {strongest_suggestion.suggestion_type.value}")
        print(f"Confidence: {strongest_suggestion.confidence:.2f}")
        print(f"Strength: {strongest_suggestion.strength.value}")
        print(f"Reasoning: {', '.join(strongest_suggestion.reasoning)}")
        
        print(f"\n--- Risk Assessment ---")
        risk_assessment = strongest_suggestion.risk_assessment
        print(f"Risk Level: {risk_assessment.risk_level.value}")
        print(f"Volatility: {risk_assessment.volatility:.2f}")
        print(f"Drawdown Potential: {risk_assessment.drawdown_potential:.2f}")
        print(f"Liquidity Risk: {risk_assessment.liquidity_risk:.2f}")
        print(f"Correlation Risk: {risk_assessment.correlation_with_market:.2f}")
        
        print(f"\n--- Position Recommendation ---")
        position = strongest_suggestion.position_recommendation
        print(f"Position Size: {position.suggested_position_size * 100:.2f}%")
        print(f"Entry Price: ${position.entry_price:.2f}")
        print(f"Stop Loss: ${position.stop_loss:.2f}")
        print(f"Take Profit: ${position.take_profit:.2f}")
        print(f"Risk/Reward Ratio: {position.risk_reward_ratio:.2f}")
    else:
        print("No trading suggestions generated")
    
    # Analyze risk/reward
    risk_reward = analyze_risk_reward(data, symbol)
    print(f"\n--- Risk/Reward Analysis ---")
    print(f"Potential Upside: {risk_reward['potential_upside']:.2f}%")
    print(f"Potential Downside: {risk_reward['potential_downside']:.2f}%")
    print(f"Risk/Reward Ratio: {risk_reward['risk_reward_ratio']:.2f}")
    print(f"Probability of Success: {risk_reward['probability_of_success']:.2f}")
    
    # Calculate position size
    position_size = calculate_position_size(data, symbol, risk_tolerance=0.5)
    print(f"\n--- Position Sizing ---")
    print(f"Recommended Position Size: {position_size['position_size']:.2f}%")
    print(f"Maximum Position Size: {position_size['max_position_size']:.2f}%")
    print(f"Risk per Trade: {position_size['risk_per_trade']:.2f}%")
    
    return data, suggestions, risk_reward, position_size


def example_stock_scanner():
    """Example of scanning multiple stocks for opportunities."""
    print("\n=== Stock Scanner Example ===")
    
    # List of stocks to scan
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX"]
    
    # Download data for all stocks
    stock_data = {}
    for symbol in symbols:
        try:
            data = download_stock_data(symbol, period="3mo")
            data = prepare_data_for_analysis(data, symbol=symbol)
            stock_data[symbol] = data
            print(f"Downloaded data for {symbol}")
        except Exception as e:
            print(f"Error downloading {symbol}: {e}")
    
    # Initialize scanner
    scanner = StockScanner()
    
    print(f"\n--- Scanning for Technical Signals ---")
    signal_results = scan_for_signals(stock_data)
    print(f"Found {len(signal_results)} stocks with technical signals")
    
    for result in signal_results.results[:5]:  # Show top 5
        print(f"{result.symbol}: Confidence {result.confidence:.2f}")
        print(f"  - {result.description}")
    
    print(f"\n--- Scanning for Patterns ---")
    pattern_results = scan_for_patterns(stock_data)
    print(f"Found {len(pattern_results)} stocks with patterns")
    
    for result in pattern_results.results[:5]:  # Show top 5
        print(f"{result.symbol}: Confidence {result.confidence:.2f}")
        print(f"  - {result.description}")
    
    print(f"\n--- Scanning for Breakouts ---")
    breakout_results = scan_for_breakouts(stock_data)
    print(f"Found {len(breakout_results)} stocks with breakouts")
    
    for result in breakout_results.results[:5]:  # Show top 5
        print(f"{result.symbol}: Confidence {result.confidence:.2f}")
        print(f"  - {result.description}")
    
    print(f"\n--- Scanning for Momentum ---")
    momentum_results = scan_for_momentum(stock_data)
    print(f"Found {len(momentum_results)} stocks with momentum")
    
    for result in momentum_results.results[:5]:  # Show top 5
        print(f"{result.symbol}: Confidence {result.confidence:.2f}")
        print(f"  - {result.description}")
    
    print(f"\n--- Scanning for Volume Anomalies ---")
    volume_results = scan_for_volume_anomalies(stock_data)
    print(f"Found {len(volume_results)} stocks with volume anomalies")
    
    for result in volume_results.results[:5]:  # Show top 5
        print(f"{result.symbol}: Confidence {result.confidence:.2f}")
        print(f"  - {result.description}")
    
    return stock_data, signal_results, pattern_results, breakout_results, momentum_results, volume_results


def example_portfolio_analysis():
    """Example of portfolio optimization and suggestions."""
    print("\n=== Portfolio Analysis Example ===")
    
    # Download data for multiple stocks
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    stock_data = {}
    
    for symbol in symbols:
        try:
            data = download_stock_data(symbol, period="1y")
            data = prepare_data_for_analysis(data, symbol=symbol)
            stock_data[symbol] = data
        except Exception as e:
            print(f"Error downloading {symbol}: {e}")
    
    # Calculate returns for portfolio optimization
    returns_data = pd.DataFrame()
    for symbol, data in stock_data.items():
        returns_data[symbol] = data['close'].pct_change().dropna()
    
    print(f"\n--- Portfolio Optimization ---")
    
    # Initialize portfolio optimizer
    optimizer = PortfolioOptimizer()
    
    # Optimize portfolio using different methods
    try:
        from finance_tools.analysis.portfolio.portfolio_types import OptimizationMethod
    except ImportError:
        from .portfolio.portfolio_types import OptimizationMethod
    
    optimization_methods = [
        OptimizationMethod.MODERN_PORTFOLIO_THEORY,
        OptimizationMethod.RISK_PARITY,
        OptimizationMethod.MAX_SHARPE_RATIO,
        OptimizationMethod.MIN_VARIANCE
    ]
    
    for method in optimization_methods:
        try:
            result = optimizer.optimize_portfolio(returns_data, method=method)
            print(f"\n{method.value.replace('_', ' ').title()}:")
            print(f"  Expected Return: {result.expected_return:.2f}%")
            print(f"  Expected Volatility: {result.expected_volatility:.2f}%")
            print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(f"  Rebalancing Needed: {result.rebalancing_needed}")
        except Exception as e:
            print(f"Error with {method.value}: {e}")
    
    print(f"\n--- Portfolio Suggestions ---")
    
    # Initialize portfolio suggester
    suggester = PortfolioSuggester()
    
    # Generate suggestions for different strategies
    try:
        from finance_tools.analysis.portfolio.portfolio_types import PortfolioStrategy
    except ImportError:
        from .portfolio.portfolio_types import PortfolioStrategy
    
    strategies = [
        PortfolioStrategy.CONSERVATIVE,
        PortfolioStrategy.MODERATE,
        PortfolioStrategy.AGGRESSIVE,
        PortfolioStrategy.GROWTH,
        PortfolioStrategy.VALUE
    ]
    
    for strategy in strategies:
        try:
            suggestion = suggester.suggest_portfolio_allocation(returns_data, strategy=strategy)
            print(f"\n{strategy.value.title()} Strategy:")
            print(f"  Expected Return: {suggestion['expected_return']:.2f}%")
            print(f"  Expected Volatility: {suggestion['expected_volatility']:.2f}%")
            print(f"  Sharpe Ratio: {suggestion['sharpe_ratio']:.2f}")
            
            # Show top allocations
            top_allocations = sorted(suggestion['suggestions'], 
                                   key=lambda x: x.suggested_weight, reverse=True)[:3]
            print(f"  Top Allocations:")
            for alloc in top_allocations:
                print(f"    {alloc.symbol}: {alloc.suggested_weight:.1f}%")
        except Exception as e:
            print(f"Error with {strategy.value} strategy: {e}")
    
    return stock_data, returns_data


def example_comprehensive_analysis():
    """Example of comprehensive analysis including signals, patterns, and suggestions."""
    print("\n=== Comprehensive Analysis Example ===")
    
    # Download real stock data
    symbol = "AAPL"
    data = download_stock_data(symbol, period="1y")
    data = prepare_data_for_analysis(data, symbol=symbol)
    
    print(f"\nComprehensive Analysis for {symbol}")
    print(f"Current price: ${data['close'].iloc[-1]:.2f}")
    print(f"Analysis period: {data.index.min()} to {data.index.max()}")
    
    # 1. Technical Indicators
    print(f"\n--- Technical Indicators ---")
    ta = TechnicalAnalysis()
    indicators = ta.calculate_all_indicators(data)
    
    # Show key indicators
    key_indicators = ['rsi', 'macd_line', 'bb_upper', 'supertrend', 'atr']
    for indicator in key_indicators:
        if indicator in indicators:
            current_value = indicators[indicator].iloc[-1]
            if indicator == 'rsi':
                print(f"{indicator.upper()}: {current_value:.2f}")
            elif indicator == 'atr':
                print(f"{indicator.upper()}: {current_value:.4f}")
            else:
                print(f"{indicator.upper()}: {current_value:.2f}")
    
    # 2. Trading Signals
    print(f"\n--- Trading Signals ---")
    signal_calc = SignalCalculator()
    signals = signal_calc.calculate_all_signals(data)
    
    buy_signals = [s for s in signals.signals if s.direction.value == 'buy']
    sell_signals = [s for s in signals.signals if s.direction.value == 'sell']
    
    print(f"Buy signals: {len(buy_signals)}")
    print(f"Sell signals: {len(sell_signals)}")
    
    # Show strongest signals
    strong_signals = sorted(signals.signals, key=lambda x: x.strength.value, reverse=True)[:3]
    for signal in strong_signals:
        print(f"  {signal.signal_type.value}: {signal.direction.value} ({signal.strength.value})")
    
    # 3. Price Patterns
    print(f"\n--- Price Patterns ---")
    pattern_detector = PatternDetector()
    patterns = pattern_detector.detect_all_patterns(data)
    
    bullish_patterns = [p for p in patterns.patterns if p.direction.value == 'bullish']
    bearish_patterns = [p for p in patterns.patterns if p.direction.value == 'bearish']
    
    print(f"Bullish patterns: {len(bullish_patterns)}")
    print(f"Bearish patterns: {len(bearish_patterns)}")
    
    # Show most reliable patterns
    reliable_patterns = sorted(patterns.patterns, key=lambda x: x.confidence, reverse=True)[:3]
    for pattern in reliable_patterns:
        print(f"  {pattern.pattern_type.value}: {pattern.direction.value} (confidence: {pattern.confidence:.2f})")
    
    # 4. Trading Suggestions
    print(f"\n--- Trading Suggestions ---")
    suggestion_engine = SuggestionEngine()
    suggestions = suggestion_engine.generate_suggestions(data, symbol)
    
    if suggestions.suggestions:
        strongest_suggestion = suggestions.get_strongest_suggestion()
        print(f"Action: {strongest_suggestion.suggestion_type.value}")
        print(f"Confidence: {strongest_suggestion.confidence:.2f}")
        print(f"Strength: {strongest_suggestion.strength.value}")
        print(f"Reasoning: {', '.join(strongest_suggestion.reasoning)}")
        
        # 5. Risk Assessment
        print(f"\n--- Risk Assessment ---")
        risk_assessment = strongest_suggestion.risk_assessment
        print(f"Risk Level: {risk_assessment.risk_level.value}")
        print(f"Volatility: {risk_assessment.volatility:.2f}")
        print(f"Drawdown Potential: {risk_assessment.drawdown_potential:.2f}")
        
        # 6. Position Sizing
        print(f"\n--- Position Sizing ---")
        position = strongest_suggestion.position_recommendation
        print(f"Position Size: {position.suggested_position_size * 100:.2f}%")
        print(f"Entry Price: ${position.entry_price:.2f}")
        print(f"Stop Loss: ${position.stop_loss:.2f}")
        print(f"Take Profit: ${position.take_profit:.2f}")
        print(f"Risk/Reward Ratio: {position.risk_reward_ratio:.2f}")
    else:
        print("No trading suggestions generated")
    
    # 7. Summary
    print(f"\n--- Analysis Summary ---")
    signal_score = len(buy_signals) - len(sell_signals)
    pattern_score = len(bullish_patterns) - len(bearish_patterns)
    
    print(f"Signal Score: {signal_score} (positive = bullish)")
    print(f"Pattern Score: {pattern_score} (positive = bullish)")
    print(f"Overall Sentiment: {'BULLISH' if signal_score + pattern_score > 0 else 'BEARISH' if signal_score + pattern_score < 0 else 'NEUTRAL'}")
    
    return data, indicators, signals, patterns, suggestions


def example_basic_indicators():
    """Example of calculating basic technical indicators with real data."""
    print("\n=== Basic Technical Indicators Example (Real Data) ===")
    
    # Download real stock data
    symbol = "AAPL"
    data = download_stock_data(symbol, period="6mo")
    
    # Prepare data for analysis
    data = prepare_data_for_analysis(data, symbol=symbol)
    
    # Calculate individual indicators
    close_prices = data['close']
    
    print(f"\nAnalyzing {symbol} - {len(data)} days of data")
    print(f"Current price: ${close_prices.iloc[-1]:.2f}")
    print(f"Price range: ${data['low'].min():.2f} - ${data['high'].max():.2f}")
    
    # EMA
    ema_20 = calculate_ema(close_prices, 20)
    ema_50 = calculate_ema(close_prices, 50)
    print(f"\nMoving Averages:")
    print(f"EMA(20): ${ema_20.iloc[-1]:.2f}")
    print(f"EMA(50): ${ema_50.iloc[-1]:.2f}")
    
    # SMA
    sma_20 = calculate_sma(close_prices, 20)
    sma_50 = calculate_sma(close_prices, 50)
    print(f"SMA(20): ${sma_20.iloc[-1]:.2f}")
    print(f"SMA(50): ${sma_50.iloc[-1]:.2f}")
    
    # RSI
    rsi = calculate_rsi(close_prices, 14)
    rsi_current = rsi.iloc[-1]
    print(f"\nMomentum Indicators:")
    print(f"RSI(14): {rsi_current:.2f}")
    if rsi_current > 70:
        print("  → Overbought (>70)")
    elif rsi_current < 30:
        print("  → Oversold (<30)")
    else:
        print("  → Neutral")
    
    # MACD
    macd_line, signal_line, histogram = calculate_macd(close_prices)
    print(f"MACD Line: {macd_line.iloc[-1]:.4f}")
    print(f"MACD Signal: {signal_line.iloc[-1]:.4f}")
    print(f"MACD Histogram: {histogram.iloc[-1]:.4f}")
    
    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(close_prices)
    current_price = close_prices.iloc[-1]
    print(f"\nVolatility Indicators:")
    print(f"Bollinger Bands:")
    print(f"  Upper: ${bb_upper.iloc[-1]:.2f}")
    print(f"  Middle: ${bb_middle.iloc[-1]:.2f}")
    print(f"  Lower: ${bb_lower.iloc[-1]:.2f}")
    
    if current_price > bb_upper.iloc[-1]:
        print("  → Price above upper band (potential sell)")
    elif current_price < bb_lower.iloc[-1]:
        print("  → Price below lower band (potential buy)")
    else:
        print("  → Price within bands")
    
    return data


def example_advanced_indicators():
    """Example of advanced technical indicators with real data."""
    print("\n=== Advanced Indicators Example (Real Data) ===")
    
    # Download real stock data
    symbol = "NVDA"
    data = download_stock_data(symbol, period="6mo")
    
    # Prepare data for analysis
    data = prepare_data_for_analysis(data, symbol=symbol)
    
    print(f"\nAnalyzing {symbol} - {len(data)} days of data")
    print(f"Current price: ${data['close'].iloc[-1]:.2f}")
    
    # Calculate advanced indicators
    high = data['high']
    low = data['low']
    close = data['close']
    volume = data['volume']
    
    print(f"\n=== Advanced Technical Indicators ===")
    
    # Supertrend
    supertrend, trend = calculate_supertrend(high, low, close)
    trend_direction = "UP" if trend.iloc[-1] == 1 else "DOWN"
    print(f"Supertrend: ${supertrend.iloc[-1]:.2f} ({trend_direction})")
    
    # ATR
    atr = calculate_atr(high, low, close)
    print(f"ATR: {atr.iloc[-1]:.4f}")
    
    # Stochastic
    stoch_k, stoch_d = calculate_stochastic(high, low, close)
    print(f"Stochastic %K: {stoch_k.iloc[-1]:.2f}")
    print(f"Stochastic %D: {stoch_d.iloc[-1]:.2f}")
    
    # CCI
    cci = calculate_cci(high, low, close)
    cci_current = cci.iloc[-1]
    print(f"CCI: {cci_current:.2f}")
    if cci_current > 100:
        print("  → Overbought (>100)")
    elif cci_current < -100:
        print("  → Oversold (<-100)")
    else:
        print("  → Neutral")
    
    # ADX
    adx, di_plus, di_minus = calculate_adx(high, low, close)
    print(f"ADX: {adx.iloc[-1]:.2f}")
    print(f"+DI: {di_plus.iloc[-1]:.2f}")
    print(f"-DI: {di_minus.iloc[-1]:.2f}")
    
    # OBV
    obv = calculate_obv(close, volume)
    print(f"OBV: {obv.iloc[-1]:,.0f}")
    
    # VWAP
    vwap = calculate_vwap(high, low, close, volume)
    print(f"VWAP: ${vwap.iloc[-1]:.2f}")
    
    # Support/Resistance
    support, resistance = calculate_support_resistance(high, low)
    current_price = close.iloc[-1]
    print(f"Support Level: ${support.iloc[-1]:.2f}")
    print(f"Resistance Level: ${resistance.iloc[-1]:.2f}")
    
    # Price position relative to support/resistance
    support_level = support.iloc[-1]
    resistance_level = resistance.iloc[-1]
    if current_price < support_level * 1.02:  # Within 2% of support
        print("  → Near support level")
    elif current_price > resistance_level * 0.98:  # Within 2% of resistance
        print("  → Near resistance level")
    else:
        print("  → Between support and resistance")
    
    return data


def example_multiple_stocks():
    """Example of analyzing multiple stocks."""
    print("\n=== Multiple Stocks Analysis Example ===")
    
    # List of stocks to analyze
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    
    results = {}
    
    for symbol in symbols:
        try:
            print(f"\n--- Analyzing {symbol} ---")
            
            # Download data
            data = download_stock_data(symbol, period="3mo")
            data = prepare_data_for_analysis(data, symbol=symbol)
            
            # Calculate key indicators
            close_prices = data['close']
            rsi = calculate_rsi(close_prices, 14)
            ema_20 = calculate_ema(close_prices, 20)
            ema_50 = calculate_ema(close_prices, 50)
            
            # Get current values
            current_price = close_prices.iloc[-1]
            current_rsi = rsi.iloc[-1]
            current_ema_20 = ema_20.iloc[-1]
            current_ema_50 = ema_50.iloc[-1]
            
            # Determine trend
            if current_ema_20 > current_ema_50:
                trend = "BULLISH"
            else:
                trend = "BEARISH"
            
            # Determine RSI condition
            if current_rsi > 70:
                rsi_condition = "OVERBOUGHT"
            elif current_rsi < 30:
                rsi_condition = "OVERSOLD"
            else:
                rsi_condition = "NEUTRAL"
            
            # Store results
            results[symbol] = {
                'price': current_price,
                'rsi': current_rsi,
                'ema_20': current_ema_20,
                'ema_50': current_ema_50,
                'trend': trend,
                'rsi_condition': rsi_condition
            }
            
            print(f"Price: ${current_price:.2f}")
            print(f"RSI: {current_rsi:.2f} ({rsi_condition})")
            print(f"EMA(20): ${current_ema_20:.2f}")
            print(f"EMA(50): ${current_ema_50:.2f}")
            print(f"Trend: {trend}")
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            results[symbol] = {'error': str(e)}
    
    # Summary table
    print(f"\n{'='*60}")
    print(f"{'Symbol':<8} {'Price':<10} {'RSI':<8} {'Trend':<10} {'Condition':<12}")
    print(f"{'='*60}")
    
    for symbol, result in results.items():
        if 'error' not in result:
            print(f"{symbol:<8} ${result['price']:<9.2f} {result['rsi']:<8.2f} {result['trend']:<10} {result['rsi_condition']:<12}")
        else:
            print(f"{symbol:<8} {'ERROR':<10} {'N/A':<8} {'N/A':<10} {'N/A':<12}")
    
    return results


def example_configuration():
    """Example of using configuration settings."""
    print("\n=== Configuration Example ===")
    
    # Get default configuration
    config = get_config()
    print("Default configuration:")
    print(f"Min data points: {config.min_data_points}")
    print(f"RSI period: {config.default_rsi_period}")
    print(f"MACD fast period: {config.default_macd_fast}")
    print(f"Bollinger Bands std dev: {config.default_bollinger_std}")
    
    # Create custom configuration
    custom_config = AnalysisConfig(
        min_data_points=50,
        default_rsi_period=21,
        default_macd_fast=8,
        default_macd_slow=21,
        default_bollinger_std=2.5,
        rsi_oversold=25.0,
        rsi_overbought=75.0
    )
    
    print("\nCustom configuration:")
    print(f"Min data points: {custom_config.min_data_points}")
    print(f"RSI period: {custom_config.default_rsi_period}")
    print(f"RSI oversold: {custom_config.rsi_oversold}")
    print(f"RSI overbought: {custom_config.rsi_overbought}")
    
    return config, custom_config


def example_data_export():
    """Example of exporting analysis results."""
    print("\n=== Data Export Example ===")
    
    # Download real stock data and analysis
    symbol = "MSFT"
    data = download_stock_data(symbol, period="6mo")
    data = prepare_data_for_analysis(data, symbol=symbol)
    
    ta = TechnicalAnalysis()
    indicators = ta.calculate_all_indicators(data)
    signals = ta.get_trading_signals(data)
    
    # Format results
    formatted_results = format_analysis_results(indicators)
    formatted_results['signals'] = signals
    formatted_results['data'] = data
    
    # Export to different formats
    try:
        # Export to JSON
        json_file = export_results(formatted_results, f"{symbol.lower()}_analysis.json", "json")
        print(f"Exported to JSON: {json_file}")
        
        # Export to Excel
        excel_file = export_results(formatted_results, f"{symbol.lower()}_analysis.xlsx", "excel")
        print(f"Exported to Excel: {excel_file}")
        
    except Exception as e:
        print(f"Export error: {e}")
    
    return formatted_results


def generate_executive_summary(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate an executive summary with final recommendations and confidence scores.
    
    Args:
        analysis_results: Dictionary containing all analysis results
        
    Returns:
        Dict[str, Any]: Executive summary with recommendations
    """
    print("\n" + "="*80)
    print("EXECUTIVE SUMMARY & FINAL RECOMMENDATIONS")
    print("="*80)
    
    summary = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'stocks_analyzed': [],
        'overall_market_sentiment': 'NEUTRAL',
        'top_recommendations': [],
        'risk_assessment': {},
        'confidence_score': 0.0
    }
    
    # Collect all analyzed stocks and their data
    analyzed_stocks = {}
    
    # Extract stock data from various analysis results
    if 'signals_data' in analysis_results:
        symbol = "AAPL"  # From signals analysis
        if symbol not in analyzed_stocks:
            analyzed_stocks[symbol] = {
                'symbol': symbol,
                'analysis_type': 'signals',
                'data': analysis_results.get('signals_data'),
                'signals': analysis_results.get('signals')
            }
    
    if 'patterns_data' in analysis_results:
        symbol = "TSLA"  # From patterns analysis
        if symbol not in analyzed_stocks:
            analyzed_stocks[symbol] = {
                'symbol': symbol,
                'analysis_type': 'patterns',
                'data': analysis_results.get('patterns_data'),
                'patterns': analysis_results.get('patterns')
            }
    
    if 'suggestions_data' in analysis_results:
        symbol = "NVDA"  # From suggestions analysis
        if symbol not in analyzed_stocks:
            analyzed_stocks[symbol] = {
                'symbol': symbol,
                'analysis_type': 'suggestions',
                'data': analysis_results.get('suggestions_data'),
                'suggestions': analysis_results.get('suggestions'),
                'risk_reward': analysis_results.get('risk_reward'),
                'position_size': analysis_results.get('position_size')
            }
    
    if 'scanner_data' in analysis_results:
        scanner_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX"]
        for symbol in scanner_symbols:
            if symbol in analysis_results.get('scanner_data', {}):
                if symbol not in analyzed_stocks:
                    analyzed_stocks[symbol] = {
                        'symbol': symbol,
                        'analysis_type': 'scanner',
                        'data': analysis_results.get('scanner_data', {}).get(symbol),
                        'scanner_results': {
                            'signals': analysis_results.get('signal_results'),
                            'patterns': analysis_results.get('pattern_results'),
                            'breakouts': analysis_results.get('breakout_results'),
                            'momentum': analysis_results.get('momentum_results'),
                            'volume': analysis_results.get('volume_results')
                        }
                    }
    
    if 'portfolio_data' in analysis_results:
        portfolio_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
        for symbol in portfolio_symbols:
            if symbol in analysis_results.get('portfolio_data', {}):
                if symbol not in analyzed_stocks:
                    analyzed_stocks[symbol] = {
                        'symbol': symbol,
                        'analysis_type': 'portfolio',
                        'data': analysis_results.get('portfolio_data', {}).get(symbol),
                        'returns_data': analysis_results.get('returns_data')
                    }
    
    if 'comp_data' in analysis_results:
        symbol = "AAPL"  # From comprehensive analysis
        if symbol not in analyzed_stocks:
            analyzed_stocks[symbol] = {
                'symbol': symbol,
                'analysis_type': 'comprehensive',
                'data': analysis_results.get('comp_data'),
                'indicators': analysis_results.get('comp_indicators'),
                'signals': analysis_results.get('comp_signals'),
                'patterns': analysis_results.get('comp_patterns'),
                'suggestions': analysis_results.get('comp_suggestions')
            }
    
    # Analyze each stock and generate recommendations
    stock_recommendations = []
    total_confidence = 0.0
    bullish_count = 0
    bearish_count = 0
    
    for symbol, stock_data in analyzed_stocks.items():
        try:
            if not stock_data.get('data') is not None:
                continue
                
            data = stock_data['data']
            current_price = data['close'].iloc[-1]
            
            # Calculate technical indicators
            close_prices = data['close']
            rsi = calculate_rsi(close_prices, 14)
            ema_20 = calculate_ema(close_prices, 20)
            ema_50 = calculate_ema(close_prices, 50)
            
            # Get current values
            current_rsi = rsi.iloc[-1]
            current_ema_20 = ema_20.iloc[-1]
            current_ema_50 = ema_50.iloc[-1]
            
            # Calculate sentiment score
            sentiment_score = 0
            confidence_factors = []
            
            # Trend analysis
            if current_ema_20 > current_ema_50:
                sentiment_score += 1
                confidence_factors.append("Bullish trend (EMA20 > EMA50)")
            else:
                sentiment_score -= 1
                confidence_factors.append("Bearish trend (EMA20 < EMA50)")
            
            # RSI analysis
            if current_rsi < 30:
                sentiment_score += 1
                confidence_factors.append("Oversold (RSI < 30)")
            elif current_rsi > 70:
                sentiment_score -= 1
                confidence_factors.append("Overbought (RSI > 70)")
            else:
                sentiment_score += 0.5
                confidence_factors.append("Neutral RSI")
            
            # Price vs moving averages
            if current_price > current_ema_20:
                sentiment_score += 0.5
                confidence_factors.append("Price above EMA20")
            else:
                sentiment_score -= 0.5
                confidence_factors.append("Price below EMA20")
            
            # Additional analysis from other modules
            if 'signals' in stock_data:
                signals = stock_data['signals']
                buy_signals = [s for s in signals.signals if s.direction.value == 'buy']
                sell_signals = [s for s in signals.signals if s.direction.value == 'sell']
                signal_score = len(buy_signals) - len(sell_signals)
                sentiment_score += signal_score * 0.5
                confidence_factors.append(f"Signal analysis: {signal_score} net signals")
            
            if 'patterns' in stock_data:
                patterns = stock_data['patterns']
                bullish_patterns = [p for p in patterns.patterns if p.direction.value == 'bullish']
                bearish_patterns = [p for p in patterns.patterns if p.direction.value == 'bearish']
                pattern_score = len(bullish_patterns) - len(bearish_patterns)
                sentiment_score += pattern_score * 0.5
                confidence_factors.append(f"Pattern analysis: {pattern_score} net patterns")
            
            if 'suggestions' in stock_data:
                suggestions = stock_data['suggestions']
                if suggestions.suggestions:
                    strongest_suggestion = suggestions.get_strongest_suggestion()
                    if strongest_suggestion.suggestion_type.value == 'buy':
                        sentiment_score += 1
                        confidence_factors.append("Strong buy recommendation")
                    elif strongest_suggestion.suggestion_type.value == 'sell':
                        sentiment_score -= 1
                        confidence_factors.append("Strong sell recommendation")
            
            # Determine recommendation
            if sentiment_score > 1:
                recommendation = "STRONG BUY"
                bullish_count += 1
            elif sentiment_score > 0:
                recommendation = "BUY"
                bullish_count += 1
            elif sentiment_score < -1:
                recommendation = "STRONG SELL"
                bearish_count += 1
            elif sentiment_score < 0:
                recommendation = "SELL"
                bearish_count += 1
            else:
                recommendation = "HOLD"
            
            # Calculate confidence score (0-100)
            confidence_score = min(100, max(0, 50 + sentiment_score * 15))
            total_confidence += confidence_score
            
            # Risk assessment
            volatility = data['close'].pct_change().std() * np.sqrt(252)
            risk_level = "LOW" if volatility < 0.2 else "MEDIUM" if volatility < 0.4 else "HIGH"
            
            stock_recommendation = {
                'symbol': symbol,
                'current_price': current_price,
                'recommendation': recommendation,
                'confidence_score': confidence_score,
                'sentiment_score': sentiment_score,
                'risk_level': risk_level,
                'volatility': volatility,
                'key_factors': confidence_factors,
                'technical_indicators': {
                    'rsi': current_rsi,
                    'ema_20': current_ema_20,
                    'ema_50': current_ema_50,
                    'trend': "BULLISH" if current_ema_20 > current_ema_50 else "BEARISH"
                }
            }
            
            stock_recommendations.append(stock_recommendation)
            
            # Print individual stock summary
            print(f"\n📊 {symbol} Analysis Summary:")
            print(f"   Current Price: ${current_price:.2f}")
            print(f"   Recommendation: {recommendation}")
            print(f"   Confidence Score: {confidence_score:.1f}%")
            print(f"   Risk Level: {risk_level}")
            print(f"   Key Factors: {', '.join(confidence_factors[:3])}")
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
    
    # Sort recommendations by confidence score
    stock_recommendations.sort(key=lambda x: x['confidence_score'], reverse=True)
    
    # Calculate overall market sentiment
    if bullish_count > bearish_count:
        overall_sentiment = "BULLISH"
    elif bearish_count > bullish_count:
        overall_sentiment = "BEARISH"
    else:
        overall_sentiment = "NEUTRAL"
    
    # Calculate average confidence
    avg_confidence = total_confidence / len(stock_recommendations) if stock_recommendations else 0
    
    # Generate top recommendations
    top_recommendations = stock_recommendations[:5]  # Top 5
    
    # Risk assessment
    high_risk_stocks = [s for s in stock_recommendations if s['risk_level'] == 'HIGH']
    medium_risk_stocks = [s for s in stock_recommendations if s['risk_level'] == 'MEDIUM']
    low_risk_stocks = [s for s in stock_recommendations if s['risk_level'] == 'LOW']
    
    # Print executive summary
    print(f"\n🎯 EXECUTIVE SUMMARY")
    print(f"   Analysis Date: {summary['timestamp']}")
    print(f"   Stocks Analyzed: {len(stock_recommendations)}")
    print(f"   Overall Market Sentiment: {overall_sentiment}")
    print(f"   Average Confidence Score: {avg_confidence:.1f}%")
    
    print(f"\n📈 TOP RECOMMENDATIONS:")
    for i, rec in enumerate(top_recommendations, 1):
        print(f"   {i}. {rec['symbol']}: {rec['recommendation']} (Confidence: {rec['confidence_score']:.1f}%)")
        print(f"      Price: ${rec['current_price']:.2f} | Risk: {rec['risk_level']}")
    
    print(f"\n⚠️  RISK ASSESSMENT:")
    print(f"   High Risk Stocks: {len(high_risk_stocks)}")
    print(f"   Medium Risk Stocks: {len(medium_risk_stocks)}")
    print(f"   Low Risk Stocks: {len(low_risk_stocks)}")
    
    print(f"\n📊 SENTIMENT BREAKDOWN:")
    print(f"   Bullish Stocks: {bullish_count}")
    print(f"   Bearish Stocks: {bearish_count}")
    print(f"   Neutral Stocks: {len(stock_recommendations) - bullish_count - bearish_count}")
    
    # Final recommendations
    print(f"\n🎯 FINAL RECOMMENDATIONS:")
    if overall_sentiment == "BULLISH":
        print("   ✅ Market conditions appear favorable for growth stocks")
        print("   ✅ Consider increasing exposure to high-confidence buy recommendations")
        print("   ⚠️  Monitor risk levels and maintain proper position sizing")
    elif overall_sentiment == "BEARISH":
        print("   ⚠️  Market conditions suggest caution")
        print("   ✅ Focus on defensive positions and risk management")
        print("   📉 Consider reducing exposure to high-risk positions")
    else:
        print("   📊 Market conditions are mixed")
        print("   ✅ Focus on individual stock selection")
        print("   ⚖️  Maintain balanced portfolio allocation")
    
    # Update summary
    summary.update({
        'stocks_analyzed': stock_recommendations,
        'overall_market_sentiment': overall_sentiment,
        'top_recommendations': top_recommendations,
        'risk_assessment': {
            'high_risk': len(high_risk_stocks),
            'medium_risk': len(medium_risk_stocks),
            'low_risk': len(low_risk_stocks),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count
        },
        'confidence_score': avg_confidence
    })
    
    return summary


def run_all_examples():
    """Run all examples with real stock data."""
    print("Advanced Technical Analysis Module Examples with Real Stock Data")
    print("=" * 80)
    
    analysis_results = {}
    
    try:
        # Basic indicators
        data1 = example_basic_indicators()
        analysis_results['basic_data'] = data1
        
        # Advanced indicators
        data2 = example_advanced_indicators()
        analysis_results['advanced_data'] = data2
        
        # Multiple stocks analysis
        results = example_multiple_stocks()
        analysis_results['multiple_stocks_results'] = results
        
        # Configuration
        config, custom_config = example_configuration()
        analysis_results['config'] = config
        analysis_results['custom_config'] = custom_config
        
        # Data export
        export_results = example_data_export()
        analysis_results['export_results'] = export_results
        
        # NEW: Advanced analysis examples
        print("\n" + "="*80)
        print("ADVANCED ANALYSIS EXAMPLES")
        print("="*80)
        
        # Signals analysis
        signals_data, signals = example_signals_analysis()
        analysis_results['signals_data'] = signals_data
        analysis_results['signals'] = signals
        
        # Pattern analysis
        patterns_data, patterns = example_pattern_analysis()
        analysis_results['patterns_data'] = patterns_data
        analysis_results['patterns'] = patterns
        
        # Trading suggestions
        suggestions_data, suggestions, risk_reward, position_size = example_trading_suggestions()
        analysis_results['suggestions_data'] = suggestions_data
        analysis_results['suggestions'] = suggestions
        analysis_results['risk_reward'] = risk_reward
        analysis_results['position_size'] = position_size
        
        # Stock scanner
        scanner_data, signal_results, pattern_results, breakout_results, momentum_results, volume_results = example_stock_scanner()
        analysis_results['scanner_data'] = scanner_data
        analysis_results['signal_results'] = signal_results
        analysis_results['pattern_results'] = pattern_results
        analysis_results['breakout_results'] = breakout_results
        analysis_results['momentum_results'] = momentum_results
        analysis_results['volume_results'] = volume_results
        
        # Portfolio analysis
        portfolio_data, returns_data = example_portfolio_analysis()
        analysis_results['portfolio_data'] = portfolio_data
        analysis_results['returns_data'] = returns_data
        
        # Comprehensive analysis
        comp_data, comp_indicators, comp_signals, comp_patterns, comp_suggestions = example_comprehensive_analysis()
        analysis_results['comp_data'] = comp_data
        analysis_results['comp_indicators'] = comp_indicators
        analysis_results['comp_signals'] = comp_signals
        analysis_results['comp_patterns'] = comp_patterns
        analysis_results['comp_suggestions'] = comp_suggestions
        
        # Generate executive summary
        executive_summary = generate_executive_summary(analysis_results)
        
        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("Advanced analysis includes:")
        print("✅ Trading Signals Analysis")
        print("✅ Price Pattern Detection")
        print("✅ Buy/Hold/Sell Suggestions")
        print("✅ Risk Assessment & Position Sizing")
        print("✅ Stock Scanner for Opportunities")
        print("✅ Portfolio Optimization")
        print("✅ Comprehensive Multi-Factor Analysis")
        print("✅ Executive Summary with Confidence Scores")
        print("Check the generated files for detailed analysis results.")
        
        return executive_summary
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    run_all_examples() 