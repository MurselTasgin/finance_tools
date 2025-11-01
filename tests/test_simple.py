#!/usr/bin/env python3
"""
Simple test script for basic functionality.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

def create_mock_stock_data():
    """Create mock stock data for testing."""
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    
    # Create mock stock data
    np.random.seed(42)
    base_price = 100
    returns = np.random.normal(0.001, 0.02, len(dates))
    prices = [base_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    data = pd.DataFrame({
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)
    
    return data

def test_basic_analysis():
    """Test basic analysis functionality."""
    print("🧪 Testing Basic Analysis Functionality")
    print("=" * 50)
    
    try:
        # Create mock data
        mock_data = create_mock_stock_data()
        print(f"✅ Created mock data with {len(mock_data)} rows")
        
        # Test basic calculations
        close_prices = mock_data['close']
        
        # Calculate basic indicators
        from finance_tools.analysis.analysis import calculate_ema, calculate_rsi
        
        ema_20 = calculate_ema(close_prices, 20)
        rsi = calculate_rsi(close_prices, 14)
        
        print(f"✅ Calculated EMA(20): {ema_20.iloc[-1]:.2f}")
        print(f"✅ Calculated RSI(14): {rsi.iloc[-1]:.2f}")
        
        # Test portfolio types
        from finance_tools.analysis.portfolio.portfolio_types import OptimizationMethod, PortfolioStrategy
        
        print(f"✅ Imported OptimizationMethod: {OptimizationMethod.MODERN_PORTFOLIO_THEORY.value}")
        print(f"✅ Imported PortfolioStrategy: {PortfolioStrategy.CONSERVATIVE.value}")
        
        # Test signal types
        from finance_tools.analysis.signals.signal_types import SignalType, SignalDirection
        
        print(f"✅ Imported SignalType: {SignalType.EMA_CROSSOVER.value}")
        print(f"✅ Imported SignalDirection: {SignalDirection.BUY.value}")
        
        print("\n🎉 All basic tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_executive_summary():
    """Test the executive summary function."""
    print("\n📊 Testing Executive Summary Function")
    print("=" * 50)
    
    try:
        from finance_tools.analysis.example_usage import generate_executive_summary
        
        # Create mock analysis results
        mock_data = create_mock_stock_data()
        
        # Create mock analysis results structure
        analysis_results = {
            'signals_data': mock_data,
            'patterns_data': mock_data,
            'suggestions_data': mock_data,
            'scanner_data': {
                'AAPL': mock_data,
                'MSFT': mock_data,
                'GOOGL': mock_data
            },
            'portfolio_data': {
                'AAPL': mock_data,
                'MSFT': mock_data,
                'GOOGL': mock_data
            },
            'comp_data': mock_data,
            'signals': type('MockSignals', (), {
                'signals': [
                    type('MockSignal', (), {
                        'direction': type('MockDirection', (), {'value': 'buy'})(),
                        'strength': type('MockStrength', (), {'value': 'strong'})()
                    })()
                ]
            })(),
            'patterns': type('MockPatterns', (), {
                'patterns': [
                    type('MockPattern', (), {
                        'direction': type('MockDirection', (), {'value': 'bullish'})(),
                        'confidence': 0.8
                    })()
                ]
            })(),
            'suggestions': type('MockSuggestions', (), {
                'suggestions': [
                    type('MockSuggestion', (), {
                        'suggestion_type': type('MockType', (), {'value': 'buy'})(),
                        'confidence': 0.8
                    })()
                ],
                'get_strongest_suggestion': lambda self: self.suggestions[0]
            })()
        }
        
        # Test the executive summary function
        summary = generate_executive_summary(analysis_results)
        
        print("✅ Executive Summary Test Passed!")
        print(f"📊 Summary keys: {list(summary.keys())}")
        print(f"📈 Stocks analyzed: {len(summary.get('stocks_analyzed', []))}")
        print(f"🎯 Overall sentiment: {summary.get('overall_market_sentiment')}")
        print(f"📊 Confidence score: {summary.get('confidence_score'):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Executive Summary Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Finance Tools Test Suite")
    print("=" * 60)
    
    # Test basic functionality
    basic_success = test_basic_analysis()
    
    # Test executive summary
    summary_success = test_executive_summary()
    
    if basic_success and summary_success:
        print("\n🎉 All tests passed!")
        print("✅ Basic analysis functionality working")
        print("✅ Executive summary functionality working")
        print("✅ Portfolio optimization types imported")
        print("✅ Signal types imported")
    else:
        print("\n💥 Some tests failed!")
        if not basic_success:
            print("❌ Basic analysis tests failed")
        if not summary_success:
            print("❌ Executive summary tests failed")

if __name__ == "__main__":
    main() 