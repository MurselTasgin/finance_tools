# test_executive_summary.py
"""
Test script for the executive summary functionality.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(__file__))

try:
    from finance_tools.analysis.example_usage import generate_executive_summary
    from finance_tools.analysis.analysis import calculate_ema, calculate_rsi
    
    # Create mock analysis results
    def create_mock_data():
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
    
    def test_executive_summary():
        """Test the executive summary function."""
        print("Testing Executive Summary Function")
        print("=" * 50)
        
        # Create mock analysis results
        mock_data = create_mock_data()
        
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
        try:
            summary = generate_executive_summary(analysis_results)
            
            print("\n✅ Executive Summary Test Passed!")
            print(f"Summary keys: {list(summary.keys())}")
            print(f"Stocks analyzed: {len(summary.get('stocks_analyzed', []))}")
            print(f"Overall sentiment: {summary.get('overall_market_sentiment')}")
            print(f"Confidence score: {summary.get('confidence_score'):.1f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ Executive Summary Test Failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    if __name__ == "__main__":
        success = test_executive_summary()
        if success:
            print("\n🎉 All tests passed!")
        else:
            print("\n💥 Tests failed!")
            
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you have the required dependencies installed.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 