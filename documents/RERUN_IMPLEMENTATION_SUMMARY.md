# Stock Scan Analysis Rerun Implementation

## Summary
Implemented the rerun functionality for Stock Scan Analysis that redirects users to the original form with pre-filled parameters from previously run jobs.

## Changes Made

### 1. **Updated Component Props**

#### `AnalysisJobsPanel.tsx`
- Added `AnalysisJobsPanelProps` interface with optional `onRerunRequest` callback
- Updated component to accept `onRerunRequest` prop

#### `AnalysisResultsPanel.tsx`
- Added `AnalysisResultsPanelProps` interface with optional `onRerunRequest` callback
- Updated component to accept `onRerunRequest` prop

#### `StockScanAnalysisForm.tsx`
- Added `initialParameters` and `onParametersUsed` props to `StockScanAnalysisFormProps`
- Updated component to accept these props

### 2. **Implemented Form Pre-population**

#### `StockScanAnalysisForm.tsx`
- Added `useEffect` hook that populates form fields when `initialParameters` is provided
- The hook extracts and sets:
  - Symbols list
  - Start and end dates
  - Analysis column
  - Sector and industry filters
  - Buy and sell thresholds
  - Selected scanners (reconstructed from `scanner_configs` and `weights`)
- Calls `onParametersUsed()` to clear the parameters after use

### 3. **Updated Rerun Handlers**

#### `AnalysisJobsPanel.tsx`
- Modified `rerunMutation` to:
  - Check if `onRerunRequest` callback is provided and analysis type is `stock_scan`
  - If yes, call `onRerunRequest` to navigate to the form with pre-filled parameters
  - Otherwise, use the API to rerun directly
- Updated results dialog's `onRerun` handler to use `onRerunRequest` for `stock_scan` analysis

#### `AnalysisResultsPanel.tsx`
- Updated results viewer's `onRerun` handler to:
  - Check if `onRerunRequest` is provided for `stock_scan` analysis
  - Navigate to form instead of directly rerunning
  - Fall back to API rerun for other analysis types

#### `AnalyticsDashboard.tsx`
- Added `rerunParameters` state to track parameters for pre-filling
- Implemented `handleRerunWithParameters` function that:
  - Stores the parameters
  - Navigates to the appropriate tab based on analysis type (tab 3 for Stock Scan)
- Passes `initialParameters` and `onParametersUsed` to `StockScanAnalysisPanel`

## User Flow

1. User runs a Stock Scan Analysis with specific parameters (dates, stocks, indicators, thresholds)
2. User views the job in "Jobs & History" or "Results & History" tab
3. User clicks the "Rerun" button
4. System redirects user to "Stock Scan Analysis" tab (tab 3)
5. Form is pre-populated with all original parameters:
   - Stock symbols
   - Date range
   - Analysis column
   - Sector/industry filters
   - BUY and SELL thresholds
   - Selected scanners with their configurations and weights
6. User can modify any parameters before running the analysis again

## Technical Details

### Parameter Structure
The `initialParameters` object contains:
```typescript
{
  symbols: string[];
  start_date: string;
  end_date: string;
  column: string;
  sector?: string;
  industry?: string;
  scanners: string[];
  scanner_configs: Record<string, any>;
  weights: Record<string, number>;
  buy_threshold: number;
  sell_threshold: number;
}
```

### Tab Navigation
- Tab 0: ETF Technical Analysis
- Tab 1: ETF Scan Analysis
- Tab 2: Stock Technical Analysis
- Tab 3: Stock Scan Analysis (where users are redirected)
- Tab 4: Jobs & History
- Tab 5: Results & History

## Benefits

1. **User-Friendly**: Users can easily rerun analyses with the same or modified parameters
2. **Transparent**: All original parameters are visible and editable
3. **Flexible**: Users can modify any parameter before rerunning
4. **Consistent**: Uses the same form interface for both new and rerun analyses
5. **Safe**: All parameters are preserved, reducing the risk of errors

