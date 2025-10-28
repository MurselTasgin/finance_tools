# finance_tools/analysis/indicators/compatibility.py
"""
Compatibility layer for existing code that imports from asset-specific modules.

This module provides transparent imports to maintain backward compatibility
while the codebase migrates to the unified system.
"""

# Re-export unified classes for backward compatibility
from .base import (
    BaseIndicator,
    IndicatorConfig,
    IndicatorSnapshot,
    IndicatorScore
)

from .registry import (
    registry as unified_registry,
    IndicatorRegistry
)

__all__ = [
    'BaseIndicator',
    'IndicatorConfig', 
    'IndicatorSnapshot',
    'IndicatorScore',
    'unified_registry',
    'IndicatorRegistry'
]

