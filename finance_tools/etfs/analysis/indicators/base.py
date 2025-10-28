# finance_tools/etfs/analysis/indicators/base.py
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

