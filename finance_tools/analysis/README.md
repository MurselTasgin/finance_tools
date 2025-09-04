# Technical Analysis Module

A comprehensive technical analysis module for financial data analysis, providing a wide range of technical indicators and tools for stocks and ETFs.

## Features

### Technical Indicators

#### Moving Averages
- **EMA (Exponential Moving Average)** - Weighted average that gives more importance to recent prices
- **SMA (Simple Moving Average)** - Arithmetic mean of prices over a specified period
- **WMA (Weighted Moving Average)** - Moving average with linearly increasing weights

#### Momentum Indicators
- **RSI (Relative Strength Index)** - Measures the speed and magnitude of price changes
- **MACD (Moving Average Convergence Divergence)** - Trend-following momentum indicator
- **Stochastic Oscillator** - Momentum indicator comparing closing price to price range
- **Momentum** - Rate of change in price over time
- **ROC (Rate of Change)** - Percentage change in price over time
- **CCI (Commodity Channel Index)** - Measures price variations from statistical mean

#### Volatility Indicators
- **Bollinger Bands** - Volatility indicator with upper and lower bands
- **ATR (Average True Range)** - Measures market volatility

#### Trend Indicators
- **Supertrend** - Trend-following indicator with dynamic support/resistance
- **ADX (Average Directional Index)** - Measures trend strength

#### Volume Indicators
- **OBV (On-Balance Volume)** - Volume-based momentum indicator
- **VWAP (Volume Weighted Average Price)** - Volume-weighted average price

#### Support/Resistance
- **Support/Resistance Levels** - Dynamic support and resistance calculation

## Installation

The module is part of the finance_tools package. No additional installation is required.

## Quick Start

```python
import pandas as pd
from finance_tools.analysis import (
    calculate_ema, calculate_rsi, calculate_macd,
    TechnicalAnalysis, prepare_data_for_analysis
)

# Create sample data
data = pd.DataFrame({
    'open': [100, 101, 102, 101, 103],
    'high': [102, 103, 104, 103, 105],
    'low': [99, 100, 101, 100, 102],
    'close': [101, 102, 103, 102, 104],
    'volume': [1000000, 1100000, 1200000, 1150000, 1250000]
}, index=pd.date_range('2023-01-01', periods=5))

# Prepare data
data = prepare_data_for_analysis(data, symbol="AAPL")

# Calculate individual indicators
ema_20 = calculate_ema(data['close'], 20)
rsi = calculate_rsi(data['close'], 14)
macd_line, signal_line, histogram = calculate_macd(data['close'])

# Use the comprehensive TechnicalAnalysis class
ta = TechnicalAnalysis()
indicators = ta.calculate_all_indicators(data)
signals = ta.get_trading_signals(data)

print(f"RSI: {rsi.iloc[-1]:.2f}")
print(f"MACD: {macd_line.iloc[-1]:.4f}")
print(f"Trading Signals: {signals}")
```

## Advanced Usage

### Configuration

```python
from finance_tools.analysis import AnalysisConfig, get_config

# Get default configuration
config = get_config()

# Create custom configuration
custom_config = AnalysisConfig(
    min_data_points=50,
    default_rsi_period=21,
    default_macd_fast=8,
    default_macd_slow=21,
    rsi_oversold=25.0,
    rsi_overbought=75.0
)
```

### Data Validation and Cleaning

```python
from finance_tools.analysis import validate_ohlcv_data, clean_data

# Validate data
validate_ohlcv_data(data)

# Clean data (handle missing values and outliers)
cleaned_data = clean_data(data, method="drop")
```

### Performance Analysis

```python
from finance_tools.analysis import calculate_performance_metrics, create_summary_report

# Calculate performance metrics
metrics = calculate_performance_metrics(data['close'])

# Create comprehensive report
report = create_summary_report(data, indicators, signals)
print(f"Total Return: {metrics['total_return']:.2f}%")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.4f}")
```

### Export Results

```python
from finance_tools.analysis import export_results

# Export to different formats
export_results(indicators, "analysis_results.json", "json")
export_results(indicators, "analysis_results.xlsx", "excel")
```

## Module Structure

```
finance_tools/analysis/
├── __init__.py              # Main module exports
├── analysis.py              # Core technical indicators
├── config.py                # Configuration management
├── utils.py                 # Utility functions
├── example_usage.py         # Usage examples
├── test_analysis.py         # Test suite
└── README.md               # This file
```

## Technical Indicators Reference

### Moving Averages

#### EMA (Exponential Moving Average)
```python
ema = calculate_ema(prices, period=20)
```
- **Parameters**: `prices` (pd.Series), `period` (int)
- **Returns**: pd.Series with EMA values
- **Default period**: 20

#### SMA (Simple Moving Average)
```python
sma = calculate_sma(prices, period=20)
```
- **Parameters**: `prices` (pd.Series), `period` (int)
- **Returns**: pd.Series with SMA values
- **Default period**: 20

### Momentum Indicators

#### RSI (Relative Strength Index)
```python
rsi = calculate_rsi(prices, period=14)
```
- **Parameters**: `prices` (pd.Series), `period` (int)
- **Returns**: pd.Series with RSI values (0-100)
- **Default period**: 14
- **Overbought level**: 70
- **Oversold level**: 30

#### MACD (Moving Average Convergence Divergence)
```python
macd_line, signal_line, histogram = calculate_macd(
    prices, fast_period=12, slow_period=26, signal_period=9
)
```
- **Parameters**: `prices` (pd.Series), `fast_period`, `slow_period`, `signal_period` (int)
- **Returns**: Tuple of (macd_line, signal_line, histogram)
- **Default periods**: 12, 26, 9

### Volatility Indicators

#### Bollinger Bands
```python
upper, middle, lower = calculate_bollinger_bands(
    prices, period=20, std_dev=2.0
)
```
- **Parameters**: `prices` (pd.Series), `period` (int), `std_dev` (float)
- **Returns**: Tuple of (upper_band, middle_band, lower_band)
- **Default period**: 20
- **Default std_dev**: 2.0

#### ATR (Average True Range)
```python
atr = calculate_atr(high, low, close, period=14)
```
- **Parameters**: `high`, `low`, `close` (pd.Series), `period` (int)
- **Returns**: pd.Series with ATR values
- **Default period**: 14

### Trend Indicators

#### Supertrend
```python
supertrend, trend = calculate_supertrend(
    high, low, close, period=10, multiplier=3.0
)
```
- **Parameters**: `high`, `low`, `close` (pd.Series), `period` (int), `multiplier` (float)
- **Returns**: Tuple of (supertrend_line, trend_direction)
- **Default period**: 10
- **Default multiplier**: 3.0

#### ADX (Average Directional Index)
```python
adx, di_plus, di_minus = calculate_adx(high, low, close, period=14)
```
- **Parameters**: `high`, `low`, `close` (pd.Series), `period` (int)
- **Returns**: Tuple of (adx, di_plus, di_minus)
- **Default period**: 14

### Volume Indicators

#### OBV (On-Balance Volume)
```python
obv = calculate_obv(close, volume)
```
- **Parameters**: `close`, `volume` (pd.Series)
- **Returns**: pd.Series with OBV values

#### VWAP (Volume Weighted Average Price)
```python
vwap = calculate_vwap(high, low, close, volume)
```
- **Parameters**: `high`, `low`, `close`, `volume` (pd.Series)
- **Returns**: pd.Series with VWAP values

## Trading Signals

The module automatically generates trading signals based on technical indicators:

- **RSI Signals**: BUY when RSI < 30, SELL when RSI > 70
- **MACD Signals**: BUY when MACD line > Signal line, SELL otherwise
- **Bollinger Bands Signals**: BUY when price < lower band, SELL when price > upper band
- **Supertrend Signals**: BUY when trend is UP, SELL when trend is DOWN
- **Moving Average Signals**: BUY when EMA(50) > EMA(200), SELL otherwise

## Error Handling

The module includes comprehensive error handling:

- **Data validation**: Ensures OHLCV data integrity
- **Parameter validation**: Validates indicator parameters
- **Missing data handling**: Multiple strategies for handling missing values
- **Outlier detection**: Automatic detection and handling of price outliers

## Performance Considerations

- **Caching**: Optional caching for repeated calculations
- **Parallel processing**: Support for parallel indicator calculation
- **Memory efficient**: Optimized for large datasets
- **Configurable**: Adjustable performance settings

## Testing

Run the test suite to verify functionality:

```python
from finance_tools.analysis.test_analysis import run_tests

success = run_tests()
if success:
    print("All tests passed!")
else:
    print("Some tests failed!")
```

## Examples

See `example_usage.py` for comprehensive examples demonstrating:

- Basic indicator calculations
- Comprehensive analysis workflows
- Advanced indicator usage
- Configuration management
- Data export functionality

## Contributing

When adding new indicators:

1. Follow the modular design pattern
2. Include proper error handling
3. Add comprehensive tests
4. Update documentation
5. Follow the existing code style

## License

Part of the finance_tools package. See main package license for details. 