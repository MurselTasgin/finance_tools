# finance_tools/analysis/scanner/stock_scanner.py
"""
Stock scanner for identifying stocks with potential breakouts and opportunities.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import time

from .scanner_types import (
    ScannerType, ScanResult, ScannerFilter, ScannerCriteria, ScanSummary, SignalDirection
)
from ..signals import SignalCalculator
from ..patterns import PatternDetector
from ..analysis import TechnicalAnalysis

logger = logging.getLogger(__name__)


class StockScanner:
    """
    Main stock scanner for identifying trading opportunities.
    """
    
    def __init__(self):
        """Initialize the stock scanner."""
        self.signal_calculator = SignalCalculator()
        self.pattern_detector = PatternDetector()
        self.technical_analysis = TechnicalAnalysis()
    
    def scan_stocks(self, stock_data: Dict[str, pd.DataFrame], 
                   criteria: ScannerCriteria) -> ScanSummary:
        """
        Scan multiple stocks based on given criteria.
        
        Args:
            stock_data: Dictionary of symbol -> DataFrame pairs
            criteria: Scanning criteria
            
        Returns:
            ScanSummary: Summary of scan results
        """
        start_time = time.time()
        results = []
        total_scanned = len(stock_data)
        
        for symbol, data in stock_data.items():
            try:
                # Apply filters
                if not self._apply_filters(data, criteria.filters):
                    continue
                
                # Scan based on scanner type
                if criteria.scanner_type == ScannerType.TECHNICAL_SCANNER:
                    scan_result = self._scan_technical_signals(data, symbol, criteria)
                elif criteria.scanner_type == ScannerType.PATTERN_SCANNER:
                    scan_result = self._scan_patterns(data, symbol, criteria)
                elif criteria.scanner_type == ScannerType.BREAKOUT_SCANNER:
                    scan_result = self._scan_breakouts(data, symbol, criteria)
                elif criteria.scanner_type == ScannerType.MOMENTUM_SCANNER:
                    scan_result = self._scan_momentum(data, symbol, criteria)
                elif criteria.scanner_type == ScannerType.VOLUME_SCANNER:
                    scan_result = self._scan_volume_anomalies(data, symbol, criteria)
                else:
                    continue
                
                if scan_result and scan_result.confidence >= criteria.min_confidence:
                    results.append(scan_result)
                    
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue
        
        # Count matches by direction
        bullish_matches = len([r for r in results if r.signal_direction == SignalDirection.BULLISH])
        bearish_matches = len([r for r in results if r.signal_direction == SignalDirection.BEARISH])
        neutral_matches = len([r for r in results if r.signal_direction == SignalDirection.NEUTRAL])
        
        execution_time = time.time() - start_time
        
        return ScanSummary(
            total_scanned=total_scanned,
            total_matches=len(results),
            bullish_matches=bullish_matches,
            bearish_matches=bearish_matches,
            neutral_matches=neutral_matches,
            scanner_type=criteria.scanner_type,
            criteria=criteria,
            execution_time=execution_time,
            timestamp=datetime.now(),
            results=results
        )
    
    def _apply_filters(self, data: pd.DataFrame, filters: ScannerFilter) -> bool:
        """Apply filters to stock data."""
        if data.empty:
            return False
        
        current_price = data['close'].iloc[-1]
        volume = data.get('volume', pd.Series(index=data.index, dtype=float))
        avg_volume = volume.mean() if not volume.empty else 0
        
        # Price filters
        if filters.min_price and current_price < filters.min_price:
            return False
        if filters.max_price and current_price > filters.max_price:
            return False
        
        # Volume filters
        if filters.min_volume and avg_volume < filters.min_volume:
            return False
        
        # Volatility filters
        if filters.min_volatility or filters.max_volatility:
            returns = data['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)
            
            if filters.min_volatility and volatility < filters.min_volatility:
                return False
            if filters.max_volatility and volatility > filters.max_volatility:
                return False
        
        return True
    
    def _scan_technical_signals(self, data: pd.DataFrame, symbol: str, 
                              criteria: ScannerCriteria) -> Optional[ScanResult]:
        """Scan for technical signals."""
        try:
            # Calculate signals
            signals_result = self.signal_calculator.calculate_all_signals(data)
            
            # Get signals based on direction
            if criteria.signal_direction == SignalDirection.BULLISH:
                signals = signals_result.get_buy_signals()
            elif criteria.signal_direction == SignalDirection.BEARISH:
                signals = signals_result.get_sell_signals()
            else:
                signals = signals_result.signals
            
            if not signals:
                return None
            
            # Get strongest signal
            strongest_signal = signals_result.get_strongest_signal()
            if not strongest_signal:
                return None
            
            current_price = data['close'].iloc[-1]
            
            return ScanResult(
                symbol=symbol,
                scanner_type=criteria.scanner_type,
                signal_direction=criteria.signal_direction,
                confidence=strongest_signal.confidence,
                strength=strongest_signal.strength.value,
                current_price=current_price,
                signal_value=strongest_signal.value,
                description=strongest_signal.description,
                timestamp=datetime.now(),
                metadata={'signal_type': strongest_signal.signal_type.value}
            )
            
        except Exception as e:
            logger.error(f"Error scanning technical signals for {symbol}: {e}")
            return None
    
    def _scan_patterns(self, data: pd.DataFrame, symbol: str, 
                      criteria: ScannerCriteria) -> Optional[ScanResult]:
        """Scan for chart patterns."""
        try:
            # Detect patterns
            patterns_result = self.pattern_detector.detect_all_patterns(data)
            
            # Filter patterns by direction
            if criteria.signal_direction == SignalDirection.BULLISH:
                patterns = patterns_result.get_bullish_patterns()
            elif criteria.signal_direction == SignalDirection.BEARISH:
                patterns = patterns_result.get_bearish_patterns()
            else:
                patterns = patterns_result.patterns
            
            if not patterns:
                return None
            
            # Get highest confidence pattern
            best_pattern = max(patterns, key=lambda p: p.confidence)
            current_price = data['close'].iloc[-1]
            
            return ScanResult(
                symbol=symbol,
                scanner_type=criteria.scanner_type,
                signal_direction=criteria.signal_direction,
                confidence=best_pattern.confidence,
                strength=best_pattern.reliability.value,
                current_price=current_price,
                signal_value=best_pattern.breakout_price or current_price,
                description=best_pattern.description,
                timestamp=datetime.now(),
                metadata={'pattern_type': best_pattern.pattern_name}
            )
            
        except Exception as e:
            logger.error(f"Error scanning patterns for {symbol}: {e}")
            return None
    
    def _scan_breakouts(self, data: pd.DataFrame, symbol: str, 
                       criteria: ScannerCriteria) -> Optional[ScanResult]:
        """Scan for breakout patterns."""
        try:
            close_prices = data['close']
            volume = data.get('volume', pd.Series(index=data.index, dtype=float))
            
            # Calculate resistance and support levels
            recent_highs = close_prices.rolling(window=20).max()
            recent_lows = close_prices.rolling(window=20).min()
            
            current_price = close_prices.iloc[-1]
            resistance_level = recent_highs.iloc[-2]
            support_level = recent_lows.iloc[-2]
            
            # Check for breakouts
            breakout_detected = False
            signal_direction = criteria.signal_direction
            confidence = 0.0
            description = ""
            
            # Resistance breakout
            if current_price > resistance_level * 1.02:  # 2% breakout
                if criteria.signal_direction == SignalDirection.BULLISH:
                    breakout_detected = True
                    confidence = 0.8
                    description = f"Bullish breakout above resistance at ${resistance_level:.2f}"
            
            # Support breakdown
            elif current_price < support_level * 0.98:  # 2% breakdown
                if criteria.signal_direction == SignalDirection.BEARISH:
                    breakout_detected = True
                    confidence = 0.8
                    description = f"Bearish breakdown below support at ${support_level:.2f}"
            
            if not breakout_detected:
                return None
            
            # Check volume confirmation
            if not volume.empty:
                avg_volume = volume.rolling(window=20).mean().iloc[-1]
                current_volume = volume.iloc[-1]
                if current_volume > avg_volume * 1.5:  # 50% above average
                    confidence += 0.1
            
            return ScanResult(
                symbol=symbol,
                scanner_type=criteria.scanner_type,
                signal_direction=signal_direction,
                confidence=min(confidence, 1.0),
                strength="strong",
                current_price=current_price,
                signal_value=current_price,
                description=description,
                timestamp=datetime.now(),
                metadata={'breakout_type': 'resistance' if signal_direction == SignalDirection.BULLISH else 'support'}
            )
            
        except Exception as e:
            logger.error(f"Error scanning breakouts for {symbol}: {e}")
            return None
    
    def _scan_momentum(self, data: pd.DataFrame, symbol: str, 
                      criteria: ScannerCriteria) -> Optional[ScanResult]:
        """Scan for momentum signals."""
        try:
            close_prices = data['close']
            
            # Calculate momentum indicators
            indicators = self.technical_analysis.calculate_all_indicators(data)
            
            rsi = indicators.get('rsi', pd.Series())
            macd_line = indicators.get('macd_line', pd.Series())
            momentum = indicators.get('momentum', pd.Series())
            
            current_price = close_prices.iloc[-1]
            confidence = 0.0
            description = ""
            signal_direction = criteria.signal_direction
            
            # RSI momentum
            if not rsi.empty:
                rsi_current = rsi.iloc[-1]
                if criteria.signal_direction == SignalDirection.BULLISH and rsi_current < 30:
                    confidence += 0.4
                    description += f"RSI oversold ({rsi_current:.1f})"
                elif criteria.signal_direction == SignalDirection.BEARISH and rsi_current > 70:
                    confidence += 0.4
                    description += f"RSI overbought ({rsi_current:.1f})"
            
            # MACD momentum
            if not macd_line.empty:
                macd_current = macd_line.iloc[-1]
                macd_prev = macd_line.iloc[-2] if len(macd_line) > 1 else 0
                
                if criteria.signal_direction == SignalDirection.BULLISH and macd_current > macd_prev:
                    confidence += 0.3
                    description += " MACD momentum increasing"
                elif criteria.signal_direction == SignalDirection.BEARISH and macd_current < macd_prev:
                    confidence += 0.3
                    description += " MACD momentum decreasing"
            
            # Price momentum
            if not momentum.empty:
                momentum_current = momentum.iloc[-1]
                if criteria.signal_direction == SignalDirection.BULLISH and momentum_current > 0:
                    confidence += 0.3
                    description += " Positive price momentum"
                elif criteria.signal_direction == SignalDirection.BEARISH and momentum_current < 0:
                    confidence += 0.3
                    description += " Negative price momentum"
            
            if confidence < criteria.min_confidence:
                return None
            
            return ScanResult(
                symbol=symbol,
                scanner_type=criteria.scanner_type,
                signal_direction=signal_direction,
                confidence=min(confidence, 1.0),
                strength="moderate",
                current_price=current_price,
                signal_value=current_price,
                description=description.strip(),
                timestamp=datetime.now(),
                metadata={'momentum_indicators': list(indicators.keys())}
            )
            
        except Exception as e:
            logger.error(f"Error scanning momentum for {symbol}: {e}")
            return None
    
    def _scan_volume_anomalies(self, data: pd.DataFrame, symbol: str, 
                              criteria: ScannerCriteria) -> Optional[ScanResult]:
        """Scan for volume anomalies."""
        try:
            close_prices = data['close']
            volume = data.get('volume', pd.Series(index=data.index, dtype=float))
            
            if volume.empty:
                return None
            
            current_price = close_prices.iloc[-1]
            current_volume = volume.iloc[-1]
            avg_volume = volume.rolling(window=20).mean().iloc[-1]
            
            # Check for volume spike
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            if volume_ratio < 2.0:  # Need at least 2x average volume
                return None
            
            # Check price movement
            price_change = (current_price - close_prices.iloc[-2]) / close_prices.iloc[-2] if len(close_prices) > 1 else 0
            
            signal_direction = SignalDirection.NEUTRAL
            confidence = 0.6
            description = f"Volume spike ({volume_ratio:.1f}x average)"
            
            if price_change > 0.02:  # 2% price increase
                signal_direction = SignalDirection.BULLISH
                confidence += 0.2
                description += " with bullish price action"
            elif price_change < -0.02:  # 2% price decrease
                signal_direction = SignalDirection.BEARISH
                confidence += 0.2
                description += " with bearish price action"
            
            if criteria.signal_direction != SignalDirection.NEUTRAL and signal_direction != criteria.signal_direction:
                return None
            
            return ScanResult(
                symbol=symbol,
                scanner_type=criteria.scanner_type,
                signal_direction=signal_direction,
                confidence=min(confidence, 1.0),
                strength="strong",
                current_price=current_price,
                signal_value=current_price,
                description=description,
                timestamp=datetime.now(),
                metadata={'volume_ratio': volume_ratio, 'price_change': price_change}
            )
            
        except Exception as e:
            logger.error(f"Error scanning volume anomalies for {symbol}: {e}")
            return None


# Convenience functions
def scan_for_signals(stock_data: Dict[str, pd.DataFrame], 
                    signal_direction: SignalDirection = SignalDirection.BULLISH,
                    min_confidence: float = 0.6) -> ScanSummary:
    """Scan for technical signals."""
    scanner = StockScanner()
    criteria = ScannerCriteria(
        scanner_type=ScannerType.TECHNICAL_SCANNER,
        signal_direction=signal_direction,
        min_confidence=min_confidence
    )
    return scanner.scan_stocks(stock_data, criteria)


def scan_for_patterns(stock_data: Dict[str, pd.DataFrame],
                     signal_direction: SignalDirection = SignalDirection.BULLISH,
                     min_confidence: float = 0.6) -> ScanSummary:
    """Scan for chart patterns."""
    scanner = StockScanner()
    criteria = ScannerCriteria(
        scanner_type=ScannerType.PATTERN_SCANNER,
        signal_direction=signal_direction,
        min_confidence=min_confidence
    )
    return scanner.scan_stocks(stock_data, criteria)


def scan_for_breakouts(stock_data: Dict[str, pd.DataFrame],
                      signal_direction: SignalDirection = SignalDirection.BULLISH,
                      min_confidence: float = 0.6) -> ScanSummary:
    """Scan for breakout patterns."""
    scanner = StockScanner()
    criteria = ScannerCriteria(
        scanner_type=ScannerType.BREAKOUT_SCANNER,
        signal_direction=signal_direction,
        min_confidence=min_confidence
    )
    return scanner.scan_stocks(stock_data, criteria)


def scan_for_momentum(stock_data: Dict[str, pd.DataFrame],
                     signal_direction: SignalDirection = SignalDirection.BULLISH,
                     min_confidence: float = 0.6) -> ScanSummary:
    """Scan for momentum signals."""
    scanner = StockScanner()
    criteria = ScannerCriteria(
        scanner_type=ScannerType.MOMENTUM_SCANNER,
        signal_direction=signal_direction,
        min_confidence=min_confidence
    )
    return scanner.scan_stocks(stock_data, criteria)


def scan_for_volume_anomalies(stock_data: Dict[str, pd.DataFrame],
                             signal_direction: SignalDirection = SignalDirection.BULLISH,
                             min_confidence: float = 0.6) -> ScanSummary:
    """Scan for volume anomalies."""
    scanner = StockScanner()
    criteria = ScannerCriteria(
        scanner_type=ScannerType.VOLUME_SCANNER,
        signal_direction=signal_direction,
        min_confidence=min_confidence
    )
    return scanner.scan_stocks(stock_data, criteria)


def scan_multiple_timeframes(stock_data: Dict[str, pd.DataFrame],
                           criteria: ScannerCriteria,
                           timeframes: List[str] = None) -> Dict[str, ScanSummary]:
    """Scan across multiple timeframes."""
    if timeframes is None:
        timeframes = ['1d', '1w', '1m']
    
    scanner = StockScanner()
    results = {}
    
    for timeframe in timeframes:
        # Resample data to timeframe
        resampled_data = {}
        for symbol, data in stock_data.items():
            try:
                resampled = data.resample(timeframe).agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                
                if len(resampled) > 20:  # Need enough data
                    resampled_data[symbol] = resampled
            except Exception as e:
                logger.error(f"Error resampling {symbol} to {timeframe}: {e}")
        
        if resampled_data:
            results[timeframe] = scanner.scan_stocks(resampled_data, criteria)
    
    return results 