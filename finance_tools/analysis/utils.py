# finance_tools/analysis/utils.py
"""
Utility functions for technical analysis module.

This module provides helper functions for data processing, validation,
result formatting, and other common operations used in technical analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


def validate_ohlcv_data(data: pd.DataFrame, required_columns: List[str] = None) -> bool:
    """
    Validate OHLCV data structure and content.
    
    Args:
        data: DataFrame to validate
        required_columns: List of required columns (default: ['open', 'high', 'low', 'close'])
    
    Returns:
        bool: True if data is valid
    
    Raises:
        ValueError: If data is invalid
    """
    if required_columns is None:
        required_columns = ['open', 'high', 'low', 'close']
    
    if not isinstance(data, pd.DataFrame):
        raise ValueError("Data must be a pandas DataFrame")
    
    if data.empty:
        raise ValueError("Data cannot be empty")
    
    # Check required columns
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Check data types
    for col in required_columns:
        if not pd.api.types.is_numeric_dtype(data[col]):
            raise ValueError(f"Column '{col}' must be numeric")
    
    # Check for negative prices
    for col in ['open', 'high', 'low', 'close']:
        if col in data.columns and (data[col] < 0).any():
            raise ValueError(f"Column '{col}' contains negative values")
    
    # Check OHLC relationships
    if all(col in data.columns for col in ['open', 'high', 'low', 'close']):
        invalid_high = (data['high'] < data[['open', 'close']].max(axis=1)).any()
        invalid_low = (data['low'] > data[['open', 'close']].min(axis=1)).any()
        
        if invalid_high:
            raise ValueError("High price cannot be less than open or close")
        if invalid_low:
            raise ValueError("Low price cannot be greater than open or close")
    
    return True


def clean_data(data: pd.DataFrame, method: str = "drop") -> pd.DataFrame:
    """
    Clean data by handling missing values and outliers.
    
    Args:
        data: DataFrame to clean
        method: Method for handling missing values ('drop', 'forward_fill', 'backward_fill')
    
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    if method not in ["drop", "forward_fill", "backward_fill"]:
        raise ValueError("Method must be 'drop', 'forward_fill', or 'backward_fill'")
    
    cleaned_data = data.copy()
    
    # Handle missing values
    if method == "drop":
        cleaned_data = cleaned_data.dropna()
    elif method == "forward_fill":
        cleaned_data = cleaned_data.fillna(method='ffill')
    elif method == "backward_fill":
        cleaned_data = cleaned_data.fillna(method='bfill')
    
    # Remove outliers (prices that are more than 3 standard deviations from mean)
    for col in ['open', 'high', 'low', 'close']:
        if col in cleaned_data.columns:
            mean = cleaned_data[col].mean()
            std = cleaned_data[col].std()
            lower_bound = mean - 3 * std
            upper_bound = mean + 3 * std
            
            # Replace outliers with NaN
            cleaned_data.loc[cleaned_data[col] < lower_bound, col] = np.nan
            cleaned_data.loc[cleaned_data[col] > upper_bound, col] = np.nan
    
    # Drop rows with NaN values after outlier removal
    cleaned_data = cleaned_data.dropna()
    
    logger.info(f"Cleaned data: {len(data)} -> {len(cleaned_data)} rows")
    return cleaned_data


def prepare_data_for_analysis(data: pd.DataFrame, 
                            symbol: str = None,
                            start_date: str = None,
                            end_date: str = None) -> pd.DataFrame:
    """
    Prepare data for technical analysis.
    
    Args:
        data: Raw OHLCV data
        symbol: Symbol name for identification
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)
    
    Returns:
        pd.DataFrame: Prepared data
    """
    # Validate data
    validate_ohlcv_data(data)
    
    # Filter by date range if provided
    if start_date or end_date:
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
    
    # Clean data
    data = clean_data(data)
    
    # Add symbol column if provided
    if symbol:
        data['symbol'] = symbol
    
    logger.info(f"Prepared data for analysis: {len(data)} rows")
    return data


def format_analysis_results(results: Dict[str, Any], 
                          include_metadata: bool = True,
                          round_decimals: int = 4) -> Dict[str, Any]:
    """
    Format analysis results for output.
    
    Args:
        results: Raw analysis results
        include_metadata: Whether to include metadata
        round_decimals: Number of decimal places to round
    
    Returns:
        Dict[str, Any]: Formatted results
    """
    formatted_results = {}
    
    # Round numeric values
    for key, value in results.items():
        if isinstance(value, pd.Series):
            formatted_results[key] = value.round(round_decimals)
        elif isinstance(value, (int, float)):
            formatted_results[key] = round(value, round_decimals)
        else:
            formatted_results[key] = value
    
    # Add metadata if requested
    if include_metadata:
        formatted_results['metadata'] = {
            'calculation_time': datetime.now().isoformat(),
            'total_indicators': len([k for k in results.keys() if not k.endswith('_error')]),
            'errors': [k for k in results.keys() if k.endswith('_error')],
            'data_points': len(next(iter(results.values()))) if results else 0
        }
    
    return formatted_results


def calculate_performance_metrics(prices: pd.Series, 
                                signals: pd.Series = None) -> Dict[str, float]:
    """
    Calculate performance metrics for a price series.
    
    Args:
        prices: Price series
        signals: Trading signals series (optional)
    
    Returns:
        Dict[str, float]: Performance metrics
    """
    metrics = {}
    
    # Basic price metrics
    metrics['total_return'] = ((prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]) * 100
    metrics['max_price'] = prices.max()
    metrics['min_price'] = prices.min()
    metrics['current_price'] = prices.iloc[-1]
    metrics['price_volatility'] = prices.pct_change().std() * 100
    
    # Calculate drawdown
    cumulative_max = prices.expanding().max()
    drawdown = (prices - cumulative_max) / cumulative_max * 100
    metrics['max_drawdown'] = drawdown.min()
    
    # Calculate Sharpe ratio (assuming risk-free rate of 0)
    returns = prices.pct_change().dropna()
    if len(returns) > 0:
        metrics['sharpe_ratio'] = returns.mean() / returns.std() if returns.std() > 0 else 0
    else:
        metrics['sharpe_ratio'] = 0
    
    # Trading signals analysis if provided
    if signals is not None and len(signals) > 0:
        buy_signals = (signals == 'BUY').sum()
        sell_signals = (signals == 'SELL').sum()
        neutral_signals = (signals == 'NEUTRAL').sum()
        
        metrics['buy_signals'] = buy_signals
        metrics['sell_signals'] = sell_signals
        metrics['neutral_signals'] = neutral_signals
        metrics['total_signals'] = len(signals.dropna())
    
    return metrics


def create_summary_report(data: pd.DataFrame, 
                        indicators: Dict[str, Any],
                        signals: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a comprehensive summary report.
    
    Args:
        data: OHLCV data
        indicators: Calculated indicators
        signals: Trading signals (optional)
    
    Returns:
        Dict[str, Any]: Summary report
    """
    # Handle date formatting safely
    start_date = None
    end_date = None
    if len(data) > 0:
        try:
            if hasattr(data.index[0], 'strftime'):
                start_date = data.index[0].strftime('%Y-%m-%d')
            else:
                start_date = str(data.index[0])
        except:
            start_date = str(data.index[0])
        
        try:
            if hasattr(data.index[-1], 'strftime'):
                end_date = data.index[-1].strftime('%Y-%m-%d')
            else:
                end_date = str(data.index[-1])
        except:
            end_date = str(data.index[-1])
    
    report = {
        'data_summary': {
            'symbol': data.get('symbol', data.get('Symbol', 'Unknown')).iloc[0] if ('symbol' in data.columns or 'Symbol' in data.columns) else 'Unknown',
            'start_date': start_date,
            'end_date': end_date,
            'total_days': len(data),
            'data_points': len(data)
        },
        'price_summary': calculate_performance_metrics(data.get('close', data.get('Close', pd.Series()))),
        'indicators_summary': {},
        'signals_summary': signals if signals else {}
    }
    
    # Add indicator summaries
    for indicator_name, indicator_data in indicators.items():
        if isinstance(indicator_data, pd.Series) and not indicator_name.endswith('_error'):
            report['indicators_summary'][indicator_name] = {
                'current_value': float(indicator_data.iloc[-1]) if len(indicator_data) > 0 else None,
                'min_value': float(indicator_data.min()) if len(indicator_data) > 0 else None,
                'max_value': float(indicator_data.max()) if len(indicator_data) > 0 else None,
                'mean_value': float(indicator_data.mean()) if len(indicator_data) > 0 else None
            }
    
    return report


def export_results(results: Dict[str, Any], 
                  filename: str,
                  format: str = 'json') -> str:
    """
    Export analysis results to file.
    
    Args:
        results: Analysis results
        filename: Output filename
        format: Export format ('json', 'csv', 'excel')
    
    Returns:
        str: Path to exported file
    """
    if format == 'json':
        # Convert pandas Series to lists for JSON serialization
        json_results = {}
        for key, value in results.items():
            if isinstance(value, pd.Series):
                json_results[key] = value.tolist()
            elif isinstance(value, pd.DataFrame):
                json_results[key] = value.to_dict('records')
            else:
                json_results[key] = value
        
        with open(filename, 'w') as f:
            json.dump(json_results, f, indent=2, default=str)
    
    elif format == 'csv':
        # Export as CSV (only for DataFrame results)
        if isinstance(results, pd.DataFrame):
            results.to_csv(filename)
        else:
            # Convert dict to DataFrame if possible
            df_results = pd.DataFrame(results)
            df_results.to_csv(filename)
    
    elif format == 'excel':
        # Export as Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for key, value in results.items():
                if isinstance(value, pd.Series):
                    value.to_frame(name=key).to_excel(writer, sheet_name=key)
                elif isinstance(value, pd.DataFrame):
                    value.to_excel(writer, sheet_name=key)
                else:
                    pd.DataFrame({key: [value]}).to_excel(writer, sheet_name=key)
    
    else:
        raise ValueError("Format must be 'json', 'csv', or 'excel'")
    
    logger.info(f"Exported results to {filename}")
    return filename


def validate_indicator_parameters(indicator_name: str, 
                                parameters: Dict[str, Any]) -> bool:
    """
    Validate parameters for a specific indicator.
    
    Args:
        indicator_name: Name of the indicator
        parameters: Parameters to validate
    
    Returns:
        bool: True if parameters are valid
    
    Raises:
        ValueError: If parameters are invalid
    """
    if indicator_name == 'rsi':
        if 'period' in parameters:
            if not isinstance(parameters['period'], int) or parameters['period'] < 2:
                raise ValueError("RSI period must be an integer >= 2")
    
    elif indicator_name == 'macd':
        if 'fast_period' in parameters and 'slow_period' in parameters:
            if parameters['fast_period'] >= parameters['slow_period']:
                raise ValueError("MACD fast period must be less than slow period")
    
    elif indicator_name == 'bollinger_bands':
        if 'std_dev' in parameters:
            if parameters['std_dev'] <= 0:
                raise ValueError("Bollinger Bands std_dev must be positive")
    
    elif indicator_name == 'supertrend':
        if 'multiplier' in parameters:
            if parameters['multiplier'] <= 0:
                raise ValueError("Supertrend multiplier must be positive")
    
    return True


def get_indicator_dependencies(indicator_name: str) -> List[str]:
    """
    Get the data dependencies for a specific indicator.
    
    Args:
        indicator_name: Name of the indicator
    
    Returns:
        List[str]: Required data columns
    """
    dependencies = {
        'ema': ['close'],
        'sma': ['close'],
        'wma': ['close'],
        'rsi': ['close'],
        'macd': ['close'],
        'bollinger_bands': ['close'],
        'momentum': ['close'],
        'supertrend': ['high', 'low', 'close'],
        'atr': ['high', 'low', 'close'],
        'stochastic': ['high', 'low', 'close'],
        'roc': ['close'],
        'cci': ['high', 'low', 'close'],
        'adx': ['high', 'low', 'close'],
        'obv': ['close', 'volume'],
        'vwap': ['high', 'low', 'close', 'volume'],
        'support_resistance': ['high', 'low']
    }
    
    return dependencies.get(indicator_name, ['close'])


def check_data_completeness(data: pd.DataFrame, 
                           indicators: List[str]) -> Dict[str, bool]:
    """
    Check if data is complete for the requested indicators.
    
    Args:
        data: OHLCV data
        indicators: List of indicators to check
    
    Returns:
        Dict[str, bool]: Completeness status for each indicator
    """
    completeness = {}
    
    for indicator in indicators:
        dependencies = get_indicator_dependencies(indicator)
        missing_columns = [col for col in dependencies if col not in data.columns]
        
        completeness[indicator] = len(missing_columns) == 0
        
        if missing_columns:
            logger.warning(f"Indicator '{indicator}' missing columns: {missing_columns}")
    
    return completeness 