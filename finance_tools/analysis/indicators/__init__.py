# finance_tools/analysis/indicators/__init__.py
"""
Unified indicator system supporting both stocks and ETFs.

Auto-discovers indicators from implementations subdirectories:
- common/: Indicators that work for both stocks and ETFs
- stock/: Stock-specific indicators
- etf/: ETF-specific indicators
"""

def _auto_discover_indicators():
    """Auto-discover and import all indicator implementations"""
    import importlib
    import pkgutil
    from pathlib import Path
    
    base_package = Path(__file__).parent
    
    # Import from all subdirectories (common, stock, etf)
    for subdir in ['common', 'stock', 'etf']:
        implementations_path = base_package / "implementations" / subdir
        
        if not implementations_path.exists():
            continue
        
        # Import all modules in this subdirectory
        for _, name, is_pkg in pkgutil.iter_modules([str(implementations_path)]):
            if not is_pkg and not name.startswith('_'):
                try:
                    importlib.import_module(f"finance_tools.analysis.indicators.implementations.{subdir}.{name}")
                except Exception as e:
                    print(f"Warning: Failed to load indicator {subdir}.{name}: {e}")


# Trigger auto-discovery when this module is imported
_auto_discover_indicators()

# Export registry and base classes
from .registry import registry, IndicatorRegistry
from .base import BaseIndicator, IndicatorConfig, IndicatorSnapshot, IndicatorScore

__all__ = [
    'registry', 
    'IndicatorRegistry', 
    'BaseIndicator', 
    'IndicatorConfig', 
    'IndicatorSnapshot', 
    'IndicatorScore'
]

