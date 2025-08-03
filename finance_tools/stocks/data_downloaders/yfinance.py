"""Stock data retrieval tool using yfinance with impersonation to avoid rate limits."""

import yfinance as yf
import pandas as pd
from typing import Dict, Any, List, Union, Optional
from datetime import datetime, timedelta
import time
import random
from curl_cffi import requests

from ...config import get_config
from ...utils.dataframe_utils import get_as_df


class DownloadResult:
    """Result class that supports as_df() method."""
    
    def __init__(self, data: Dict[str, Any], metadata: Dict[str, Any]):
        self.data = data
        self.metadata = metadata
    
    def as_df(self) -> pd.DataFrame:
        """Convert result to DataFrame."""
        return get_as_df(self)


class YFinanceDownloader:
    """Simplified tool for downloading stock data using yfinance."""
    
    def __init__(self):
        self._session = requests.Session(impersonate="chrome")
        self.config = get_config()
        self._user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    
    def _parse_symbols(self, symbols_input: Union[str, List[str]]) -> List[str]:
        """Parse symbols input into a list of symbols."""
        if isinstance(symbols_input, str):
            # Handle comma-separated string
            if ',' in symbols_input:
                return [s.strip() for s in symbols_input.split(',')]
            else:
                return [symbols_input.strip()]
        elif isinstance(symbols_input, list):
            return [str(s).strip() for s in symbols_input]
        else:
            raise ValueError(f"Unsupported symbols format: {type(symbols_input)}")
    
    def _setup_impersonation(self):
        """Setup user agent impersonation."""
        if self._session:
            user_agent = random.choice(self._user_agents)
            self._session.headers.update({
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
    
    def _format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format DataFrame with proper date formatting and column ordering.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Formatted DataFrame with YYYY-MM-DD dates and Symbol column after Date
        """
        if df.empty:
            return df
        
        # Check if the index is a DatetimeIndex (which we want to convert to Date column)
        index_is_datetime = isinstance(df.index, pd.DatetimeIndex)
        
        # Reset index to make date a column
        df = df.reset_index()
        
        # Handle date formatting
        date_col = None
        
        # If the original index was a DatetimeIndex, it becomes the 'index' column
        if index_is_datetime and 'index' in df.columns:
            # Rename index to Date and remove any existing Date column to avoid duplicates
            if 'Date' in df.columns:
                df = df.drop('Date', axis=1)
            df = df.rename(columns={'index': 'Date'})
            date_col = 'Date'
        elif 'Date' in df.columns:
            # If Date column already exists, use it
            date_col = 'Date'
        elif 'index' in df.columns:
            # If we have an index column but it's not from a DatetimeIndex, 
            # check if it looks like a date column
            try:
                # Try to convert to datetime to see if it's a date
                pd.to_datetime(df['index'])
                # If successful, rename it to Date
                df = df.rename(columns={'index': 'Date'})
                date_col = 'Date'
            except:
                # If it's not a date, drop the index column
                df = df.drop('index', axis=1)
        
        # Format the date column if we found one
        if date_col and date_col in df.columns:
            try:
                # Convert to datetime and format
                df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')
            except Exception as e:
                # If conversion fails, try to handle as string
                try:
                    df[date_col] = df[date_col].astype(str)
                except:
                    print(f"Warning: Could not format date column {date_col}: {e}")
        
        # Remove any remaining 'index' column that shouldn't be there
        if 'index' in df.columns:
            df = df.drop('index', axis=1)
        
        # Reorder columns to put Symbol after Date
        if 'Symbol' in df.columns and 'Date' in df.columns:
            # Get all columns except Date and Symbol
            other_cols = [col for col in df.columns if col not in ['Date', 'Symbol']]
            # Reorder: Date, Symbol, then other columns
            df = df[['Date', 'Symbol'] + other_cols]
        
        return df
    
    def download(self, symbols: Union[str, List[str]], 
                start_date: Optional[str] = None,
                end_date: Optional[str] = None,
                period: str = "1y",
                interval: str = "1d",
                include_dividends: bool = False,
                include_splits: bool = False,
                auto_adjust: bool = True,
                use_impersonation: bool = True) -> DownloadResult:
        """
        Download stock data with flexible input formats.
        
        Args:
            symbols: Stock symbol(s) - can be:
                - String: "AAPL" or "AAPL, MSFT"
                - List: ["AAPL"] or ["AAPL", "MSFT"]
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            period: Period for data download (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            include_dividends: Include dividend information
            include_splits: Include stock split information
            auto_adjust: Automatically adjust prices for splits and dividends
            use_impersonation: Use browser impersonation to avoid rate limits
        
        Returns:
            DownloadResult object with data and metadata
        """
        start_time = time.time()
        
        try:
            # Parse symbols
            symbols_list = self._parse_symbols(symbols)
            
            if not symbols_list:
                raise ValueError("No valid symbols provided")
            
            # Setup impersonation if requested
            if use_impersonation:
                self._setup_impersonation()
            
            # Download data
            if len(symbols_list) == 1:
                result_data, metadata = self._download_single_stock(
                    symbols_list[0], start_date, end_date, period, interval,
                    include_dividends, include_splits, auto_adjust
                )
            else:
                result_data, metadata = self._download_multiple_stocks(
                    symbols_list, start_date, end_date, period, interval,
                    include_dividends, include_splits, auto_adjust
                )
            
            # Add execution metadata
            execution_time = time.time() - start_time
            metadata.update({
                "execution_time": execution_time,
                "symbols_requested": symbols_list,
                "symbols_processed": symbols_list,
                "period": period if not start_date else f"{start_date} to {end_date}",
                "interval": interval,
                "use_impersonation": use_impersonation
            })
            
            return DownloadResult(result_data, metadata)
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_metadata = {
                "error": str(e),
                "execution_time": execution_time,
                "symbols_requested": self._parse_symbols(symbols) if symbols else [],
                "success": False
            }
            return DownloadResult({"data": pd.DataFrame()}, error_metadata)
    
    def _download_single_stock(self, symbol: str, start_date: str, end_date: str, 
                              period: str, interval: str, include_dividends: bool,
                              include_splits: bool, auto_adjust: bool) -> tuple:
        """Download data for a single stock."""
        
        # Create ticker object
        ticker = yf.Ticker(symbol, session=self._session)
        
        # Prepare download parameters
        download_params = {
            'interval': interval,
            'auto_adjust': auto_adjust,
            'prepost': True
        }
        
        # Use period or date range
        if start_date and end_date:
            download_params['start'] = start_date
            download_params['end'] = end_date
        else:
            download_params['period'] = period
        
        # Add small delay to avoid rate limiting
        time.sleep(random.uniform(0.1, 0.5))
        
        # Download historical data
        hist_data = ticker.history(**download_params)
        
        if hist_data.empty:
            raise ValueError(f"No data found for symbol {symbol}")
        
        # Add symbol column for identification
        hist_data['Symbol'] = symbol
        
        # Format the DataFrame with proper date formatting and column ordering
        hist_data = self._format_dataframe(hist_data)
        
        # Get additional data if requested
        additional_data = {}
        
        if include_dividends:
            try:
                dividends = ticker.dividends
                if not dividends.empty:
                    additional_data['dividends'] = dividends
            except Exception as e:
                print(f"Warning: Could not fetch dividends for {symbol}: {e}")
        
        if include_splits:
            try:
                splits = ticker.splits
                if not splits.empty:
                    additional_data['splits'] = splits
            except Exception as e:
                print(f"Warning: Could not fetch splits for {symbol}: {e}")
        
        # Get basic info
        try:
            info = ticker.info
            basic_info = {
                'symbol': symbol,
                'longName': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'N/A')
            }
        except Exception:
            basic_info = {'symbol': symbol}
        
        metadata = {
            'basic_info': basic_info,
            'additional_data': list(additional_data.keys()),
            'data_columns': list(hist_data.columns),
            'date_range': {
                'start': hist_data.index.min().strftime('%Y-%m-%d') if not hist_data.empty and hasattr(hist_data.index.min(), 'strftime') else None,
                'end': hist_data.index.max().strftime('%Y-%m-%d') if not hist_data.empty and hasattr(hist_data.index.max(), 'strftime') else None
            }
        }
        
        # Return dictionary with data key containing the DataFrame
        result_data = {
            'data': hist_data,
            **additional_data
        }
        
        return result_data, metadata
    
    def _download_multiple_stocks(self, symbols: List[str], start_date: str, end_date: str,
                                 period: str, interval: str, include_dividends: bool,
                                 include_splits: bool, auto_adjust: bool) -> tuple:
        """Download data for multiple stocks."""
        
        # Try the new approach: download stocks individually and combine
        if len(symbols) > 1:
            return self._download_multiple_stocks_individual(symbols, start_date, end_date,
                                                          period, interval, include_dividends,
                                                          include_splits, auto_adjust)
        
        # For single symbol, use the original approach
        # Prepare download parameters
        download_params = {
            'interval': interval,
            'auto_adjust': auto_adjust,
            'prepost': True,
            'group_by': 'ticker'
        }
        
        # Use period or date range
        if start_date and end_date:
            download_params['start'] = start_date
            download_params['end'] = end_date
        else:
            download_params['period'] = period
        
        # Add delay to avoid rate limiting
        time.sleep(random.uniform(0.2, 0.8))
        
        # Download data for all symbols
        data = yf.download(symbols, **download_params, session=self._session)
        
        if data.empty:
            raise ValueError(f"No data found for symbols {symbols}")
        
        # Debug: Print data structure information (only in debug mode)
        if self.config.is_feature_enabled("debug"):
            print(f"Downloaded data shape: {data.shape}")
            print(f"Data columns type: {type(data.columns)}")
            print(f"Data columns: {data.columns}")
            if isinstance(data.columns, pd.MultiIndex):
                print(f"MultiIndex levels: {data.columns.levels}")
                print(f"MultiIndex names: {data.columns.names}")
        
        # Process multi-index columns if multiple symbols
        if len(symbols) > 1:
            # Reorganize data to have symbol as a column
            processed_data = {}
            
            # Check the structure of the downloaded data
            if isinstance(data.columns, pd.MultiIndex):
                # Handle multi-index columns
                for symbol in symbols:
                    try:
                        # Try different approaches to extract symbol data
                        symbol_data = None
                        
                        # Method 1: Try to extract by symbol name from column names
                        symbol_columns = [col for col in data.columns if symbol in str(col)]
                        if symbol_columns:
                            symbol_data = data[symbol_columns].copy()
                            # Flatten column names if they're tuples
                            if isinstance(symbol_data.columns, pd.MultiIndex):
                                symbol_data.columns = [col[1] if isinstance(col, tuple) else col for col in symbol_data.columns]
                            if self.config.is_feature_enabled("debug"):
                                print(f"Found {len(symbol_columns)} columns for {symbol}: {symbol_columns}")
                        
                        # Method 2: If Method 1 failed, try xs approach
                        if symbol_data is None or symbol_data.empty:
                            try:
                                symbol_data = data.xs(symbol, level=1, axis=1)
                            except (KeyError, IndexError):
                                pass
                        
                        # Method 3: If still no data, try level 0
                        if symbol_data is None or symbol_data.empty:
                            try:
                                symbol_data = data.xs(symbol, level=0, axis=1)
                            except (KeyError, IndexError):
                                pass
                        
                        # Method 4: Fallback - try to extract by position if we know the order
                        if symbol_data is None or symbol_data.empty:
                            try:
                                symbol_index = symbols.index(symbol)
                                # Try to extract columns by position (this is a last resort)
                                if symbol_index < len(data.columns):
                                    symbol_data = data.iloc[:, symbol_index:symbol_index+1].copy()
                                    if not symbol_data.empty:
                                        symbol_data.columns = ['Close']  # Assume it's close price
                            except (IndexError, ValueError):
                                pass
                        
                        if symbol_data is not None and not symbol_data.empty:
                            symbol_data['Symbol'] = symbol
                            processed_data[symbol] = symbol_data
                            if self.config.is_feature_enabled("debug"):
                                print(f"Successfully processed {symbol} with shape: {symbol_data.shape}")
                        else:
                            print(f"Warning: No data found for symbol {symbol}")
                            
                    except Exception as e:
                        print(f"Warning: Error processing symbol {symbol}: {e}")
            else:
                # Single column structure - treat as single symbol data
                combined_data = data.copy()
                combined_data['Symbol'] = symbols[0] if len(symbols) == 1 else 'Unknown'
                return self._create_result_data(combined_data, {}, {}, symbols)
            
            # Combine all symbol data
            if processed_data:
                combined_data = pd.concat(processed_data.values(), ignore_index=False)
                combined_data = combined_data.sort_index()
            else:
                combined_data = pd.DataFrame()
        else:
            # Single symbol
            combined_data = data.copy()
            combined_data['Symbol'] = symbols[0]
        
        # Get additional data for each symbol if requested
        additional_data = {}
        basic_info = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol, session=self._session)
                
                # Get basic info
                try:
                    info = ticker.info
                    basic_info[symbol] = {
                        'longName': info.get('longName', 'N/A'),
                        'sector': info.get('sector', 'N/A'),
                        'industry': info.get('industry', 'N/A'),
                        'currency': info.get('currency', 'USD'),
                        'exchange': info.get('exchange', 'N/A')
                    }
                except Exception:
                    basic_info[symbol] = {}
                
                # Get dividends and splits if requested
                if include_dividends:
                    try:
                        dividends = ticker.dividends
                        if not dividends.empty:
                            if 'dividends' not in additional_data:
                                additional_data['dividends'] = {}
                            additional_data['dividends'][symbol] = dividends
                    except Exception as e:
                        print(f"Warning: Could not fetch dividends for {symbol}: {e}")
                
                if include_splits:
                    try:
                        splits = ticker.splits
                        if not splits.empty:
                            if 'splits' not in additional_data:
                                additional_data['splits'] = {}
                            additional_data['splits'][symbol] = splits
                    except Exception as e:
                        print(f"Warning: Could not fetch splits for {symbol}: {e}")
                
                # Small delay between requests
                time.sleep(random.uniform(0.1, 0.3))
                
            except Exception as e:
                print(f"Warning: Error processing {symbol}: {e}")
        
        return self._create_result_data(combined_data, additional_data, basic_info, symbols)
    
    def _download_multiple_stocks_individual(self, symbols: List[str], start_date: str, end_date: str,
                                           period: str, interval: str, include_dividends: bool,
                                           include_splits: bool, auto_adjust: bool) -> tuple:
        """Download multiple stocks by downloading each individually and combining."""
        
        all_data = []
        additional_data = {}
        basic_info = {}
        
        for symbol in symbols:
            try:
                if self.config.is_feature_enabled("debug"):
                    print(f"Downloading data for {symbol}...")
                
                # Download single stock data
                single_result, single_metadata = self._download_single_stock(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    period=period,
                    interval=interval,
                    include_dividends=include_dividends,
                    include_splits=include_splits,
                    auto_adjust=auto_adjust
                )
                
                # Add to combined data
                if 'data' in single_result and not single_result['data'].empty:
                    all_data.append(single_result['data'])
                
                # Add additional data
                for key, value in single_result.items():
                    if key != 'data':
                        if key not in additional_data:
                            additional_data[key] = {}
                        additional_data[key][symbol] = value
                
                # Add basic info
                if 'basic_info' in single_metadata:
                    basic_info[symbol] = single_metadata['basic_info']
                
                # Small delay between downloads
                time.sleep(random.uniform(0.1, 0.3))
                
            except Exception as e:
                print(f"Warning: Failed to download {symbol}: {e}")
        
        # Combine all price data
        if all_data:
            combined_data = pd.concat(all_data, ignore_index=False)
            combined_data = combined_data.sort_index()
        else:
            combined_data = pd.DataFrame()
        
        return self._create_result_data(combined_data, additional_data, basic_info, symbols)
    
    def _create_result_data(self, combined_data: pd.DataFrame, additional_data: Dict, 
                           basic_info: Dict, symbols: List[str]) -> tuple:
        """Helper method to create result data structure."""
        # Format the combined data with proper date formatting and column ordering
        if not combined_data.empty:
            combined_data = self._format_dataframe(combined_data)
        
        metadata = {
            'basic_info': basic_info,
            'additional_data': list(additional_data.keys()),
            'data_columns': list(combined_data.columns) if not combined_data.empty else [],
            'symbols_processed': symbols,
            'date_range': {
                'start': combined_data['Date'].min() if not combined_data.empty and 'Date' in combined_data.columns and len(combined_data['Date']) > 0 else None,
                'end': combined_data['Date'].max() if not combined_data.empty and 'Date' in combined_data.columns and len(combined_data['Date']) > 0 else None
            }
        }
        
        # Return dictionary with data key containing the DataFrame
        result_data = {
            'data': combined_data,
            **additional_data
        }
        
        return result_data, metadata


# Also create a function-based interface for easier use
def get_stock_data_yf(symbols: Union[str, List[str]], start_date: str = None, end_date: str = None,
                     period: str = "1y", interval: str = "1d", **kwargs) -> pd.DataFrame:
    """
    Download stock data using yfinance.
    
    Args:
        symbols: Stock symbol(s) - can be string or list
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        period: Period for data download (optional)
        interval: Data interval (optional)
        **kwargs: Additional arguments
    
    Returns:
        pandas.DataFrame with stock data
    """
    tool = YFinanceDownloader()
    result = tool.download(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        period=period,
        interval=interval,
        **kwargs
    )
    
    if result.metadata.get('error'):
        raise Exception(result.metadata['error'])
    
    return result.as_df()