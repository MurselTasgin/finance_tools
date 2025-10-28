# finance_tools/etfs/analysis/indicators/registry.py
from typing import Dict, Optional, List
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

