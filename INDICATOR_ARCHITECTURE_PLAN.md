# Stock Indicator Architecture - Plugin-Based Design Plan

## Executive Summary

Current problem: Adding a new indicator requires modifying 3+ files (indicators.py, scanner.py, frontend form) with hardcoded logic. This is inflexible and violates Open/Closed Principle.

**Solution**: Implement a plugin-based architecture where each indicator is self-contained with standardized methods that the main module discovers and calls generically.

---

## Architecture Overview

### Directory Structure
```
finance_tools/stocks/analysis/
├── indicators/
│   ├── __init__.py                    # Registers all indicators
│   ├── base.py                        # Abstract base classes
│   ├── registry.py                     # Indicator discovery & registration
│   ├── implementations/
│   │   ├── __init__.py
│   │   ├── ema.py                     # EMA indicator module
│   │   ├── macd.py                    # MACD indicator module
│   │   ├── rsi.py                     # RSI indicator module
│   │   ├── momentum.py                # Momentum indicator module
│   │   ├── volume.py                  # Volume indicator module
│   │   ├── stochastic.py              # Stochastic indicator module
│   │   ├── atr.py                     # ATR indicator module
│   │   ├── adx.py                     # ADX indicator module
│   │   ├── supertrend.py              # Supertrend indicator module
│   │   └── ema_regime.py              # EMA Regime indicator module
│   └── ema_cross.py                   # EMA Cross indicator module
├── scanner.py                         # Simplified - just iterates indicators
└── scanner_types.py                   # Core types (unchanged)
```

---

## Core Components

### 1. Abstract Base Indicator Class (`indicators/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import pandas as pd

@dataclass
class IndicatorConfig:
    """Configuration schema for an indicator"""
    name: str
    parameters: Dict[str, Any]
    weight: float = 1.0

@dataclass
class IndicatorSnapshot:
    """Snapshot of indicator values for a specific row"""
    values: Dict[str, float]  # {column_name: value}

@dataclass
class IndicatorScore:
    """Score contribution from this indicator"""
    raw: float
    weight: float
    contribution: float
    explanation: str

class BaseIndicator(ABC):
    """Abstract base class for all technical indicators"""
    
    @abstractmethod
    def get_id(self) -> str:
        """Return unique identifier (e.g., 'ema_cross', 'macd')"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return human-readable name"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return detailed description of what this indicator does"""
        pass
    
    @abstractmethod
    def get_required_columns(self) -> List[str]:
        """Return list of required DataFrame columns (e.g., ['close', 'high', 'low', 'volume'])"""
        pass
    
    @abstractmethod
    def get_parameter_schema(self) -> Dict[str, Any]:
        """Return JSON schema for configuration parameters
        
        Example: {
            'fast': {'type': 'integer', 'default': 20, 'min': 5, 'max': 100},
            'slow': {'type': 'integer', 'default': 50, 'min': 10, 'max': 200}
        }
        """
        pass
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        """Calculate indicator values and add them as columns to DataFrame
        
        Args:
            df: DataFrame with OHLCV data
            column: Column name to analyze (e.g., 'close')
            config: Configuration for this indicator
            
        Returns:
            DataFrame with additional indicator columns added
        """
        pass
    
    @abstractmethod
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        """Extract snapshot values for the last row
        
        Args:
            df: DataFrame (already enriched with indicator columns)
            column: Column name (e.g., 'close')
            config: Configuration
            
        Returns:
            IndicatorSnapshot with relevant values for display
        """
        pass
    
    @abstractmethod
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        """Calculate score contribution from this indicator
        
        Args:
            df: DataFrame (already enriched with indicator columns)
            column: Column name
            config: Configuration (includes weight)
            
        Returns:
            IndicatorScore or None if not applicable
        """
        pass
    
    @abstractmethod
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        """Generate human-readable explanation of current state
        
        Args:
            df: DataFrame (already enriched)
            column: Column name
            config: Configuration
            
        Returns:
            List of explanation strings
        """
        pass
    
    # Optional methods (default implementations provided)
    
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities (e.g., ['provides_buy_signal', 'provides_sell_signal'])
        
        This can be used by frontend to show/hide features
        """
        return []
    
    def get_suggestions(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[str]:
        """Return high-level suggestion: 'buy', 'sell', 'hold', or None
        
        Args:
            df: DataFrame (already enriched)
            column: Column name
            config: Configuration
            
        Returns:
            String suggestion or None
        """
        return None
```

---

### 2. Indicator Registry (`indicators/registry.py`)

```python
from typing import Dict, Type, List
from .base import BaseIndicator

class IndicatorRegistry:
    """Singleton registry for all available indicators"""
    
    _instance = None
    _indicators: Dict[str, BaseIndicator] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, indicator: BaseIndicator):
        """Register an indicator instance"""
        self._indicators[indicator.get_id()] = indicator
    
    def get(self, indicator_id: str) -> Optional[BaseIndicator]:
        """Get indicator by ID"""
        return self._indicators.get(indicator_id)
    
    def get_all(self) -> Dict[str, BaseIndicator]:
        """Get all registered indicators"""
        return self._indicators.copy()
    
    def get_all_ids(self) -> List[str]:
        """Get list of all indicator IDs"""
        return list(self._indicators.keys())
    
    def clear(self):
        """Clear registry (mainly for testing)"""
        self._indicators.clear()

# Global registry instance
registry = IndicatorRegistry()
```

---

### 3. Example Indicator Implementation (`indicators/implementations/ema_cross.py`)

```python
from typing import Dict, List, Optional, Any
import pandas as pd
from ..base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
from ..registry import registry

class EMACrossIndicator(BaseIndicator):
    """EMA Crossover indicator"""
    
    def __init__(self):
        # Register on instantiation
        registry.register(self)
    
    def get_id(self) -> str:
        return "ema_cross"
    
    def get_name(self) -> str:
        return "EMA Crossover"
    
    def get_description(self) -> str:
        return "Detects when short-term EMA crosses above/below long-term EMA"
    
    def get_required_columns(self) -> List[str]:
        return ['close']  # Only needs close price
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'short': {
                'type': 'integer',
                'default': 20,
                'min': 5,
                'max': 200,
                'description': 'Short-term EMA period'
            },
            'long': {
                'type': 'integer',
                'default': 50,
                'min': 10,
                'max': 500,
                'description': 'Long-term EMA period'
            }
        }
    
    def calculate(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> pd.DataFrame:
        """Calculate EMA and cross signals"""
        import pandas as pd
        from ta.trend import EMAIndicator
        
        params = config.parameters
        short_period = int(params.get('short', 20))
        long_period = int(params.get('long', 50))
        
        series = df[column].astype(float)
        
        # Calculate EMAs
        ema_short = EMAIndicator(close=series, window=short_period, fillna=False).ema_indicator()
        ema_long = EMAIndicator(close=series, window=long_period, fillna=False).ema_indicator()
        
        result = df.copy()
        result[f"{column}_ema_{short_period}"] = ema_short
        result[f"{column}_ema_{long_period}"] = ema_long
        
        # Cross signals
        prev_diff = (ema_short - ema_long).shift(1)
        curr_diff = (ema_short - ema_long)
        
        result[f"{column}_ema_{short_period}_{long_period}_cross_up"] = (
            (prev_diff <= 0) & (curr_diff > 0)
        ).astype(int)
        result[f"{column}_ema_{short_period}_{long_period}_cross_down"] = (
            (prev_diff >= 0) & (curr_diff < 0)
        ).astype(int)
        
        return result
    
    def get_snapshot(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> IndicatorSnapshot:
        """Extract current values"""
        params = config.parameters
        short_period = int(params.get('short', 20))
        long_period = int(params.get('long', 50))
        
        last_row = df.iloc[-1]
        snapshot = {}
        
        for period in [short_period, long_period]:
            col_name = f"{column}_ema_{period}"
            val = last_row.get(col_name)
            if pd.notnull(val):
                snapshot[col_name] = float(val)
        
        return IndicatorSnapshot(values=snapshot)
    
    def get_score(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[IndicatorScore]:
        """Calculate score based on price position relative to EMAs"""
        if config.weight <= 0:
            return None
        
        params = config.parameters
        short_period = int(params.get('short', 20))
        long_period = int(params.get('long', 50))
        
        last_row = df.iloc[-1]
        price = last_row.get(column)
        ema_short = last_row.get(f"{column}_ema_{short_period}")
        ema_long = last_row.get(f"{column}_ema_{long_period}")
        
        if not all(pd.notnull([price, ema_short, ema_long])):
            return None
        
        # Score: percentage position relative to EMAs
        if ema_short > 0:
            price_comp = (price - ema_short) / ema_short
        else:
            price_comp = 0.0
        
        if ema_long > 0:
            cross_comp = (ema_short - ema_long) / ema_long
        else:
            cross_comp = 0.0
        
        # Weighted average
        raw = (price_comp * 0.5) + (cross_comp * 0.5)
        contribution = raw * config.weight
        
        explanation = f"Price position: {price_comp:.3f}, EMA cross: {cross_comp:.3f}"
        
        return IndicatorScore(
            raw=raw,
            weight=config.weight,
            contribution=contribution,
            explanation=explanation
        )
    
    def explain(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> List[str]:
        """Generate explanation"""
        params = config.parameters
        short_period = int(params.get('short', 20))
        long_period = int(params.get('long', 50))
        
        last_row = df.iloc[-1]
        
        price = last_row.get(column)
        ema_short = last_row.get(f"{column}_ema_{short_period}")
        ema_long = last_row.get(f"{column}_ema_{long_period}")
        
        lines = []
        lines.append(f"📈 EMA {short_period}/{long_period} Analysis:")
        
        if not all(pd.notnull([price, ema_short, ema_long])):
            lines.append("  ⚠️ Insufficient data")
            return lines
        
        # Cross status
        cross_up = last_row.get(f"{column}_ema_{short_period}_{long_period}_cross_up") == 1
        cross_down = last_row.get(f"{column}_ema_{short_period}_{long_period}_cross_down") == 1
        
        if cross_up:
            lines.append(f"  ✅ BULLISH CROSS: EMA {short_period} crossed above EMA {long_period}")
        elif cross_down:
            lines.append(f"  ❌ BEARISH CROSS: EMA {short_period} crossed below EMA {long_period}")
        else:
            lines.append(f"  ➖ NO CROSS: No recent crossover detected")
        
        # Price vs EMAs
        if price > ema_short:
            lines.append(f"  ✅ Price ({price:.2f}) above EMA {short_period} ({ema_short:.2f})")
        else:
            lines.append(f"  ❌ Price ({price:.2f}) below EMA {short_period} ({ema_short:.2f})")
        
        # Trend
        if ema_short > ema_long:
            lines.append(f"  📈 UPTREND: Short-term EMA above long-term EMA")
        else:
            lines.append(f"  📉 DOWNTREND: Short-term EMA below long-term EMA")
        
        return lines
    
    def get_capabilities(self) -> List[str]:
        return ['provides_buy_signal', 'provides_sell_signal', 'provides_trend_direction']
    
    def get_suggestions(self, df: pd.DataFrame, column: str, config: IndicatorConfig) -> Optional[str]:
        """Return buy/sell/hold suggestion"""
        last_row = df.iloc[-1]
        
        cross_up = last_row.get(f"{column}_ema_{last_row.get('short', 20)}_{last_row.get('long', 50)}_cross_up") == 1
        cross_down = last_row.get(f"{column}_ema_{last_row.get('short', 20)}_{last_row.get('long', 50)}_cross_down") == 1
        
        if cross_up:
            return "buy"
        elif cross_down:
            return "sell"
        return "hold"

# Instantiate to register
_ = EMACrossIndicator()
```

---

### 4. Updated Scanner (`scanner.py` - simplified)

```python
from typing import List, Dict
import pandas as pd
from .indicators.registry import registry
from .scanner_types import StockScanCriteria, StockScanResult, StockSuggestion
from ...logging import get_logger

class StockScanner:
    """Runs stock scans using plugin-based indicators"""
    
    def __init__(self) -> None:
        self.logger = get_logger("stock_scanner")
    
    def scan(self, symbol_to_df: Dict[str, pd.DataFrame], criteria: StockScanCriteria) -> List[StockScanResult]:
        self.logger.info(f"🔍 Starting scan for {len(symbol_to_df)} symbols")
        
        results: List[StockScanResult] = []
        
        for symbol, df in symbol_to_df.items():
            if df is None or df.empty:
                self.logger.warning(f"⚠️ Skipping {symbol} - empty DataFrame")
                continue
            
            if criteria.column not in df.columns:
                self.logger.warning(f"⚠️ Skipping {symbol} - column '{criteria.column}' not found")
                continue
            
            # Build indicator configurations from criteria
            indicator_configs = self._build_indicator_configs(criteria)
            
            # Enrich DataFrame with all indicators
            enriched = df.copy()
            indicators_snapshot = {}
            
            for indicator_id, config in indicator_configs.items():
                indicator = registry.get(indicator_id)
                if indicator is None:
                    self.logger.warning(f"⚠️ Unknown indicator: {indicator_id}")
                    continue
                
                # Calculate indicator
                enriched = indicator.calculate(enriched, criteria.column, config)
                
                # Get snapshot
                snapshot = indicator.get_snapshot(enriched, criteria.column, config)
                indicators_snapshot.update(snapshot.values)
            
            # Derive suggestion and score from all indicators
            suggestion, score, components = self._derive_suggestion(enriched, criteria, indicator_configs)
            
            results.append(
                StockScanResult(
                    symbol=symbol,
                    timestamp=pd.to_datetime(enriched.iloc[-1]["date"]).to_pydatetime() if "date" in enriched.columns else None,
                    last_value=float(enriched.iloc[-1][criteria.column]) if pd.notnull(enriched.iloc[-1][criteria.column]) else None,
                    suggestion=suggestion,
                    score=score,
                    indicators_snapshot=indicators_snapshot,
                    components=components,
                )
            )
        
        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)
        return results
    
    def _build_indicator_configs(self, criteria: StockScanCriteria) -> Dict[str, Any]:
        """Build indicator configurations from criteria"""
        from .indicators.base import IndicatorConfig
        
        configs = {}
        
        # EMA Cross
        if criteria.w_ema_cross > 0:
            configs['ema_cross'] = IndicatorConfig(
                name="EMA Cross",
                parameters={'short': criteria.ema_short, 'long': criteria.ema_long},
                weight=criteria.w_ema_cross
            )
        
        # MACD
        if criteria.w_macd > 0:
            configs['macd'] = IndicatorConfig(
                name="MACD",
                parameters={
                    'window_slow': criteria.macd_slow,
                    'window_fast': criteria.macd_fast,
                    'window_sign': criteria.macd_sign
                },
                weight=criteria.w_macd
            )
        
        # RSI
        if criteria.w_rsi > 0:
            configs['rsi'] = IndicatorConfig(
                name="RSI",
                parameters={
                    'window': criteria.rsi_window,
                    'lower': criteria.rsi_lower,
                    'upper': criteria.rsi_upper
                },
                weight=criteria.w_rsi
            )
        
        # Add other indicators based on criteria...
        
        return configs
    
    def _derive_suggestion(self, df: pd.DataFrame, criteria: StockScanCriteria, indicator_configs: Dict) -> Tuple[StockSuggestion, float, Dict]:
        """Derive suggestion and score by aggregating indicator contributions"""
        from .indicators.registry import registry
        
        reasons = []
        components = {}
        total_score = 0.0
        
        # Get explanations and scores from each indicator
        for indicator_id, config in indicator_configs.items():
            indicator = registry.get(indicator_id)
            if indicator is None:
                continue
            
            # Get explanation
            explanation = indicator.explain(df, criteria.column, config)
            reasons.extend(explanation)
            reasons.append("")  # Blank line between indicators
            
            # Get score
            score = indicator.get_score(df, criteria.column, config)
            if score is not None:
                components[indicator_id] = {
                    'raw': score.raw,
                    'weight': score.weight,
                    'contribution': score.contribution
                }
                total_score += score.contribution
        
        # Add summary
        reasons.append("=" * 60)
        reasons.append(f"📊 TOTAL SCORE: {total_score:.3f}")
        reasons.append("=" * 60)
        
        # Determine recommendation
        if total_score >= criteria.score_buy_threshold:
            recommendation = "buy"
        elif total_score <= -criteria.score_sell_threshold:
            recommendation = "sell"
        else:
            recommendation = "hold"
        
        suggestion = StockSuggestion(recommendation=recommendation, reasons=reasons)
        
        return suggestion, total_score, components
```

---

### 5. Auto-Discovery (`indicators/__init__.py`)

```python
"""Auto-import all indicators to trigger registration"""
import importlib
import pkgutil
from pathlib import Path

def _auto_discover_indicators():
    """Auto-discover and import all indicator implementations"""
    package = Path(__file__).parent / "implementations"
    
    # Import all modules in implementations/
    for _, name, is_pkg in pkgutil.iter_modules([str(package)]):
        if not is_pkg:
            try:
                importlib.import_module(f".implementations.{name}", __package__)
            except Exception as e:
                print(f"Warning: Failed to load indicator {name}: {e}")

# Trigger auto-discovery when this module is imported
_auto_discover_indicators()

# Export registry
from .registry import registry, IndicatorRegistry
from .base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore
```

---

## Frontend Changes

### Backend API Endpoint: GET `/api/stock/indicators`

```python
@router.get("/indicators")
def get_available_indicators():
    """Return list of all available indicators with their schemas"""
    from finance_tools.stocks.analysis.indicators.registry import registry
    
    indicators = []
    for indicator_id, indicator in registry.get_all().items():
        indicators.append({
            'id': indicator_id,
            'name': indicator.get_name(),
            'description': indicator.get_description(),
            'required_columns': indicator.get_required_columns(),
            'parameter_schema': indicator.get_parameter_schema(),
            'capabilities': indicator.get_capabilities()
        })
    
    return {"indicators": indicators}
```

### Frontend: Dynamic Scanner Configuration

```typescript
// Replace hardcoded AVAILABLE_SCANNERS with API call
useEffect(() => {
  stockApi.getIndicators().then(response => {
    setAvailableScanners(response.indicators);
  });
}, []);

interface Indicator {
  id: string;
  name: string;
  description: string;
  required_columns: string[];
  parameter_schema: Record<string, any>;
  capabilities: string[];
}
```

---

## Migration Strategy

### Phase 1: Build Infrastructure
1. Create `indicators/` directory structure
2. Implement `BaseIndicator` abstract class
3. Implement `IndicatorRegistry`
4. Create auto-discovery mechanism

### Phase 2: Migrate Existing Indicators
1. Create indicator modules (EMA Cross, MACD, RSI, etc.)
2. Test each in isolation
3. Gradually replace hardcoded logic

### Phase 3: Update Scanner
1. Simplify `scanner.py` to use registry
2. Remove all hardcoded indicator logic
3. Test thoroughly

### Phase 4: Update Frontend
1. Add API endpoint for indicator discovery
2. Make frontend dynamic
3. Remove hardcoded scanner definitions

### Phase 5: Cleanup
1. Remove old indicator calculation code
2. Clean up unused imports
3. Update documentation

---

## Benefits

1. **Open/Closed Principle**: Open for extension, closed for modification
2. **Single Responsibility**: Each indicator handles its own logic
3. **DRY**: No code duplication
4. **Testability**: Each indicator can be tested independently
5. **Discoverability**: Frontend automatically shows available indicators
6. **Maintainability**: Changes to one indicator don't affect others
7. **Documentation**: Each indicator self-documents via methods

---

## Testing Strategy

### Unit Tests per Indicator
```python
# tests/indicators/test_ema_cross.py
def test_ema_cross_indicator():
    indicator = EMACrossIndicator()
    assert indicator.get_id() == "ema_cross"
    assert indicator.get_name() == "EMA Crossover"
    
    df = create_test_dataframe()
    config = IndicatorConfig(name="test", parameters={'short': 20, 'long': 50})
    
    result = indicator.calculate(df, 'close', config)
    assert 'close_ema_20' in result.columns
    
    snapshot = indicator.get_snapshot(result, 'close', config)
    assert len(snapshot.values) > 0
    
    score = indicator.get_score(result, 'close', config)
    assert score is not None
    assert isinstance(score.raw, float)
```

### Integration Tests
```python
def test_scanner_with_indicators():
    scanner = StockScanner()
    criteria = StockScanCriteria(column='close', w_ema_cross=1.0)
    
    data = {'AAPL': create_test_dataframe()}
    results = scanner.scan(data, criteria)
    
    assert len(results) > 0
    assert 'ema_cross' in results[0].components
```

---

## Future Enhancements

1. **Indicator Dependencies**: Some indicators depend on others (e.g., ATR used by Supertrend)
2. **Composite Indicators**: Indicators that combine multiple sub-indicators
3. **Performance Caching**: Cache calculated indicators
4. **Runtime Validation**: Validate configurations against schemas
5. **Indicator Templates**: Pre-configured indicator sets (e.g., "momentum_scanner")
6. **Custom Indicators**: User-defined indicators via Python scripts

---

## Questions to Consider

1. **Backward Compatibility**: Should old API be maintained during migration?
2. **Configuration Storage**: How to store user indicator configurations?
3. **Validation**: When to validate parameter schemas (runtime vs. load time)?
4. **Error Handling**: How to handle indicator calculation failures?
5. **Performance**: Should indicators be calculated in parallel?
6. **Frontend Complexity**: How to handle dynamic parameter forms?

---

## Conclusion

This architecture transforms the system from a monolithic, hardcoded approach to a flexible, extensible plugin system. Adding a new indicator becomes as simple as creating a new file with 6 methods, and the system automatically:
- Discovers it
- Documents it
- Exposes it to the frontend
- Uses it in scans
- Explains it in results

No more touching core files!

