# EMA Regime Indicators Implementation

## Summary

Successfully integrated the EMA regime indicators from `additional_indicators.py` (experimental library) into the main `indicators.py` file. This implementation adds comprehensive trend-following indicators with regime filters, extension detection, and volume confirmation.

## What Was Implemented

### 1. New Indicator: `ema_regime_signals`

Added a comprehensive indicator that computes multiple signals based on EMA-20 (fast), EMA-50 (slow), and EMA-200 (regime).

### 2. Core Features Implemented

#### EMA Calculations
- **EMA-20** (fast): Short-term trend indicator
- **EMA-50** (slow): Medium-term trend indicator
- **EMA-200** (regime): Long-term trend filter

#### Cross Signals
- **Price x EMA-fast**: Signals when price crosses above/below EMA-20
- **EMA-fast x EMA-slow**: Signals when EMA-20 crosses EMA-50
- **Price x EMA-regime**: Signals when price crosses above/below EMA-200
- **EMA-slow x EMA-regime**: Golden Cross (50 above 200) and Death Cross (50 below 200)

#### Regime Filters
- **Regime_Long**: Close > EMA-200 AND EMA-50 > EMA-200 (uptrend context)
- **Regime_Short**: Close < EMA-200 AND EMA-50 < EMA-200 (downtrend context)

#### Extension Filter (Avoid Stretched Moves)
- Computes `|Close - EMA-20| / ATR`
- Default threshold: 1.5 (configurable via `max_ext_atr`)
- `not_extended` signal flags when price is not too stretched from EMA-20

#### Volume Confirmation
- Volume SMA calculated (default 20 periods)
- Volume must be >= `min_vol_mult * Volume_SMA` (default 1.2x)
- Ensures volume supports the signal

#### Slope Filters
- `slow_ema_slope_up`: EMA-50 rising (compares current vs 3 periods ago)
- `slow_ema_slope_dn`: EMA-50 declining
- Reduces false signal flip-flops

#### Composite Entry Conditions
- **Long Entry (price x fast)**: Price crosses above EMA-20 + Regime Long + Slow EMA Slope Up + Not Extended + Volume Confirm
- **Long Entry (fast x slow)**: EMA-20 crosses EMA-50 + Regime Long + Slow EMA Slope Up + Not Extended + Volume Confirm
- **Short Entry (price x fast)**: Price crosses below EMA-20 + Regime Short + Slow EMA Slope Down + Not Extended + Volume Confirm
- **Short Entry (fast x slow)**: EMA-20 crosses below EMA-50 + Regime Short + Slow EMA Slope Down + Not Extended + Volume Confirm

### 3. Helper Functions Added

- `_crossed_above()`: Detects when series A crosses above series B
- `_crossed_below()`: Detects when series A crosses below series B

### 4. Output Columns

When `ema_regime_signals` is computed, the following columns are added:

**EMA Series:**
- `{column}_ema_20`
- `{column}_ema_50`
- `{column}_ema_200`

**Cross Signals (int):**
- `{column}_sig_price_above_fast`
- `{column}_sig_price_below_fast`
- `{column}_sig_fast_above_slow`
- `{column}_sig_fast_below_slow`
- `{column}_sig_price_above_regime`
- `{column}_sig_price_below_regime`
- `{column}_golden_cross`
- `{column}_death_cross`

**Regime Filters (int):**
- `{column}_regime_long`
- `{column}_regime_short`

**Slope Filters (int):**
- `{column}_slow_ema_slope_up`
- `{column}_slow_ema_slope_dn`

**Extension & Volume (int):**
- `{column}_dist_fast_atr`
- `{column}_not_extended`
- `{column}_vol_confirm`

**Composite Entry Signals (int):**
- `{column}_long_entry_price_x_fast`
- `{column}_long_entry_fast_x_slow`
- `{column}_short_entry_price_x_fast`
- `{column}_short_entry_fast_x_slow`

**ATR (if not already present):**
- `{column}_atr`

**Volume SMA:**
- `volume_sma_20`

## Usage Example

```python
from finance_tools.stocks.analysis.indicators import StockTechnicalIndicatorCalculator

calculator = StockTechnicalIndicatorCalculator()

# Default parameters
indicators = {
    "ema_regime_signals": {}
}

# Custom parameters
indicators = {
    "ema_regime_signals": {
        "fast": 20,           # EMA-fast period
        "slow": 50,           # EMA-slow period
        "regime": 200,        # EMA-regime period
        "max_ext_atr": 1.5,   # Max extension threshold
        "min_vol_mult": 1.2,  # Minimum volume multiplier
        "vol_sma": 20,        # Volume SMA period
        "atr_period": 14      # ATR period
    }
}

result = calculator.compute(df, "close", indicators)
```

## Key Differences from Original Implementation

1. **Integrated into existing class structure**: Uses `StockTechnicalIndicatorCalculator` instead of standalone functions
2. **Uses ta library**: Leverages `ta` library's `EMAIndicator` and `AverageTrueRange` classes
3. **Flexible column naming**: Uses `{column}` prefix pattern consistent with existing indicators
4. **Configurable parameters**: All thresholds and periods are configurable via params dict
5. **Missing data handling**: Gracefully handles missing high/low/volume data
6. **Output format**: Returns int (0/1) for signal columns instead of boolean

## Technical Notes

- All cross signals detect the exact bar where the cross occurs (no look-ahead bias)
- ATR is computed automatically if high/low data is available
- Volume SMA is computed if volume data is available
- If required data (high/low/volume) is missing, related signals are set to 0
- Extension filter uses ATR to normalize distance from EMA-20
- All signals are returned as integers (0 or 1) for database compatibility
