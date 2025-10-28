# finance_tools/etfs/analysis/indicators/__init__.py
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
                importlib.import_module(f".implementations.{name}", package=__package__)
            except Exception as e:
                print(f"Warning: Failed to load ETF indicator {name}: {e}")


# Trigger auto-discovery when this module is imported
_auto_discover_indicators()

# Export registry
from .registry import registry, IndicatorRegistry
from .base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore

__all__ = ['registry', 'IndicatorRegistry', 'BaseIndicator', 'IndicatorConfig', 'IndicatorSnapshot', 'IndicatorScore']

