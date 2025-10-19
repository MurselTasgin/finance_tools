"""Technical analysis tool implementing common indicators like EMA, MACD, RSI, Momentum."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union, Optional
import time

from ..data_downloaders.base_tool import BaseTool, ToolResult, ToolArgument, ToolCapability, ToolArgumentType, register_tool


class TechnicalAnalysisTool(BaseTool):
    """Tool for performing technical analysis on stock data."""
    
    def __init__(self):
        super().__init__(
            name="technical_analysis",
            description="""
            Calculate advanced technical analysis indicators including Exponential Moving Averages (EMA), MACD, RSI, Momentum, 
            and Bollinger Bands for stock price patterns and trading signal analysis. Provides detailed technical insights and trend identification for investment decisions.
            Does not support visualizations, charts or graphs. 
            """,
            version="1.0.0"
        )
        self._setup_arguments()
        self._setup_capabilities()
    
    def _setup_arguments(self):
        """Setup tool arguments."""
        self.add_argument(ToolArgument(
            name="data",
            type=ToolArgumentType.DICT,
            description="Stock price data (DataFrame or dict with OHLCV columns)",
            required=True
        ))
        
        self.add_argument(ToolArgument(
            name="indicators",
            type=ToolArgumentType.LIST,
            description="List of indicators to calculate (EMA, SMA, MACD, RSI, BB, STOCH, MOMENTUM, ROC, ATR, CCI)",
            required=True
        ))
        
        self.add_argument(ToolArgument(
            name="symbol",
            type=ToolArgumentType.STRING,
            description="Stock symbol for identification (optional)",
            required=False,
            default=None
        ))
        
        self.add_argument(ToolArgument(
            name="ema_periods",
            type=ToolArgumentType.LIST,
            description="EMA periods to calculate (default: [12, 26, 50, 200])",
            required=False,
            default=[12, 26, 50, 200]
        ))
        
        self.add_argument(ToolArgument(
            name="sma_periods",
            type=ToolArgumentType.LIST,
            description="SMA periods to calculate (default: [20, 50, 200])",
            required=False,
            default=[20, 50, 200]
        ))
        
        self.add_argument(ToolArgument(
            name="rsi_period",
            type=ToolArgumentType.INTEGER,
            description="RSI calculation period (default: 14)",
            required=False,
            default=14,
            min_value=2,
            max_value=100
        ))
        
        self.add_argument(ToolArgument(
            name="macd_fast",
            type=ToolArgumentType.INTEGER,
            description="MACD fast EMA period (default: 12)",
            required=False,
            default=12,
            min_value=1,
            max_value=50
        ))
        
        self.add_argument(ToolArgument(
            name="macd_slow",
            type=ToolArgumentType.INTEGER,
            description="MACD slow EMA period (default: 26)",
            required=False,
            default=26,
            min_value=1,
            max_value=100
        ))
        
        self.add_argument(ToolArgument(
            name="macd_signal",
            type=ToolArgumentType.INTEGER,
            description="MACD signal line period (default: 9)",
            required=False,
            default=9,
            min_value=1,
            max_value=50
        ))
        
        self.add_argument(ToolArgument(
            name="bb_period",
            type=ToolArgumentType.INTEGER,
            description="Bollinger Bands period (default: 20)",
            required=False,
            default=20,
            min_value=5,
            max_value=100
        ))
        
        self.add_argument(ToolArgument(
            name="bb_std",
            type=ToolArgumentType.FLOAT,
            description="Bollinger Bands standard deviation multiplier (default: 2.0)",
            required=False,
            default=2.0,
            min_value=0.5,
            max_value=5.0
        ))
        
        self.add_argument(ToolArgument(
            name="stoch_k_period",
            type=ToolArgumentType.INTEGER,
            description="Stochastic %K period (default: 14)",
            required=False,
            default=14,
            min_value=5,
            max_value=50
        ))
        
        self.add_argument(ToolArgument(
            name="stoch_d_period",
            type=ToolArgumentType.INTEGER,
            description="Stochastic %D period (default: 3)",
            required=False,
            default=3,
            min_value=1,
            max_value=20
        ))
        
        self.add_argument(ToolArgument(
            name="momentum_period",
            type=ToolArgumentType.INTEGER,
            description="Momentum calculation period (default: 10)",
            required=False,
            default=10,
            min_value=1,
            max_value=50
        ))
        
        self.add_argument(ToolArgument(
            name="atr_period",
            type=ToolArgumentType.INTEGER,
            description="ATR calculation period (default: 14)",
            required=False,
            default=14,
            min_value=5,
            max_value=50
        ))
        
        self.add_argument(ToolArgument(
            name="return_format",
            type=ToolArgumentType.STRING,
            description="Return format for results",
            required=False,
            default="dataframe",
            choices=["dataframe", "dict", "json"]
        ))
    
    def _setup_capabilities(self):
        """Setup tool capabilities."""
        self.add_capability(ToolCapability(
            name="moving_averages",
            description="Calculate EMA and SMA indicators",
            input_types=[ToolArgumentType.DICT, ToolArgumentType.LIST],
            output_type="pandas.DataFrame",
            examples=[
                "EMA(12), EMA(26), SMA(20), SMA(50)",
                "Multiple timeframes supported"
            ]
        ))
        
        self.add_capability(ToolCapability(
            name="momentum_indicators",
            description="Calculate RSI, MACD, Momentum, ROC",
            input_types=[ToolArgumentType.DICT, ToolArgumentType.LIST],
            output_type="pandas.DataFrame",
            examples=[
                "RSI(14), MACD(12,26,9), Momentum(10)",
                "Overbought/oversold signals"
            ]
        ))
        
        self.add_capability(ToolCapability(
            name="volatility_indicators",
            description="Calculate Bollinger Bands, ATR",
            input_types=[ToolArgumentType.DICT, ToolArgumentType.LIST],
            output_type="pandas.DataFrame",
            examples=[
                "Bollinger Bands(20,2), ATR(14)",
                "Volatility and range analysis"
            ]
        ))
        
        self.add_capability(ToolCapability(
            name="oscillators",
            description="Calculate Stochastic oscillator, CCI",
            input_types=[ToolArgumentType.DICT, ToolArgumentType.LIST],
            output_type="pandas.DataFrame",
            examples=[
                "Stochastic(14,3), CCI(20)",
                "Momentum oscillators for timing"
            ]
        ))
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute technical analysis."""
        start_time = time.time()
        
        try:
            validated_args = self.validate_arguments(**kwargs)
            
            data = validated_args["data"]
            indicators = [ind.upper() for ind in validated_args["indicators"]]
            symbol = validated_args.get("symbol")
            return_format = validated_args.get("return_format", "dataframe")
            
            # Convert data to DataFrame if it's a dict
            if isinstance(data, dict):
                df = pd.DataFrame(data)
            elif isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                raise ValueError("Data must be a pandas DataFrame or dictionary")
            
            # Validate required columns
            required_columns = ['Open', 'High', 'Low', 'Close']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                # Try alternative column names
                column_mapping = {
                    'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close',
                    'volume': 'Volume', 'adj close': 'Adj Close'
                }
                
                for old_name, new_name in column_mapping.items():
                    if old_name in df.columns:
                        df[new_name] = df[old_name]
                
                # Check again
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    return ToolResult(
                        success=False,
                        error=f"Missing required columns: {missing_columns}. Available: {list(df.columns)}"
                    )
            
            # Sort by index (date) to ensure proper calculation
            df = df.sort_index()
            
            # Calculate indicators
            results_df = df.copy()
            calculations_performed = []
            
            for indicator in indicators:
                try:
                    if indicator == 'EMA':
                        ema_periods = validated_args.get("ema_periods", [12, 26, 50, 200])
                        for period in ema_periods:
                            results_df[f'EMA_{period}'] = self._calculate_ema(df['Close'], period)
                            calculations_performed.append(f'EMA_{period}')
                    
                    elif indicator == 'SMA':
                        sma_periods = validated_args.get("sma_periods", [20, 50, 200])
                        for period in sma_periods:
                            results_df[f'SMA_{period}'] = self._calculate_sma(df['Close'], period)
                            calculations_performed.append(f'SMA_{period}')
                    
                    elif indicator == 'RSI':
                        rsi_period = validated_args.get("rsi_period", 14)
                        results_df['RSI'] = self._calculate_rsi(df['Close'], rsi_period)
                        calculations_performed.append('RSI')
                    
                    elif indicator == 'MACD':
                        macd_fast = validated_args.get("macd_fast", 12)
                        macd_slow = validated_args.get("macd_slow", 26)
                        macd_signal = validated_args.get("macd_signal", 9)
                        
                        macd_line, macd_signal_line, macd_histogram = self._calculate_macd(
                            df['Close'], macd_fast, macd_slow, macd_signal
                        )
                        results_df['MACD'] = macd_line
                        results_df['MACD_Signal'] = macd_signal_line
                        results_df['MACD_Histogram'] = macd_histogram
                        calculations_performed.extend(['MACD', 'MACD_Signal', 'MACD_Histogram'])
                    
                    elif indicator == 'BB':
                        bb_period = validated_args.get("bb_period", 20)
                        bb_std = validated_args.get("bb_std", 2.0)
                        
                        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
                            df['Close'], bb_period, bb_std
                        )
                        results_df['BB_Upper'] = bb_upper
                        results_df['BB_Middle'] = bb_middle
                        results_df['BB_Lower'] = bb_lower
                        calculations_performed.extend(['BB_Upper', 'BB_Middle', 'BB_Lower'])
                    
                    elif indicator == 'STOCH':
                        stoch_k_period = validated_args.get("stoch_k_period", 14)
                        stoch_d_period = validated_args.get("stoch_d_period", 3)
                        
                        stoch_k, stoch_d = self._calculate_stochastic(
                            df['High'], df['Low'], df['Close'], stoch_k_period, stoch_d_period
                        )
                        results_df['Stoch_K'] = stoch_k
                        results_df['Stoch_D'] = stoch_d
                        calculations_performed.extend(['Stoch_K', 'Stoch_D'])
                    
                    elif indicator == 'MOMENTUM':
                        momentum_period = validated_args.get("momentum_period", 10)
                        results_df['Momentum'] = self._calculate_momentum(df['Close'], momentum_period)
                        calculations_performed.append('Momentum')
                    
                    elif indicator == 'ROC':
                        roc_period = validated_args.get("momentum_period", 10)  # Use same period as momentum
                        results_df['ROC'] = self._calculate_roc(df['Close'], roc_period)
                        calculations_performed.append('ROC')
                    
                    elif indicator == 'ATR':
                        atr_period = validated_args.get("atr_period", 14)
                        results_df['ATR'] = self._calculate_atr(df['High'], df['Low'], df['Close'], atr_period)
                        calculations_performed.append('ATR')
                    
                    elif indicator == 'CCI':
                        cci_period = validated_args.get("bb_period", 20)  # Use same period as BB
                        results_df['CCI'] = self._calculate_cci(df['High'], df['Low'], df['Close'], cci_period)
                        calculations_performed.append('CCI')
                    
                    else:
                        print(f"Warning: Unknown indicator '{indicator}' skipped")
                
                except Exception as e:
                    print(f"Warning: Failed to calculate {indicator}: {str(e)}")
            
            # Format output
            formatted_results = self._format_output(results_df, return_format)
            
            # Generate analysis summary
            analysis_summary = self._generate_analysis_summary(results_df, calculations_performed)
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                data=formatted_results,
                metadata={
                    "symbol": symbol,
                    "indicators_calculated": calculations_performed,
                    "data_points": len(results_df),
                    "date_range": {
                        "start": results_df.index.min().strftime('%Y-%m-%d') if not results_df.empty else None,
                        "end": results_df.index.max().strftime('%Y-%m-%d') if not results_df.empty else None
                    },
                    "analysis_summary": analysis_summary,
                    "return_format": return_format
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Technical analysis failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return series.ewm(span=period, adjust=False).mean()
    
    def _calculate_sma(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return series.rolling(window=period).mean()
    
    def _calculate_rsi(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, series: pd.Series, fast: int, slow: int, signal: int) -> tuple:
        """Calculate MACD indicator."""
        ema_fast = self._calculate_ema(series, fast)
        ema_slow = self._calculate_ema(series, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def _calculate_bollinger_bands(self, series: pd.Series, period: int, std_dev: float) -> tuple:
        """Calculate Bollinger Bands."""
        sma = self._calculate_sma(series, period)
        std = series.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band, sma, lower_band
    
    def _calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                            k_period: int, d_period: int) -> tuple:
        """Calculate Stochastic Oscillator."""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return k_percent, d_percent
    
    def _calculate_momentum(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Momentum indicator."""
        return series.diff(period)
    
    def _calculate_roc(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Rate of Change."""
        return ((series / series.shift(period)) - 1) * 100
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """Calculate Average True Range."""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    def _calculate_cci(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """Calculate Commodity Channel Index."""
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )
        
        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
        return cci
    
    def _generate_analysis_summary(self, df: pd.DataFrame, indicators: List[str]) -> Dict[str, Any]:
        """Generate analysis summary from calculated indicators."""
        summary = {}
        
        try:
            latest_data = df.iloc[-1]
            
            # Price analysis
            if 'Close' in df.columns:
                current_price = latest_data['Close']
                summary['current_price'] = current_price
                
                # Moving average analysis
                ma_signals = []
                for col in df.columns:
                    if col.startswith(('EMA_', 'SMA_')):
                        ma_value = latest_data[col]
                        if pd.notna(ma_value):
                            signal = "above" if current_price > ma_value else "below"
                            ma_signals.append(f"Price {signal} {col}")
                
                summary['moving_average_signals'] = ma_signals
            
            # RSI analysis
            if 'RSI' in latest_data:
                rsi_value = latest_data['RSI']
                if pd.notna(rsi_value):
                    if rsi_value > 70:
                        rsi_signal = "Overbought"
                    elif rsi_value < 30:
                        rsi_signal = "Oversold"
                    else:
                        rsi_signal = "Normal"
                    
                    summary['rsi_analysis'] = {
                        'value': rsi_value,
                        'signal': rsi_signal
                    }
            
            # MACD analysis
            if 'MACD' in latest_data and 'MACD_Signal' in latest_data:
                macd_value = latest_data['MACD']
                macd_signal = latest_data['MACD_Signal']
                
                if pd.notna(macd_value) and pd.notna(macd_signal):
                    macd_trend = "Bullish" if macd_value > macd_signal else "Bearish"
                    summary['macd_analysis'] = {
                        'macd': macd_value,
                        'signal': macd_signal,
                        'trend': macd_trend
                    }
            
            # Bollinger Bands analysis
            if all(col in latest_data for col in ['BB_Upper', 'BB_Lower', 'Close']):
                bb_upper = latest_data['BB_Upper']
                bb_lower = latest_data['BB_Lower']
                current_price = latest_data['Close']
                
                if pd.notna(bb_upper) and pd.notna(bb_lower):
                    if current_price > bb_upper:
                        bb_signal = "Above upper band (overbought)"
                    elif current_price < bb_lower:
                        bb_signal = "Below lower band (oversold)"
                    else:
                        bb_signal = "Within bands (normal)"
                    
                    summary['bollinger_bands_analysis'] = {
                        'position': bb_signal,
                        'upper': bb_upper,
                        'lower': bb_lower
                    }
            
            # Stochastic analysis
            if 'Stoch_K' in latest_data and 'Stoch_D' in latest_data:
                stoch_k = latest_data['Stoch_K']
                stoch_d = latest_data['Stoch_D']
                
                if pd.notna(stoch_k) and pd.notna(stoch_d):
                    if stoch_k > 80:
                        stoch_signal = "Overbought"
                    elif stoch_k < 20:
                        stoch_signal = "Oversold"
                    else:
                        stoch_signal = "Normal"
                    
                    summary['stochastic_analysis'] = {
                        'k': stoch_k,
                        'd': stoch_d,
                        'signal': stoch_signal
                    }
            
        except Exception as e:
            summary['error'] = f"Could not generate complete analysis summary: {str(e)}"
        
        return summary
    
    def _format_output(self, data: pd.DataFrame, format_type: str) -> Any:
        """Format output according to specified format."""
        if format_type == "dataframe":
            return data
        elif format_type == "dict":
            return data.to_dict('index')
        elif format_type == "json":
            return data.to_json(orient='index', date_format='iso')
        else:
            return data


# Register the tool
@register_tool("technical_analysis")
class RegisteredTechnicalAnalysisTool(TechnicalAnalysisTool):
    pass


# Also create a function-based interface for easier use
@register_tool("calculate_technical_indicators")
def technical_analysis(data: Union[pd.DataFrame, Dict], indicators: List[str], **kwargs) -> pd.DataFrame:
    """
    Perform technical analysis on stock data.
    
    Args:
        data: Stock price data (DataFrame or dict)
        indicators: List of indicators to calculate
        **kwargs: Additional parameters
    
    Returns:
        pandas.DataFrame with original data and calculated indicators
    """
    tool = TechnicalAnalysisTool()
    result = tool.execute(
        data=data,
        indicators=indicators,
        return_format="dataframe",
        **kwargs
    )
    
    if result.success:
        return result.data
    else:
        raise Exception(result.error)