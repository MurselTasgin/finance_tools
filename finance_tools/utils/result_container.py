# finance_tools/utils/result_container.py
"""
Custom result container that supports both dictionary and attribute access.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass


class ResultContainer:
    """
    A container class that supports both dictionary-style and attribute-style access.
    
    This allows accessing data as both:
    - result['data'] (dictionary style)
    - result.data (attribute style)
    """
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize with a dictionary of data."""
        self._data = data
    
    def __getitem__(self, key: str) -> Any:
        """Support dictionary-style access: result['data']"""
        return self._data[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Support dictionary-style assignment: result['data'] = value"""
        self._data[key] = value
    
    def __getattr__(self, name: str) -> Any:
        """Support attribute-style access: result.data"""
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Support attribute-style assignment: result.data = value"""
        if name == '_data':
            super().__setattr__(name, value)
        else:
            self._data[name] = value
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator: 'data' in result"""
        return key in self._data
    
    def __iter__(self):
        """Support iteration over keys"""
        return iter(self._data)
    
    def keys(self):
        """Return dictionary keys"""
        return self._data.keys()
    
    def values(self):
        """Return dictionary values"""
        return self._data.values()
    
    def items(self):
        """Return dictionary items"""
        return self._data.items()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value with default: result.get('data', default)"""
        return self._data.get(key, default)
    
    def __len__(self) -> int:
        """Return number of items"""
        return len(self._data)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"{self.__class__.__name__}({self._data})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to regular dictionary"""
        return self._data.copy()


@dataclass
class DownloadResult:
    """
    A dataclass for download results that supports both access patterns.
    """
    data: ResultContainer
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    
    def __getitem__(self, key: str) -> Any:
        """Support dictionary-style access: result['data']"""
        if key == 'data':
            return self.data
        elif key == 'success':
            return self.success
        elif key == 'error':
            return self.error
        elif key == 'metadata':
            return self.metadata
        elif key == 'execution_time':
            return self.execution_time
        else:
            raise KeyError(f"'{key}' not found in result")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value with default"""
        try:
            return self[key]
        except KeyError:
            return default 