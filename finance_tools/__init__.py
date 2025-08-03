# finance_tools/__init__.py
"""
Finance Tools - A comprehensive financial analysis and data collection toolkit.

This package provides tools for:
- Stock data analysis and visualization
- ETF analysis and comparison
- Technical analysis indicators
- Financial news collection and analysis
- Data downloaders for various financial sources
"""

__version__ = "0.1.0"
__author__ = "Mursel Tasgin"
__email__ = "mursel.tasgin@gmail.com"

# Import main modules
from . import stocks
from . import etfs

# Import utility functions
from .utils.dataframe_utils import get_as_df, get_stock_summary, extract_stock_data
from .utils.simple_result import SimpleResult, create_download_result

# Version info
__all__ = [
    "__version__", "__author__", "__email__", 
    "stocks", "etfs", 
    "get_as_df", "get_stock_summary", "extract_stock_data",
    "SimpleResult", "create_download_result"
]

# Add convenience note about as_df() method
__doc__ = """
Finance Tools - A comprehensive financial analysis and data collection toolkit.

Quick Start:
    from finance_tools.stocks.data_downloaders import YFinanceDownloader
    
    # Download data and convert to DataFrame
    df = downloader.execute(symbols=["AAPL", "MSFT"]).as_df()
    
    # Or use the utility function
    from finance_tools import get_as_df
    df = get_as_df(downloader.execute(symbols=["AAPL", "MSFT"]))
""" 