# finance_tools/analysis/config.py
"""
Configuration module for technical analysis parameters and settings.

This module provides centralized configuration management for all
technical analysis indicators and parameters.
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class IndicatorCategory(Enum):
    """Categories for technical indicators."""
    MOVING_AVERAGE = "moving_average"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    TREND = "trend"
    VOLUME = "volume"
    SUPPORT_RESISTANCE = "support_resistance"


@dataclass
class IndicatorConfig:
    """Configuration for a single technical indicator."""
    name: str
    category: IndicatorCategory
    default_period: int
    min_period: int = 1
    max_period: int = 500
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class AnalysisConfig:
    """Main configuration class for technical analysis."""
    
    # Data validation settings
    min_data_points: int = 30
    validate_data: bool = True
    handle_missing_data: str = "drop"  # drop, forward_fill, backward_fill
    
    # Default periods for indicators
    default_ema_periods: List[int] = field(default_factory=lambda: [12, 26, 50, 200])
    default_sma_periods: List[int] = field(default_factory=lambda: [20, 50, 200])
    default_rsi_period: int = 14
    default_macd_fast: int = 12
    default_macd_slow: int = 26
    default_macd_signal: int = 9
    default_bollinger_period: int = 20
    default_bollinger_std: float = 2.0
    default_stochastic_k: int = 14
    default_stochastic_d: int = 3
    default_momentum_period: int = 10
    default_roc_period: int = 10
    default_atr_period: int = 14
    default_cci_period: int = 20
    default_supertrend_period: int = 10
    default_supertrend_multiplier: float = 3.0
    default_adx_period: int = 14
    default_support_resistance_window: int = 20
    
    # Trading signal thresholds
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    cci_oversold: float = -100.0
    cci_overbought: float = 100.0
    adx_trend_threshold: float = 25.0
    
    # Logging settings
    log_level: str = "INFO"
    log_indicators: bool = True
    log_errors: bool = True
    
    # Performance settings
    enable_caching: bool = True
    cache_size: int = 1000
    parallel_processing: bool = False
    max_workers: int = 4
    
    # Output settings
    include_metadata: bool = True
    round_decimals: int = 4
    include_signals: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.min_data_points < 10:
            raise ValueError("min_data_points must be at least 10")
        
        if self.rsi_oversold >= self.rsi_overbought:
            raise ValueError("rsi_oversold must be less than rsi_overbought")
        
        if self.cci_oversold >= self.cci_overbought:
            raise ValueError("cci_oversold must be less than cci_overbought")
    
    def get_indicator_config(self, indicator_name: str) -> IndicatorConfig:
        """Get configuration for a specific indicator."""
        configs = {
            "ema": IndicatorConfig(
                name="ema",
                category=IndicatorCategory.MOVING_AVERAGE,
                default_period=20,
                description="Exponential Moving Average"
            ),
            "sma": IndicatorConfig(
                name="sma",
                category=IndicatorCategory.MOVING_AVERAGE,
                default_period=20,
                description="Simple Moving Average"
            ),
            "wma": IndicatorConfig(
                name="wma",
                category=IndicatorCategory.MOVING_AVERAGE,
                default_period=20,
                description="Weighted Moving Average"
            ),
            "rsi": IndicatorConfig(
                name="rsi",
                category=IndicatorCategory.MOMENTUM,
                default_period=self.default_rsi_period,
                description="Relative Strength Index"
            ),
            "macd": IndicatorConfig(
                name="macd",
                category=IndicatorCategory.MOMENTUM,
                default_period=self.default_macd_slow,
                parameters={
                    "fast_period": self.default_macd_fast,
                    "slow_period": self.default_macd_slow,
                    "signal_period": self.default_macd_signal
                },
                description="Moving Average Convergence Divergence"
            ),
            "bollinger_bands": IndicatorConfig(
                name="bollinger_bands",
                category=IndicatorCategory.VOLATILITY,
                default_period=self.default_bollinger_period,
                parameters={"std_dev": self.default_bollinger_std},
                description="Bollinger Bands"
            ),
            "momentum": IndicatorConfig(
                name="momentum",
                category=IndicatorCategory.MOMENTUM,
                default_period=self.default_momentum_period,
                description="Momentum Indicator"
            ),
            "supertrend": IndicatorConfig(
                name="supertrend",
                category=IndicatorCategory.TREND,
                default_period=self.default_supertrend_period,
                parameters={"multiplier": self.default_supertrend_multiplier},
                description="Supertrend Indicator"
            ),
            "atr": IndicatorConfig(
                name="atr",
                category=IndicatorCategory.VOLATILITY,
                default_period=self.default_atr_period,
                description="Average True Range"
            ),
            "stochastic": IndicatorConfig(
                name="stochastic",
                category=IndicatorCategory.MOMENTUM,
                default_period=self.default_stochastic_k,
                parameters={
                    "k_period": self.default_stochastic_k,
                    "d_period": self.default_stochastic_d
                },
                description="Stochastic Oscillator"
            ),
            "roc": IndicatorConfig(
                name="roc",
                category=IndicatorCategory.MOMENTUM,
                default_period=self.default_roc_period,
                description="Rate of Change"
            ),
            "cci": IndicatorConfig(
                name="cci",
                category=IndicatorCategory.MOMENTUM,
                default_period=self.default_cci_period,
                description="Commodity Channel Index"
            ),
            "adx": IndicatorConfig(
                name="adx",
                category=IndicatorCategory.TREND,
                default_period=self.default_adx_period,
                description="Average Directional Index"
            ),
            "obv": IndicatorConfig(
                name="obv",
                category=IndicatorCategory.VOLUME,
                default_period=1,
                description="On-Balance Volume"
            ),
            "vwap": IndicatorConfig(
                name="vwap",
                category=IndicatorCategory.VOLUME,
                default_period=1,
                description="Volume Weighted Average Price"
            ),
            "support_resistance": IndicatorConfig(
                name="support_resistance",
                category=IndicatorCategory.SUPPORT_RESISTANCE,
                default_period=self.default_support_resistance_window,
                description="Support and Resistance Levels"
            )
        }
        
        return configs.get(indicator_name, IndicatorConfig(
            name=indicator_name,
            category=IndicatorCategory.MOMENTUM,
            default_period=20,
            description="Unknown indicator"
        ))
    
    def get_all_indicators(self) -> List[str]:
        """Get list of all available indicators."""
        return [
            "ema", "sma", "wma", "rsi", "macd", "bollinger_bands",
            "momentum", "supertrend", "atr", "stochastic", "roc",
            "cci", "adx", "obv", "vwap", "support_resistance"
        ]
    
    def get_indicators_by_category(self, category: IndicatorCategory) -> List[str]:
        """Get indicators by category."""
        indicators = self.get_all_indicators()
        return [
            indicator for indicator in indicators
            if self.get_indicator_config(indicator).category == category
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "min_data_points": self.min_data_points,
            "validate_data": self.validate_data,
            "handle_missing_data": self.handle_missing_data,
            "default_ema_periods": self.default_ema_periods,
            "default_sma_periods": self.default_sma_periods,
            "default_rsi_period": self.default_rsi_period,
            "default_macd_fast": self.default_macd_fast,
            "default_macd_slow": self.default_macd_slow,
            "default_macd_signal": self.default_macd_signal,
            "default_bollinger_period": self.default_bollinger_period,
            "default_bollinger_std": self.default_bollinger_std,
            "default_stochastic_k": self.default_stochastic_k,
            "default_stochastic_d": self.default_stochastic_d,
            "default_momentum_period": self.default_momentum_period,
            "default_roc_period": self.default_roc_period,
            "default_atr_period": self.default_atr_period,
            "default_cci_period": self.default_cci_period,
            "default_supertrend_period": self.default_supertrend_period,
            "default_supertrend_multiplier": self.default_supertrend_multiplier,
            "default_adx_period": self.default_adx_period,
            "default_support_resistance_window": self.default_support_resistance_window,
            "rsi_oversold": self.rsi_oversold,
            "rsi_overbought": self.rsi_overbought,
            "cci_oversold": self.cci_oversold,
            "cci_overbought": self.cci_overbought,
            "adx_trend_threshold": self.adx_trend_threshold,
            "log_level": self.log_level,
            "log_indicators": self.log_indicators,
            "log_errors": self.log_errors,
            "enable_caching": self.enable_caching,
            "cache_size": self.cache_size,
            "parallel_processing": self.parallel_processing,
            "max_workers": self.max_workers,
            "include_metadata": self.include_metadata,
            "round_decimals": self.round_decimals,
            "include_signals": self.include_signals
        }


# Default configuration instance
DEFAULT_CONFIG = AnalysisConfig()


def load_config_from_env() -> AnalysisConfig:
    """Load configuration from environment variables."""
    config = AnalysisConfig()
    
    # Load from environment variables if they exist
    if os.getenv("ANALYSIS_MIN_DATA_POINTS"):
        config.min_data_points = int(os.getenv("ANALYSIS_MIN_DATA_POINTS"))
    
    if os.getenv("ANALYSIS_VALIDATE_DATA"):
        config.validate_data = os.getenv("ANALYSIS_VALIDATE_DATA").lower() == "true"
    
    if os.getenv("ANALYSIS_LOG_LEVEL"):
        config.log_level = os.getenv("ANALYSIS_LOG_LEVEL")
    
    if os.getenv("ANALYSIS_ENABLE_CACHING"):
        config.enable_caching = os.getenv("ANALYSIS_ENABLE_CACHING").lower() == "true"
    
    if os.getenv("ANALYSIS_PARALLEL_PROCESSING"):
        config.parallel_processing = os.getenv("ANALYSIS_PARALLEL_PROCESSING").lower() == "true"
    
    return config


def get_config() -> AnalysisConfig:
    """Get the current configuration."""
    return load_config_from_env() 