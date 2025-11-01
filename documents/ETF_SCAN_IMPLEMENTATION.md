# ETF Scan Analysis Implementation

## Overview
Implemented the ETF Scan Analysis form component based on the CLI implementation in `@cli.py` to provide a comprehensive UI for running ETF scans with buy/sell/hold signals.

## Files Created

### 1. `frontend/src/components/ETFScanAnalysisForm.tsx`
Complete form component for configuring and running ETF scans with the following sections:

#### Basic Parameters
- **Fund Codes**: Multi-input field to specify which ETFs/funds to scan (e.g., NNF, YAC)
- **Date Range**: Start and end dates for the scan period
- **Column Selection**: Choose which metric to analyze (price, market_cap, etc.)

#### Filters
- **Include Keywords**: Fund names must contain these keywords
- **Exclude Keywords**: Fund names must NOT contain these keywords
- **Case Sensitive**: Toggle case sensitivity for keyword matching
- **Match All Includes**: Require all include keywords to match (AND logic)

#### Indicator Parameters
- **EMA Parameters**: Short and long window periods (default: 20, 50)
- **MACD Parameters**: Slow, Fast, Signal periods (default: 26, 12, 9)
- **RSI Parameters**: Window and thresholds (default: 14, lower: 30, upper: 70)

#### Weights & Thresholds
- **Indicator Weights**: Adjust importance of each signal
  - Weight EMA (default: 1.0)
  - Weight MACD (default: 1.0)
  - Weight RSI (default: 1.0)
  - Weight Momentum (default: 1.0)
- **Score Thresholds**: 
  - Buy Threshold (default: 1.0)
  - Sell Threshold (default: 1.0)

#### Advanced Features
- **Momentum Indicators**: Optional momentum and daily momentum components
- **Supertrend**: Optional supertrend indicator with:
  - HL Factor (synthetic high-low multiplier)
  - ATR Period (Average True Range period)
  - Multiplier (for band calculation)

## Files Modified

### `frontend/src/components/AnalyticsDashboard.tsx`
1. Added import for `ETFScanAnalysisForm`
2. Updated `ETFScanAnalysisPanel` to use the new form component
3. Properly wraps parameters to match backend API expectations

## Backend Integration

The form sends parameters to the backend in the following format:

```typescript
{
  codes: string[];                    // Fund codes to scan
  start_date: string;                 // YYYY-MM-DD format
  end_date: string;                   // YYYY-MM-DD format
  column: string;                     // Column to analyze
  include_keywords?: string[];        // Optional
  exclude_keywords?: string[];        // Optional
  case_sensitive: boolean;
  all_includes: boolean;
  ema_short: number;
  ema_long: number;
  macd_slow: number;
  macd_fast: number;
  macd_sign: number;
  rsi_window: number;
  rsi_lower: number;
  rsi_upper: number;
  w_ema: number;                      // Weights
  w_macd: number;
  w_rsi: number;
  w_momentum: number;
  w_momentum_daily: number;
  w_supertrend: number;
  buy_threshold: number;
  sell_threshold: number;
  st_hl_factor?: number;              // Supertrend params
  st_atr?: number;
  st_multiplier?: number;
}
```

## API Endpoint
- **Endpoint**: `POST /api/analytics/etf/scan`
- **Parameters**: Full configuration object (see above)
- **Response**: Analysis results with buy/sell/hold suggestions and scores

## Usage Flow

1. User navigates to "ETF Scan" tab in Analytics Dashboard
2. Configures fund codes, date range, and filters
3. Selects indicators and adjusts weights
4. Clicks "Run ETF Scan Analysis" button
5. Results are displayed showing:
   - Fund codes
   - Signal recommendations (BUY/SELL/HOLD)
   - Composite scores
   - Individual indicator signals

## CLI Integration
The parameters map directly to the CLI implementation in `@cli.py`:
- `handle_etf_scan()` function processes these parameters
- Uses `EtfAnalyzer` and `EtfScanner` for calculations
- Generates buy/sell/hold suggestions based on weighted scoring

## Status
✅ Frontend component created and compiles successfully
✅ Integrated with AnalyticsDashboard
✅ Full parameter support matching CLI implementation
✅ Ready for backend integration testing

## Next Steps
1. Test with backend API
2. Verify analysis results display correctly
3. Add visualization/charting for scan results
4. Add export functionality for scan results
