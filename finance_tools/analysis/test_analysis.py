# finance_tools/analysis/test_analysis.py
"""
Test suite for the technical analysis module.

This module contains comprehensive tests for all technical indicators
and utility functions in the analysis module.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Import modules to test
from .analysis import (
    calculate_ema, calculate_sma, calculate_wma, calculate_rsi, calculate_macd,
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
from .config import AnalysisConfig, get_config

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class TestDataPreparation(unittest.TestCase):
    """Test data preparation and validation functions."""
    
    def setUp(self):
        """Set up test data."""
        # Create sample OHLCV data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        base_price = 100.0
        prices = [base_price]
        for _ in range(len(dates) - 1):
            new_price = prices[-1] * (1 + np.random.normal(0, 0.02))
            prices.append(new_price)
        
        self.test_data = pd.DataFrame({
            'open': [p * (1 + np.random.normal(0, 0.01)) for p in prices],
            'high': [p * (1 + abs(np.random.normal(0, 0.02))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.02))) for p in prices],
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        # Ensure OHLC relationships
        self.test_data['high'] = self.test_data[['open', 'high', 'close']].max(axis=1)
        self.test_data['low'] = self.test_data[['open', 'low', 'close']].min(axis=1)
    
    def test_validate_ohlcv_data(self):
        """Test OHLCV data validation."""
        # Test valid data
        self.assertTrue(validate_ohlcv_data(self.test_data))
        
        # Test invalid data types
        invalid_data = self.test_data.copy()
        invalid_data['close'] = 'invalid'
        with self.assertRaises(ValueError):
            validate_ohlcv_data(invalid_data)
        
        # Test missing columns
        invalid_data = self.test_data.drop('close', axis=1)
        with self.assertRaises(ValueError):
            validate_ohlcv_data(invalid_data)
        
        # Test negative prices
        invalid_data = self.test_data.copy()
        invalid_data.loc[0, 'close'] = -10
        with self.assertRaises(ValueError):
            validate_ohlcv_data(invalid_data)
    
    def test_clean_data(self):
        """Test data cleaning function."""
        # Add some missing values
        dirty_data = self.test_data.copy()
        dirty_data.loc[10:15, 'close'] = np.nan
        
        # Test drop method
        cleaned_data = clean_data(dirty_data, method='drop')
        self.assertFalse(cleaned_data.isnull().any().any())
        
        # Test forward fill method
        cleaned_data = clean_data(dirty_data, method='forward_fill')
        self.assertFalse(cleaned_data.isnull().any().any())
    
    def test_prepare_data_for_analysis(self):
        """Test data preparation function."""
        prepared_data = prepare_data_for_analysis(
            self.test_data, 
            symbol="TEST",
            start_date="2023-06-01",
            end_date="2023-06-30"
        )
        
        self.assertIn('symbol', prepared_data.columns)
        self.assertEqual(prepared_data['symbol'].iloc[0], "TEST")
        self.assertTrue(len(prepared_data) <= 30)  # June has 30 days


class TestMovingAverages(unittest.TestCase):
    """Test moving average functions."""
    
    def setUp(self):
        """Set up test data."""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        self.prices = pd.Series(
            [100 + i * 0.1 + np.random.normal(0, 1) for i in range(len(dates))],
            index=dates
        )
    
    def test_calculate_ema(self):
        """Test EMA calculation."""
        ema_20 = calculate_ema(self.prices, 20)
        
        self.assertEqual(len(ema_20), len(self.prices))
        self.assertTrue(ema_20.notna().any())  # Should have some non-NaN values
        self.assertTrue(ema_20.iloc[-1] > 0)  # Should be positive
        
        # Test with invalid period
        with self.assertRaises(ValueError):
            calculate_ema(self.prices, 0)
    
    def test_calculate_sma(self):
        """Test SMA calculation."""
        sma_20 = calculate_sma(self.prices, 20)
        
        self.assertEqual(len(sma_20), len(self.prices))
        self.assertTrue(sma_20.notna().any())
        self.assertTrue(sma_20.iloc[-1] > 0)
        
        # Test with invalid period
        with self.assertRaises(ValueError):
            calculate_sma(self.prices, 0)
    
    def test_calculate_wma(self):
        """Test WMA calculation."""
        wma_20 = calculate_wma(self.prices, 20)
        
        self.assertEqual(len(wma_20), len(self.prices))
        self.assertTrue(wma_20.notna().any())
        self.assertTrue(wma_20.iloc[-1] > 0)


class TestMomentumIndicators(unittest.TestCase):
    """Test momentum indicator functions."""
    
    def setUp(self):
        """Set up test data."""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        self.prices = pd.Series(
            [100 + i * 0.1 + np.random.normal(0, 1) for i in range(len(dates))],
            index=dates
        )
    
    def test_calculate_rsi(self):
        """Test RSI calculation."""
        rsi = calculate_rsi(self.prices, 14)
        
        self.assertEqual(len(rsi), len(self.prices))
        self.assertTrue(rsi.notna().any())
        # RSI should be between 0 and 100
        self.assertTrue(0 <= rsi.iloc[-1] <= 100)
        
        # Test with invalid period
        with self.assertRaises(ValueError):
            calculate_rsi(self.prices, 1)
    
    def test_calculate_macd(self):
        """Test MACD calculation."""
        macd_line, signal_line, histogram = calculate_macd(self.prices)
        
        self.assertEqual(len(macd_line), len(self.prices))
        self.assertEqual(len(signal_line), len(self.prices))
        self.assertEqual(len(histogram), len(self.prices))
        
        # Test with invalid parameters
        with self.assertRaises(ValueError):
            calculate_macd(self.prices, fast_period=26, slow_period=12)
    
    def test_calculate_momentum(self):
        """Test momentum calculation."""
        momentum = calculate_momentum(self.prices, 10)
        
        self.assertEqual(len(momentum), len(self.prices))
        self.assertTrue(momentum.notna().any())
    
    def test_calculate_roc(self):
        """Test ROC calculation."""
        roc = calculate_roc(self.prices, 10)
        
        self.assertEqual(len(roc), len(self.prices))
        self.assertTrue(roc.notna().any())


class TestVolatilityIndicators(unittest.TestCase):
    """Test volatility indicator functions."""
    
    def setUp(self):
        """Set up test data."""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        self.data = pd.DataFrame({
            'open': [100 + np.random.normal(0, 1) for _ in range(len(dates))],
            'high': [102 + np.random.normal(0, 1) for _ in range(len(dates))],
            'low': [98 + np.random.normal(0, 1) for _ in range(len(dates))],
            'close': [100 + np.random.normal(0, 1) for _ in range(len(dates))],
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        # Ensure OHLC relationships
        self.data['high'] = self.data[['open', 'high', 'close']].max(axis=1)
        self.data['low'] = self.data[['open', 'low', 'close']].min(axis=1)
    
    def test_calculate_bollinger_bands(self):
        """Test Bollinger Bands calculation."""
        upper, middle, lower = calculate_bollinger_bands(self.data['close'])
        
        self.assertEqual(len(upper), len(self.data))
        self.assertEqual(len(middle), len(self.data))
        self.assertEqual(len(lower), len(self.data))
        
        # Upper band should be higher than lower band
        self.assertTrue(upper.iloc[-1] > lower.iloc[-1])
        
        # Test with invalid std_dev
        with self.assertRaises(ValueError):
            calculate_bollinger_bands(self.data['close'], std_dev=0)
    
    def test_calculate_atr(self):
        """Test ATR calculation."""
        atr = calculate_atr(self.data['high'], self.data['low'], self.data['close'])
        
        self.assertEqual(len(atr), len(self.data))
        self.assertTrue(atr.notna().any())
        self.assertTrue(atr.iloc[-1] > 0)  # ATR should be positive


class TestTrendIndicators(unittest.TestCase):
    """Test trend indicator functions."""
    
    def setUp(self):
        """Set up test data."""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        self.data = pd.DataFrame({
            'open': [100 + np.random.normal(0, 1) for _ in range(len(dates))],
            'high': [102 + np.random.normal(0, 1) for _ in range(len(dates))],
            'low': [98 + np.random.normal(0, 1) for _ in range(len(dates))],
            'close': [100 + np.random.normal(0, 1) for _ in range(len(dates))],
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        # Ensure OHLC relationships
        self.data['high'] = self.data[['open', 'high', 'close']].max(axis=1)
        self.data['low'] = self.data[['open', 'low', 'close']].min(axis=1)
    
    def test_calculate_supertrend(self):
        """Test Supertrend calculation."""
        supertrend, trend = calculate_supertrend(
            self.data['high'], 
            self.data['low'], 
            self.data['close']
        )
        
        self.assertEqual(len(supertrend), len(self.data))
        self.assertEqual(len(trend), len(self.data))
        self.assertTrue(supertrend.notna().any())
        
        # Trend should be 1 (up) or -1 (down)
        self.assertIn(trend.iloc[-1], [1, -1])
    
    def test_calculate_adx(self):
        """Test ADX calculation."""
        adx, di_plus, di_minus = calculate_adx(
            self.data['high'], 
            self.data['low'], 
            self.data['close']
        )
        
        self.assertEqual(len(adx), len(self.data))
        self.assertEqual(len(di_plus), len(self.data))
        self.assertEqual(len(di_minus), len(self.data))
        
        # ADX should be between 0 and 100
        self.assertTrue(0 <= adx.iloc[-1] <= 100)


class TestVolumeIndicators(unittest.TestCase):
    """Test volume indicator functions."""
    
    def setUp(self):
        """Set up test data."""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        self.data = pd.DataFrame({
            'open': [100 + np.random.normal(0, 1) for _ in range(len(dates))],
            'high': [102 + np.random.normal(0, 1) for _ in range(len(dates))],
            'low': [98 + np.random.normal(0, 1) for _ in range(len(dates))],
            'close': [100 + np.random.normal(0, 1) for _ in range(len(dates))],
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        # Ensure OHLC relationships
        self.data['high'] = self.data[['open', 'high', 'close']].max(axis=1)
        self.data['low'] = self.data[['open', 'low', 'close']].min(axis=1)
    
    def test_calculate_obv(self):
        """Test OBV calculation."""
        obv = calculate_obv(self.data['close'], self.data['volume'])
        
        self.assertEqual(len(obv), len(self.data))
        self.assertTrue(obv.notna().any())
        self.assertTrue(obv.iloc[-1] > 0)  # OBV should be positive
    
    def test_calculate_vwap(self):
        """Test VWAP calculation."""
        vwap = calculate_vwap(
            self.data['high'], 
            self.data['low'], 
            self.data['close'], 
            self.data['volume']
        )
        
        self.assertEqual(len(vwap), len(self.data))
        self.assertTrue(vwap.notna().any())
        self.assertTrue(vwap.iloc[-1] > 0)  # VWAP should be positive


class TestTechnicalAnalysisClass(unittest.TestCase):
    """Test the TechnicalAnalysis class."""
    
    def setUp(self):
        """Set up test data."""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        self.data = pd.DataFrame({
            'open': [100 + np.random.normal(0, 1) for _ in range(len(dates))],
            'high': [102 + np.random.normal(0, 1) for _ in range(len(dates))],
            'low': [98 + np.random.normal(0, 1) for _ in range(len(dates))],
            'close': [100 + np.random.normal(0, 1) for _ in range(len(dates))],
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        # Ensure OHLC relationships
        self.data['high'] = self.data[['open', 'high', 'close']].max(axis=1)
        self.data['low'] = self.data[['open', 'low', 'close']].min(axis=1)
        
        self.ta = TechnicalAnalysis()
    
    def test_calculate_all_indicators(self):
        """Test calculating all indicators."""
        indicators = self.ta.calculate_all_indicators(self.data)
        
        self.assertIsInstance(indicators, dict)
        self.assertTrue(len(indicators) > 0)
        
        # Check that key indicators are present
        expected_indicators = ['ema_12', 'ema_26', 'sma_20', 'rsi', 'macd_line']
        for indicator in expected_indicators:
            self.assertIn(indicator, indicators)
    
    def test_get_trading_signals(self):
        """Test trading signal generation."""
        signals = self.ta.get_trading_signals(self.data)
        
        self.assertIsInstance(signals, dict)
        self.assertTrue(len(signals) > 0)
        
        # Check signal values
        for signal_name, signal_value in signals.items():
            self.assertIn(signal_value, ['BUY', 'SELL', 'NEUTRAL'])
    
    def test_validation_settings(self):
        """Test validation settings."""
        self.ta.set_validation(validate=True, min_points=50)
        
        # Test with insufficient data
        small_data = self.data.head(30)
        with self.assertRaises(ValueError):
            self.ta.calculate_all_indicators(small_data)


class TestConfiguration(unittest.TestCase):
    """Test configuration functionality."""
    
    def test_analysis_config(self):
        """Test AnalysisConfig class."""
        config = AnalysisConfig()
        
        self.assertEqual(config.min_data_points, 30)
        self.assertEqual(config.default_rsi_period, 14)
        self.assertEqual(config.default_macd_fast, 12)
        self.assertEqual(config.default_macd_slow, 26)
        
        # Test validation
        with self.assertRaises(ValueError):
            AnalysisConfig(min_data_points=5)  # Too small
        
        with self.assertRaises(ValueError):
            AnalysisConfig(rsi_oversold=80, rsi_overbought=70)  # Invalid range
    
    def test_get_config(self):
        """Test get_config function."""
        config = get_config()
        
        self.assertIsInstance(config, AnalysisConfig)
        self.assertTrue(config.min_data_points >= 10)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def setUp(self):
        """Set up test data."""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        self.data = pd.DataFrame({
            'open': [100 + np.random.normal(0, 1) for _ in range(len(dates))],
            'high': [102 + np.random.normal(0, 1) for _ in range(len(dates))],
            'low': [98 + np.random.normal(0, 1) for _ in range(len(dates))],
            'close': [100 + np.random.normal(0, 1) for _ in range(len(dates))],
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        # Ensure OHLC relationships
        self.data['high'] = self.data[['open', 'high', 'close']].max(axis=1)
        self.data['low'] = self.data[['open', 'low', 'close']].min(axis=1)
    
    def test_format_analysis_results(self):
        """Test result formatting."""
        results = {
            'ema_20': pd.Series([100.1, 100.2, 100.3]),
            'rsi': pd.Series([50.1, 50.2, 50.3]),
            'test_value': 42.123456
        }
        
        formatted = format_analysis_results(results, round_decimals=2)
        
        self.assertIn('metadata', formatted)
        self.assertEqual(formatted['test_value'], 42.12)
    
    def test_calculate_performance_metrics(self):
        """Test performance metrics calculation."""
        prices = pd.Series([100, 101, 102, 101, 103])
        signals = pd.Series(['BUY', 'HOLD', 'SELL', 'BUY', 'HOLD'])
        
        metrics = calculate_performance_metrics(prices, signals)
        
        self.assertIn('total_return', metrics)
        self.assertIn('current_price', metrics)
        self.assertIn('max_price', metrics)
        self.assertIn('min_price', metrics)
        self.assertIn('buy_signals', metrics)
        self.assertIn('sell_signals', metrics)
    
    def test_create_summary_report(self):
        """Test summary report creation."""
        indicators = {
            'rsi': pd.Series([50, 51, 52]),
            'ema_20': pd.Series([100, 101, 102])
        }
        signals = {'rsi_signal': 'BUY', 'macd_signal': 'SELL'}
        
        report = create_summary_report(self.data, indicators, signals)
        
        self.assertIn('data_summary', report)
        self.assertIn('price_summary', report)
        self.assertIn('indicators_summary', report)
        self.assertIn('signals_summary', report)


def run_tests():
    """Run all tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestDataPreparation,
        TestMovingAverages,
        TestMomentumIndicators,
        TestVolatilityIndicators,
        TestTrendIndicators,
        TestVolumeIndicators,
        TestTechnicalAnalysisClass,
        TestConfiguration,
        TestUtilityFunctions
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    if success:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed!") 