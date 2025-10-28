# Unified Technical Analysis Architecture Plan

## Executive Summary

This document outlines a plan to unify stock and ETF technical analysis systems into a single, cohesive architecture. The goal is to eliminate code duplication, improve maintainability, and enable better code reusability while preserving the plugin-based indicator architecture.

---

## Current State Analysis

### Data Structure Comparison

#### Stock Data (`StockPriceHistory`)
**Columns:**
- `symbol` (str): Stock ticker
- `date` (date): Trading date
- `interval` (str): Timeframe (1d, 1h, 5m, etc.)
- `open`, `high`, `low`, `close` (float): OHLC prices
- `volume` (int): Trading volume
- `dividends`, `stock_splits` (float): Corporate actions

**Frequency:** Daily, hourly, or intraday (configurable)

**Analysis Column:** `close` (uses OHLCV for calculations)

**Indicators Available:**
- EMA Cross (`ema_cross`)
- MACD (`macd`)
- RSI (`rsi`)
- Momentum (`momentum`)
- Stochastic (`stochastic`)
- ATR (`atr`)
- ADX (`adx`)
- Volume (`volume`)
- EMA Regime (`ema_regime`)
- Sentiment (`sentiment`)

#### ETF Data (`TefasFundInfo`)
**Columns:**
- `code` (str): Fund code
- `date` (date): Trading date
- `price` (float): Net asset value
- `title` (str): Fund name
- `market_cap` (float): Portfolio size (PORTFOYBUYUKLUK)
- `number_of_shares` (float): Number of outstanding shares (TEDPAYSAYISI)
- `number_of_investors` (int): Investor count (KISISAYISI)
- `fund_type` (str): BYF, YAT, EMK

**Frequency:** Daily only

**Analysis Column:** `price` (single price point, no OHLCV)

**Additional Metrics Available for Analysis:**
- `market_cap`: Portfolio size (analogous to market capitalization in stocks)
- `number_of_shares`: Outstanding shares (analogous to share count)
- `number_of_investors`: Investor participation (unique metric for ETFs)

**Indicators Available:**
- EMA Cross (`ema_cross`)
- MACD (`macd`)
- RSI (`rsi`)
- Momentum (`momentum`)
- Daily Momentum (`momentum_daily`)
- Supertrend (`supertrend`)

**Potential New Indicators Enabled by Additional Metrics:**
- **AUM Trend**: Market cap momentum (fund flow proxy)
- **Investor Count Momentum**: Interest/participation trends
- **Share Turnover**: Daily changes in number_of_shares
- **Fund Flow**: Delta in market_cap * price changes

### Key Differences

1. **Data Structure:**
   - Stocks: Full OHLCV data
   - ETFs: Single price point, BUT has additional metrics (market_cap, number_of_shares, number_of_investors)
   
2. **Available Indicators:**
   - Stocks: 10 indicators (some using high/low/volume)
   - ETFs: 6 indicators (price-based only)
   - **Opportunity:** ETF metrics enable volume-like indicators (market_cap changes = fund flows)
   
3. **Column Names:**
   - Stocks use `close` for analysis
   - ETFs use `price` for analysis
   - **Note:** ETFs also have `market_cap`, `number_of_shares`, `number_of_investors` available for specialized indicators

4. **Registers:**
   - Both have identical plugin architecture
   - Both use the same `BaseIndicator` interface
   - Both have separate registries (`finance_tools.stocks.analysis.indicators.registry` vs `finance_tools.etfs.analysis.indicators.registry`)

5. **Scanners:**
   - `StockScanner` (stocks/analysis/scanner.py)
   - `EtfScanner` (etfs/analysis/scanner.py)
   - Both follow identical patterns for indicator registration and scoring

6. **Additional ETF Metrics (Untapped Potential):**
   - `market_cap` can be used like volume (fund flows indicator)
   - `number_of_investors` can track interest/participation trends
   - `number_of_shares` can show share creation/destruction (liquidity indicator)

### Shared Patterns

1. **Base Classes:**
   - Both use `BaseIndicator` abstract class
   - Both use `IndicatorConfig`, `IndicatorSnapshot`, `IndicatorScore`
   - Interface is identical in both systems

2. **Plugin Architecture:**
   - Auto-discovery via `implementations/` directory
   - Registry pattern for indicator management
   - Dynamic weight assignment

3. **Scoring System:**
   - Weighted indicator contributions
   - Buy/sell/hold suggestions
   - Detailed calculation explanations

4. **Database:**
   - Shared base (`finance_tools.etfs.tefas.models.Base`)
   - Same database connection pool
   - Unified `AnalysisResult` table for both types

---

## Architectural Plan: Unified System

### Phase 1: Unified Base Classes and Types

#### 1.1 Create Unified Indicator Base
**Location:** `finance_tools/analysis/indicators/base.py`

**Changes:**
- Move `BaseIndicator`, `IndicatorConfig`, `IndicatorSnapshot`, `IndicatorScore` to unified location
- Add column mapping abstraction
- Support both `close` (stocks) and `price` (ETF) seamlessly

**Key Addition: Column Mapping**
```python
class BaseIndicator(ABC):
    def get_price_column(self, df: pd.DataFrame, column_hint: str = None) -> str:
        """Auto-detect the primary price column based on DataFrame structure.
        
        Priority:
        1. If column_hint provided and exists in DataFrame
        2. 'close' (for stocks)
        3. 'price' (for ETFs)
        4. First numeric column
        """
        if column_hint and column_hint in df.columns:
            return column_hint
        
        if 'close' in df.columns:
            return 'close'
        
        if 'price' in df.columns:
            return 'price'
        
        # Fallback: find first numeric column
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            return numeric_cols[0]
        
        raise ValueError("No suitable price column found")
```

#### 1.2 Unified Data Types
**Location:** `finance_tools/analysis/types.py`

**New Types:**
```python
@dataclass
class UnifiedScanCriteria:
    """Criteria that works for both stocks and ETFs"""
    column: str  # Will auto-detect 'close' or 'price'
    asset_type: str  # 'stock' or 'etf'
    
    # Indicator configuration (dynamic weights)
    w_ema_cross: float = 0.0
    w_macd: float = 0.0
    w_rsi: float = 0.0
    # ... all indicator weights
    
    # Thresholds
    score_buy_threshold: float = 1.0
    score_sell_threshold: float = 1.0

@dataclass
class UnifiedScanResult:
    """Unified result structure"""
    identifier: str  # symbol or code
    asset_type: str  # 'stock' or 'etf'
    timestamp: datetime
    last_value: float
    suggestion: UnifiedSuggestion
    score: float
    indicators_snapshot: Dict[str, float]
    components: Dict[str, Any]
    indicator_details: Dict[str, Any]
```

### Phase 2: Unified Indicator Registry

#### 2.1 Single Registry
**Location:** `finance_tools/analysis/indicators/registry.py`

**Implementation:**
- Combine both registries into one
- Support asset type filtering
- Auto-discovery of indicators from subdirectories

**Structure:**
```
finance_tools/
  analysis/
    indicators/
      base.py           # Unified base classes
      registry.py       # Unified registry
      implementations/
        stock/          # Stock-specific indicators
          ema_cross.py
          volume.py
          adx.py
          ...
        etf/            # ETF-specific indicators
          ema_cross.py
          daily_momentum.py
          ...
        common/         # Shared indicators
          rsi.py
          macd.py
          momentum.py
```

#### 2.2 Indicator Compatibility Matrix

**Tier 1: Universal Indicators (work with both)**
- RSI (only needs single price column)
- MACD (only needs single price column)
- Momentum (only needs single price column)
- EMA Cross (only needs single price column)

**Tier 2: Stock-Only Indicators (OHLCV required)**
- Volume (needs volume column)
- ATR (needs high/low/close)
- ADX (needs high/low)
- Stochastic (needs high/low/close)

**Tier 3: ETF-Specific Indicators**
- Daily Momentum (ETF-specific logic)
- Supertrend (adjustable for ETFs)

**Tier 4: ETF-Enhanced Indicators (NEW - leveraging market_cap, number_of_investors, number_of_shares)**
- **Fund Flow Momentum**: Changes in market_cap as proxy for money flows
- **Investor Interest**: Growth in number_of_investors (sentiment indicator)
- **Share Creation/Destruction**: Changes in number_of_shares (liquidity proxy)
- **AUM Trend**: Portfolio size momentum (size-based signal)
- **Investor Count RSI**: Overbought/oversold based on investor growth rate

**Key Insight:** 
ETF metrics (`market_cap`, `number_of_shares`, `number_of_investors`) provide dimensional parity with stock volume metrics. This enables:
- Volume-like analysis for ETFs using market_cap changes
- Participation/sentiment analysis via investor count trends  
- Liquidity analysis via share count changes
- Multi-dimensional ETF scanning beyond just price

**Decision:**
- Common indicators go in `indicators/implementations/common/`
- Asset-specific go in `indicators/implementations/stock/` or `indicators/implementations/etf/`
- ETF-enhanced indicators in `indicators/implementations/etf/` (leveraging unique metrics)
- Each indicator declares its capabilities via `get_asset_types()` and `get_required_columns()` methods

### Phase 3: Unified Scanner

#### 3.1 Create Unified Scanner
**Location:** `finance_tools/analysis/scanner.py`

**Design:**
```python
class UnifiedScanner:
    """Scanner that works for both stocks and ETFs"""
    
    def __init__(self):
        self.logger = get_logger("unified_scanner")
        self.registry = UnifiedIndicatorRegistry()
    
    def scan(
        self, 
        data_map: Dict[str, pd.DataFrame], 
        criteria: UnifiedScanCriteria
    ) -> List[UnifiedScanResult]:
        """
        Args:
            data_map: {identifier: DataFrame} - both symbols and codes
            criteria: Unified criteria with asset_type specified
        
        Returns:
            List of unified scan results
        """
        # Auto-detect price column
        # Build indicator configs
        # Apply indicators
        # Calculate scores
        # Return unified results
```

**Key Features:**
- Auto-detects whether data is stock or ETF based on column presence
- Dynamically filters indicators based on asset type
- Single scanning logic for both asset types

#### 3.2 Asset Type Detection
```python
def detect_asset_type(df: pd.DataFrame) -> str:
    """Detect if DataFrame contains stock or ETF data"""
    has_ohlcv = all(col in df.columns for col in ['open', 'high', 'low', 'close'])
    has_price = 'price' in df.columns
    
    if has_ohlcv:
        return 'stock'
    elif has_price:
        return 'etf'
    else:
        raise ValueError("Cannot determine asset type from DataFrame columns")
```

### Phase 4: Unified Retriever

#### 4.1 Universal Data Retriever
**Location:** `finance_tools/analysis/retriever.py`

**Design:**
```python
class UniversalDataRetriever:
    """Retrieves data for both stocks and ETFs"""
    
    def __init__(self):
        self.stock_retriever = StockDataRetriever()
        self.etf_retriever = EtfDataRetriever()
    
    def fetch(
        self,
        identifiers: List[str],
        asset_type: str,  # 'stock' or 'etf'
        start: Optional[date] = None,
        end: Optional[date] = None,
        **kwargs
    ) -> pd.DataFrame:
        """Fetch data based on asset type"""
        if asset_type == 'stock':
            return self.stock_retriever.fetch_info(
                symbols=identifiers, start=start, end=end, **kwargs
            )
        elif asset_type == 'etf':
            return self.etf_retriever.fetch_info(
                codes=identifiers, start=start, end=end, **kwargs
            )
```

### Phase 5: Backend Integration

#### 5.1 Unified API Endpoints

**Current State:**
- `/api/stocks/scan` - Stock scanning
- `/api/etfs/scan` - ETF scanning

**Unified Design:**
- `/api/analysis/scan` - Universal scanning endpoint
  - Accepts `asset_type` parameter
  - Returns unified result structure
  - Handles both stocks and ETFs

#### 5.2 Backend Service Updates

**Location:** `backend/main.py` (AnalyticsService)

**Changes:**
```python
@router.post("/api/analysis/scan")
async def unified_scan(request: UnifiedScanRequest):
    """Unified scanning endpoint for both stocks and ETFs"""
    
    # Fetch data based on asset type
    retriever = UniversalDataRetriever()
    data = retriever.fetch(
        identifiers=request.identifiers,
        asset_type=request.asset_type,
        start=request.start,
        end=request.end
    )
    
    # Group by identifier
    data_map = {}
    group_col = 'symbol' if request.asset_type == 'stock' else 'code'
    for identifier, group in data.groupby(group_col):
        data_map[identifier] = group
    
    # Scan with unified scanner
    scanner = UnifiedScanner()
    results = scanner.scan(data_map, request.criteria)
    
    return results
```

### Phase 6: Frontend Unification

#### 6.1 Unified Analysis Panel

**Current State:**
- Separate UI components for stocks and ETFs
- Different tabs/views for each

**Unified Design:**
- Single `AnalysisPanel` component
- Asset type selector (Stock/ETF)
- Dynamic indicator configuration based on asset type
- Unified results display

**Location:** `frontend/src/components/AnalysisPanel.tsx`

**Features:**
- Asset type switcher
- Dynamic indicator selection (show only available for selected type)
- Unified results table
- Same visualization for both types

---

## Migration Strategy

### Step 1: Create Unified Structure (Non-Breaking)
1. Create `finance_tools/analysis/` directory structure
2. Move common base classes to unified location
3. Keep existing stock/etf modules working
4. Implement unified scanner alongside existing ones

### Step 2: Migrate Indicators
1. Move common indicators to `analysis/indicators/implementations/common/`
2. Keep asset-specific indicators in their subdirectories
3. Update imports gradually
4. Add compatibility layer for old imports

### Step 3: Backend Migration
1. Create unified API endpoints
2. Keep old endpoints for backward compatibility
3. Route old endpoints through unified scanner
4. Update frontend gradually

### Step 4: Frontend Migration
1. Create unified `AnalysisPanel`
2. Keep old components for backward compatibility
3. Update to use unified endpoints
4. Phase out old components

### Step 5: Cleanup
1. Remove duplicate code
2. Deprecate old imports
3. Update documentation
4. Consolidate test suites

---

## Benefits

### Code Reusability
- Single indicator implementations for common indicators
- Unified scanner logic
- Shared base classes and types

### Maintainability
- One place to update indicator logic
- Unified testing
- Single source of truth for scoring algorithms

### Flexibility
- Easy to add new asset types (crypto, forex, etc.)
- Indicators can declare compatibility
- Dynamic feature detection

### Performance
- Single registry reduces memory footprint
- Shared indicator calculations
- Unified caching layer

---

## Implementation Timeline

### Week 1: Foundation
- [ ] Create unified directory structure
- [ ] Move base classes
- [ ] Implement unified registry
- [ ] Create compatibility layer

### Week 2: Indicators
- [ ] Migrate common indicators
- [ ] Update indicator structure
- [ ] Add asset type detection
- [ ] Update indicator registration

### Week 3: Scanner
- [ ] Implement unified scanner
- [ ] Create unified types
- [ ] Implement asset type detection
- [ ] Add unified retriever

### Week 4: Backend
- [ ] Create unified API endpoint
- [ ] Update backend service
- [ ] Maintain backward compatibility
- [ ] Add unified database queries

### Week 5: Frontend
- [ ] Create unified analysis panel
- [ ] Implement asset type switching
- [ ] Update UI components
- [ ] Add unified visualization

### Week 6: Testing & Cleanup
- [ ] Integration tests
- [ ] Performance testing
- [ ] Documentation
- [ ] Remove deprecated code

---

## Risk Mitigation

### Backward Compatibility
- Keep old endpoints active during transition
- Compatibility layer for imports
- Gradual deprecation warnings

### Data Integrity
- Ensure column mapping is correct
- Validate data types
- Add data validation layer

### Performance
- Monitor memory usage
- Profile indicator calculations
- Optimize hot paths

### Testing
- Unit tests for all indicators
- Integration tests for scanners
- End-to-end tests for workflows

---

## Open Questions

1. ~~**Volume Indicators:** How to handle ETF volume? (Not available in current ETF data)~~
   - **SOLVED:** Use `market_cap` changes as fund flow proxy, `number_of_investors` for participation, `number_of_shares` for liquidity

2. **ATR/ADX:** Should we add OHLCV support for ETFs or keep as stock-only?
   - ETFs don't have high/low, so these remain stock-only
   - Alternative: Create ETF-specific volatility indicators using price range data

3. **Intervals:** ETFs are daily-only. How to handle this in unified system?
   - Accept limitation for ETFs
   - Stocks can be multi-timeframe
   - Document timeframe capabilities in indicator metadata

4. **Frontend UX:** Single unified panel or keep separate tabs?
   - Recommendation: Single panel with asset type selector
   - Dynamically show/hide indicators based on selected type

5. **Database:** Should we add OHLCV fields to ETF table?
   - Recommendation: **No** - ETFs fundamentally have single NAV per day
   - Continue leveraging available metrics (market_cap, number_of_shares, number_of_investors)
   - These provide different but equally valuable signals

---

## Recommendations

1. **Start Small:** Begin with common indicators (RSI, MACD, Momentum, EMA Cross)
2. **Maintain Parallel Systems:** Keep old systems working during transition
3. **Gradual Migration:** Migrate one indicator at a time
4. **Add Asset Type to Database:** Consider adding `asset_type` column to `AnalysisResult`
5. ~~**Extend ETF Schema:** Consider adding high/low/open columns for future compatibility~~
   - **REVISED:** DON'T add OHLCV to ETFs - they have NAV only
   - **INSTEAD:** Create new ETF-specific indicators leveraging existing metrics
6. **NEW: Leverage ETF Unique Metrics:**
   - Build fund flow indicators using market_cap
   - Create participation indicators using number_of_investors
   - Develop liquidity indicators using number_of_shares
7. **Create Hybrid Indicators:** Some indicators could support both asset types with conditional logic

---

## Success Criteria

- [ ] Single indicator implementation for RSI, MACD, Momentum, EMA Cross
- [ ] Unified scanner handles both asset types
- [ ] Backend uses single scanning logic
- [ ] Frontend uses single analysis panel
- [ ] No code duplication
- [ ] All existing tests pass
- [ ] Performance is equivalent or better
- [ ] Documentation is updated

---

## Next Steps

1. Review this plan with team
2. Decide on final directory structure
3. Create proof-of-concept for one indicator
4. Get stakeholder approval
5. Begin implementation

---

**Document Version:** 1.0  
**Date:** 2025-01-15  
**Author:** Architecture Planning
