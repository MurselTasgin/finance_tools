# tests/test_yfinance.py
"""
Tests for YFinanceDownloader class.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

from finance_tools.stocks.data_downloaders.yfinance import YFinanceDownloader


class TestYFinanceDownloader:
    """Test cases for YFinanceDownloader."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.downloader = YFinanceDownloader()
    
    def test_init(self):
        """Test YFinanceDownloader initialization."""
        assert self.downloader is not None
        assert hasattr(self.downloader, 'download_data')
    
    @patch('finance_tools.stocks.data_downloaders.yfinance.yf')
    def test_download_data(self, mock_yf):
        """Test downloading stock data."""
        # Mock the yfinance download
        mock_data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [105, 106, 107],
            'Low': [95, 96, 97],
            'Close': [103, 104, 105],
            'Volume': [1000, 1100, 1200]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        mock_yf.download.return_value = mock_data
        
        # Test the download
        result = self.downloader.download_data("AAPL", period="1d")
        
        # Verify the result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert list(result.columns) == ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Verify yfinance was called correctly
        mock_yf.download.assert_called_once_with("AAPL", period="1d")
    
    @patch('finance_tools.stocks.data_downloaders.yfinance.yf')
    def test_get_current_price(self, mock_yf):
        """Test getting current price."""
        mock_ticker = Mock()
        mock_ticker.info = {'regularMarketPrice': 150.0}
        mock_yf.Ticker.return_value = mock_ticker
        
        result = self.downloader.get_current_price("AAPL")
        
        assert result == 150.0
        mock_yf.Ticker.assert_called_once_with("AAPL")
    
    @patch('finance_tools.stocks.data_downloaders.yfinance.yf')
    def test_get_company_info(self, mock_yf):
        """Test getting company information."""
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Apple Inc.',
            'sector': 'Technology',
            'marketCap': 2000000000000
        }
        mock_yf.Ticker.return_value = mock_ticker
        
        result = self.downloader.get_company_info("AAPL")
        
        assert result['longName'] == 'Apple Inc.'
        assert result['sector'] == 'Technology'
        assert result['marketCap'] == 2000000000000
        mock_yf.Ticker.assert_called_once_with("AAPL")
    
    def test_invalid_symbol(self):
        """Test handling of invalid stock symbol."""
        with pytest.raises(Exception):
            self.downloader.download_data("INVALID_SYMBOL_12345", period="1d")
    
    def test_invalid_period(self):
        """Test handling of invalid period."""
        with pytest.raises(ValueError):
            self.downloader.download_data("AAPL", period="invalid_period") 