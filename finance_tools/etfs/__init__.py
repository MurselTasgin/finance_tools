# finance_tools/etfs/__init__.py
"""
ETFs module for ETF analysis and comparison.

This module provides tools for:
- ETF data collection and analysis
- ETF comparison and screening
- Portfolio allocation analysis
- ETF performance tracking
"""
from . import tefas
from .tefas import TefasDownloader
# Future ETF modules will be imported here
__all__ = ["tefas", "TefasDownloader"]   