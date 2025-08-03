# finance_tools/utils/simple_result.py
"""
Simple result class that supports both dictionary and attribute access.
"""

from types import SimpleNamespace
from typing import Any, Dict


class SimpleResult(dict):
    """
    A simple dictionary subclass that supports both dictionary and attribute access.
    
    Usage:
        result = SimpleResult({'data': df, 'success': True})
        result['data']      # Dictionary access
        result.data         # Attribute access
    """
    
    def __getattr__(self, name: str) -> Any:
        """Support attribute access: result.data"""
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Support attribute assignment: result.data = value"""
        self[name] = value


# Alternative using SimpleNamespace (even simpler)
def create_result(data_dict: Dict[str, Any]) -> SimpleNamespace:
    """
    Create a result object using SimpleNamespace.
    
    Usage:
        result = create_result({'data': df, 'success': True})
        result.data         # Attribute access only
    """
    return SimpleNamespace(**data_dict)


# Example usage functions
def create_download_result(data: Any, success: bool = True, error: str = None, 
                          metadata: Dict = None, execution_time: float = None) -> SimpleResult:
    """
    Create a download result with both access patterns.
    
    Returns:
        SimpleResult object that supports both result['data'] and result.data
    """
    result_data = {
        'data': data,
        'success': success,
        'error': error,
        'metadata': metadata or {},
        'execution_time': execution_time
    }
    return SimpleResult(result_data) 