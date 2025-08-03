# finance_tools/utils/dataframe_utils.py
"""
Utility functions for processing download results and converting to DataFrames.
"""

import pandas as pd
from typing import Dict, Any, Union, List
from .simple_result import SimpleResult


def get_as_df(result: Union[Dict, SimpleResult, Any]) -> pd.DataFrame:
    """
    Extract and unify data from download results into a single DataFrame.
    
    This function can be used as a pipe function to process download results
    and convert them into a unified DataFrame format.
    
    Args:
        result: Download result (can be dict, SimpleResult, or any object with 'data' attribute)
    
    Returns:
        pd.DataFrame: Unified DataFrame with all stock data
        
    Examples:
        # Single stock
        result = downloader.execute(symbols=["AAPL"])
        df = get_as_df(result)
        
        # Multiple stocks
        result = downloader.execute(symbols=["AAPL", "MSFT"])
        df = get_as_df(result)
        
        # As pipe function
        df = downloader.execute(symbols=["AAPL", "MSFT"]) | get_as_df
    """
    
    # Extract the data dictionary from various result types
    if hasattr(result, 'data'):
        # ToolResult object
        data_dict = result.data
    elif isinstance(result, dict):
        # Direct dictionary
        data_dict = result
    elif hasattr(result, '__getitem__'):
        # Dictionary-like object (SimpleResult)
        data_dict = result
    else:
        raise ValueError(f"Unsupported result type: {type(result)}")
    
    # Extract the main DataFrame from the data dictionary
    if isinstance(data_dict, dict) and 'data' in data_dict:
        main_data = data_dict['data']
    else:
        # If data_dict is already a DataFrame
        main_data = data_dict
    
    if not isinstance(main_data, pd.DataFrame):
        raise ValueError(f"Expected DataFrame, got {type(main_data)}")
    
    if main_data.empty:
        return pd.DataFrame()
    
    # Check if this is multiple stocks data (has 'Symbol' column)
    if 'Symbol' in main_data.columns:
        # Multiple stocks - unify the data
        return _unify_multiple_stocks(main_data)
    else:
        # Single stock - just return the data (already formatted)
        return main_data


def _unify_multiple_stocks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Unify multiple stocks data into a single DataFrame.
    
    Args:
        df: DataFrame with 'Symbol' column containing multiple stocks
    
    Returns:
        pd.DataFrame: Unified DataFrame (already formatted)
    """
    if df.empty:
        return df
    
    # Data is already formatted by the downloader, just return it
    return df


def get_as_df_pipe(result: Union[Dict, SimpleResult, Any]) -> pd.DataFrame:
    """
    Alias for get_as_df to make it clear it can be used as a pipe function.
    
    This function can be used with the pipe operator (|) in Python 3.12+.
    
    Args:
        result: Download result
    
    Returns:
        pd.DataFrame: Unified DataFrame
    """
    return get_as_df(result)


def extract_stock_data(result: Union[Dict, SimpleResult, Any], 
                      include_metadata: bool = False) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Extract stock data with optional metadata.
    
    Args:
        result: Download result
        include_metadata: Whether to include metadata in the result
    
    Returns:
        DataFrame if include_metadata=False, Dict with 'data' and 'metadata' if True
    """
    df = get_as_df(result)
    
    if not include_metadata:
        return df
    
    # Extract metadata if available
    metadata = {}
    if hasattr(result, 'metadata'):
        metadata = result.metadata or {}
    elif isinstance(result, dict) and 'metadata' in result:
        metadata = result['metadata']
    
    return {
        'data': df,
        'metadata': metadata
    }


def get_stock_summary(result: Union[Dict, SimpleResult, Any]) -> Dict[str, Any]:
    """
    Get a summary of the stock data.
    
    Args:
        result: Download result
    
    Returns:
        Dict with summary information
    """
    df = get_as_df(result)
    
    if df.empty:
        return {'error': 'No data available'}
    
    summary = {
        'shape': df.shape,
        'columns': list(df.columns),
        'date_range': None,
        'symbols': [],
        'latest_prices': {}
    }
    
    # Get date range if Date column exists
    if 'Date' in df.columns:
        summary['date_range'] = {
            'start': df['Date'].min().strftime('%Y-%m-%d'),
            'end': df['Date'].max().strftime('%Y-%m-%d')
        }
    
    # Get symbols if Symbol column exists
    if 'Symbol' in df.columns:
        summary['symbols'] = df['Symbol'].unique().tolist()
        
        # Get latest prices for each symbol
        for symbol in summary['symbols']:
            symbol_data = df[df['Symbol'] == symbol]
            if not symbol_data.empty and 'Close' in symbol_data.columns:
                summary['latest_prices'][symbol] = symbol_data['Close'].iloc[-1]
    
    return summary


# Add pipe support for Python 3.12+
try:
    # This will work in Python 3.12+ where pipe operator is supported
    def __or__(self, other):
        """Support for pipe operator: result | get_as_df"""
        if callable(other):
            return other(self)
        return NotImplemented
except:
    pass 