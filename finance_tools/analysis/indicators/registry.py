# finance_tools/analysis/indicators/registry.py
"""
Unified indicator registry supporting both stocks and ETFs.

This registry replaces the separate registries in stocks and etfs modules,
providing a single source of truth for all indicators with asset type filtering.
"""
from __future__ import annotations

from typing import Dict, Optional, List
from .base import BaseIndicator


class IndicatorRegistry:
    """Singleton registry for all available indicators across asset types"""
    
    _instance = None
    _indicators: Dict[str, BaseIndicator] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, indicator: BaseIndicator):
        """Register an indicator instance"""
        indicator_id = indicator.get_id()
        if indicator_id in self._indicators:
            # Update if indicator already exists
            self._indicators[indicator_id] = indicator
        else:
            self._indicators[indicator_id] = indicator
    
    def get(self, indicator_id: str) -> Optional[BaseIndicator]:
        """Get indicator by ID"""
        return self._indicators.get(indicator_id)
    
    def get_all(self) -> Dict[str, BaseIndicator]:
        """Get all registered indicators"""
        return self._indicators.copy()
    
    def get_all_ids(self) -> List[str]:
        """Get list of all indicator IDs"""
        return list(self._indicators.keys())
    
    def get_by_asset_type(self, asset_type: str) -> Dict[str, BaseIndicator]:
        """Get indicators that support a specific asset type
        
        Args:
            asset_type: 'stock', 'etf', or 'universal'
            
        Returns:
            Dict of indicator_id -> indicator for matching asset types
        """
        result = {}
        for indicator_id, indicator in self._indicators.items():
            supported_types = indicator.get_asset_types()
            if asset_type in supported_types or 'universal' in supported_types:
                result[indicator_id] = indicator
        return result
    
    def is_compatible(self, indicator_id: str, asset_type: str) -> bool:
        """Check if an indicator is compatible with an asset type
        
        Args:
            indicator_id: ID of the indicator
            asset_type: 'stock' or 'etf'
            
        Returns:
            True if indicator supports the asset type
        """
        indicator = self.get(indicator_id)
        if indicator is None:
            return False
        supported_types = indicator.get_asset_types()
        return asset_type in supported_types or 'universal' in supported_types
    
    def clear(self):
        """Clear registry (mainly for testing)"""
        self._indicators.clear()


# Global registry instance
registry = IndicatorRegistry()

