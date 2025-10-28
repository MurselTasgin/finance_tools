# finance_tools/analysis/indicators/base.py
"""
Unified base classes for technical indicators supporting both stocks and ETFs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
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
    calculation_details: Optional[List[str]] = None  # Step-by-step calculation explanation


class BaseIndicator(ABC):
    """Abstract base class for all technical indicators
    
    Supports both stocks (close/high/low/volume) and ETFs (price/market_cap/number_of_shares).
    Indicators automatically detect asset type from DataFrame columns.
    """
    
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
        """Return list of required DataFrame columns
        
        Examples:
        - Price-based: ['close'] or ['price']
        - OHLC: ['high', 'low', 'close']
        - Volume-based: ['close', 'volume']
        - ETF metrics: ['price', 'market_cap']
        """
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
            df: DataFrame with time series data
            column: Column name to analyze (e.g., 'close', 'price')
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
            column: Column name (e.g., 'close', 'price')
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
    
    def get_asset_types(self) -> List[str]:
        """Return supported asset types: ['stock'], ['etf'], or ['stock', 'etf']
        
        Used by registry to filter indicators by asset type.
        Default: ['stock', 'etf'] - universal indicators
        """
        return ['stock', 'etf']
    
    def get_price_column(self, df: pd.DataFrame, column_hint: str = None) -> str:
        """Auto-detect the primary price column based on DataFrame structure.
        
        Priority:
        1. If column_hint provided and exists in DataFrame
        2. 'close' (for stocks)
        3. 'price' (for ETFs)
        4. First numeric column
        
        Args:
            df: DataFrame to inspect
            column_hint: Optional specific column to use
            
        Returns:
            Column name to use for price analysis
        """
        if column_hint and column_hint in df.columns:
            return column_hint
        
        if 'close' in df.columns:
            return 'close'
        
        if 'price' in df.columns:
            return 'price'
        
        # Fallback: find first numeric column
        numeric_cols = df.select_dtypes(include=['float64', 'int64', 'Float64', 'Int64']).columns.tolist()
        if len(numeric_cols) > 0:
            return numeric_cols[0]
        
        raise ValueError("No suitable price column found in DataFrame")
    
    def detect_asset_type(self, df: pd.DataFrame) -> str:
        """Detect if DataFrame contains stock or ETF data
        
        Args:
            df: DataFrame to inspect
            
        Returns:
            'stock' or 'etf'
        """
        has_ohlcv = all(col in df.columns for col in ['open', 'high', 'low', 'close'])
        has_price = 'price' in df.columns
        
        if has_ohlcv:
            return 'stock'
        elif has_price:
            return 'etf'
        else:
            raise ValueError("Cannot determine asset type from DataFrame columns")
    
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

