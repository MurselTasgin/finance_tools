#!/usr/bin/env python3
"""
Test script for unified indicator registry.

Verifies:
1. Registry auto-discovers indicators
2. RSI is registered and available
3. Asset type filtering works
4. Column auto-detection works
"""

import pandas as pd
from datetime import datetime, timedelta
from finance_tools.analysis.indicators import registry, IndicatorConfig
from finance_tools.analysis.indicators.base import BaseIndicator


def test_registry_discovery():
    """Test that indicators are auto-discovered"""
    print("\n=== Testing Registry Discovery ===")
    
    all_indicators = registry.get_all()
    print(f"✅ Registered indicators: {len(all_indicators)}")
    for ind_id, indicator in all_indicators.items():
        print(f"  - {ind_id}: {indicator.get_name()}")
        print(f"    Asset types: {indicator.get_asset_types()}")
    
    # Check all expected indicators
    expected_common = ['rsi', 'macd', 'momentum', 'ema_cross']
    expected_stock = ['adx', 'atr', 'stochastic', 'volume', 'ema_regime', 'sentiment']
    expected_etf = ['supertrend', 'daily_momentum']
    
    expected_indicators = expected_common + expected_stock + expected_etf
    found_indicators = {}
    
    for ind_id in expected_indicators:
        indicator = registry.get(ind_id)
        if indicator:
            found_indicators[ind_id] = indicator
            print(f"\n✅ {ind_id.upper()} found: {indicator.get_name()}")
            print(f"   Supports: {indicator.get_asset_types()}")
        else:
            print(f"\n❌ {ind_id.upper()} NOT found")
    
    return found_indicators


def test_asset_type_filtering():
    """Test filtering by asset type"""
    print("\n=== Testing Asset Type Filtering ===")
    
    stock_indicators = registry.get_by_asset_type('stock')
    etf_indicators = registry.get_by_asset_type('etf')
    universal_indicators = registry.get_by_asset_type('universal')
    
    print(f"Stock indicators: {len(stock_indicators)}")
    print(f"ETF indicators: {len(etf_indicators)}")
    print(f"Universal indicators: {len(universal_indicators)}")
    
    # Test RSI compatibility
    is_stock_compatible = registry.is_compatible('rsi', 'stock')
    is_etf_compatible = registry.is_compatible('rsi', 'etf')
    
    print(f"\nRSI compatibility:")
    print(f"  - Stocks: {is_stock_compatible}")
    print(f"  - ETFs: {is_etf_compatible}")
    
    assert is_stock_compatible and is_etf_compatible, "RSI should be compatible with both"


def test_column_auto_detection():
    """Test auto-detection of price columns"""
    print("\n=== Testing Column Auto-Detection ===")
    
    # Create sample stock data
    stock_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=50),
        'open': [100] * 50,
        'high': [102] * 50,
        'low': [99] * 50,
        'close': [101] * 50,
        'volume': [1000] * 50
    })
    
    # Create sample ETF data
    etf_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=50),
        'price': [10.5] * 50,
        'market_cap': [1000000] * 50,
        'number_of_shares': [100000] * 50
    })
    
    rsi = registry.get('rsi')
    if not rsi:
        print("❌ RSI not available")
        return
    
    # Test stock column detection
    stock_column = rsi.get_price_column(stock_data, 'close')
    print(f"Stock auto-detected column: {stock_column}")
    assert stock_column == 'close', f"Expected 'close', got {stock_column}"
    
    # Test ETF column detection
    etf_column = rsi.get_price_column(etf_data, 'price')
    print(f"ETF auto-detected column: {etf_column}")
    assert etf_column == 'price', f"Expected 'price', got {etf_column}"
    
    # Test asset type detection
    stock_type = rsi.detect_asset_type(stock_data)
    etf_type = rsi.detect_asset_type(etf_data)
    
    print(f"Detected stock type: {stock_type}")
    print(f"Detected ETF type: {etf_type}")
    
    assert stock_type == 'stock', f"Expected 'stock', got {stock_type}"
    assert etf_type == 'etf', f"Expected 'etf', got {etf_type}"
    
    print("✅ Column auto-detection works correctly")


def test_rsi_calculation():
    """Test RSI indicator calculation"""
    print("\n=== Testing RSI Calculation ===")
    
    # Create test data with simulated price movement
    dates = pd.date_range('2024-01-01', periods=30)
    
    # Simulate upward trend
    prices = [100 + i * 0.5 + i % 2 for i in range(30)]
    
    stock_data = pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': [p * 1.02 for p in prices],
        'low': [p * 0.98 for p in prices],
        'close': prices,
        'volume': [1000] * 30
    })
    
    rsi = registry.get('rsi')
    if not rsi:
        print("❌ RSI not available")
        return
    
    # Calculate RSI
    config = IndicatorConfig(
        name='RSI',
        parameters={'window': 14},
        weight=1.0
    )
    
    try:
        enriched = rsi.calculate(stock_data, 'close', config)
        
        # Check RSI column was added
        rsi_col = 'close_rsi_14'
        assert rsi_col in enriched.columns, f"RSI column {rsi_col} not found"
        
        # Get snapshot
        snapshot = rsi.get_snapshot(enriched, 'close', config)
        print(f"RSI snapshot: {snapshot.values}")
        
        # Get score
        score = rsi.get_score(enriched, 'close', config)
        if score:
            print(f"RSI score: {score.contribution:.4f}")
            print(f"Explanation: {score.explanation}")
        
        # Get explanation
        explanation = rsi.explain(enriched, 'close', config)
        print("Explanation:")
        for line in explanation:
            print(f"  {line}")
        
        print("✅ RSI calculation successful")
        
    except Exception as e:
        print(f"❌ RSI calculation failed: {e}")
        raise


def main():
    """Run all tests"""
    print("🧪 Testing Unified Indicator Registry")
    print("=" * 60)
    
    try:
        found_indicators = test_registry_discovery()
        if not found_indicators:
            print("\n❌ Tests cannot continue without indicators")
            return
        
        rsi = found_indicators.get('rsi')
        if not rsi:
            print("\n❌ Tests cannot continue without RSI")
            return
        
        test_asset_type_filtering()
        test_column_auto_detection()
        test_rsi_calculation()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

