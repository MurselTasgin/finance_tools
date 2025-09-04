# finance_tools/analysis/scanner/scanner_types.py
"""
Scanner types and enums for stock scanning.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime


class ScannerType(Enum):
    """Types of stock scanners."""
    TECHNICAL_SCANNER = "technical_scanner"
    PATTERN_SCANNER = "pattern_scanner"
    BREAKOUT_SCANNER = "breakout_scanner"
    MOMENTUM_SCANNER = "momentum_scanner"
    VOLUME_SCANNER = "volume_scanner"
    MULTI_TIMEFRAME_SCANNER = "multi_timeframe_scanner"


class SignalDirection(Enum):
    """Signal directions for scanning."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class ScannerFilter:
    """Filter criteria for stock scanning."""
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_volume: Optional[float] = None
    min_market_cap: Optional[float] = None
    max_market_cap: Optional[float] = None
    sectors: Optional[List[str]] = None
    exclude_sectors: Optional[List[str]] = None
    min_volatility: Optional[float] = None
    max_volatility: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert filter to dictionary."""
        return {
            'min_price': self.min_price,
            'max_price': self.max_price,
            'min_volume': self.min_volume,
            'min_market_cap': self.min_market_cap,
            'max_market_cap': self.max_market_cap,
            'sectors': self.sectors,
            'exclude_sectors': self.exclude_sectors,
            'min_volatility': self.min_volatility,
            'max_volatility': self.max_volatility
        }


@dataclass
class ScannerCriteria:
    """Scanning criteria for different scanner types."""
    scanner_type: ScannerType
    signal_direction: SignalDirection
    min_confidence: float = 0.6
    min_strength: str = "moderate"
    timeframe: str = "1d"
    lookback_period: int = 50
    filters: ScannerFilter = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = ScannerFilter()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert criteria to dictionary."""
        return {
            'scanner_type': self.scanner_type.value,
            'signal_direction': self.signal_direction.value,
            'min_confidence': self.min_confidence,
            'min_strength': self.min_strength,
            'timeframe': self.timeframe,
            'lookback_period': self.lookback_period,
            'filters': self.filters.to_dict()
        }


@dataclass
class ScanResult:
    """Result of a stock scan."""
    symbol: str
    scanner_type: ScannerType
    signal_direction: SignalDirection
    confidence: float
    strength: str
    current_price: float
    signal_value: float
    description: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scan result to dictionary."""
        return {
            'symbol': self.symbol,
            'scanner_type': self.scanner_type.value,
            'signal_direction': self.signal_direction.value,
            'confidence': self.confidence,
            'strength': self.strength,
            'current_price': self.current_price,
            'signal_value': self.signal_value,
            'description': self.description,
            'timestamp': self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp),
            'metadata': self.metadata
        }


@dataclass
class ScanSummary:
    """Summary of scan results."""
    total_scanned: int
    total_matches: int
    bullish_matches: int
    bearish_matches: int
    neutral_matches: int
    scanner_type: ScannerType
    criteria: ScannerCriteria
    execution_time: float
    timestamp: datetime
    results: List[ScanResult] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
        if self.metadata is None:
            self.metadata = {}
    
    def get_top_matches(self, limit: int = 10) -> List[ScanResult]:
        """Get top matches by confidence."""
        sorted_results = sorted(self.results, key=lambda x: x.confidence, reverse=True)
        return sorted_results[:limit]
    
    def get_bullish_matches(self) -> List[ScanResult]:
        """Get all bullish matches."""
        return [r for r in self.results if r.signal_direction == SignalDirection.BULLISH]
    
    def get_bearish_matches(self) -> List[ScanResult]:
        """Get all bearish matches."""
        return [r for r in self.results if r.signal_direction == SignalDirection.BEARISH]
    
    def __len__(self) -> int:
        """Return the number of scan results."""
        return len(self.results)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scan summary to dictionary."""
        return {
            'total_scanned': self.total_scanned,
            'total_matches': self.total_matches,
            'bullish_matches': self.bullish_matches,
            'bearish_matches': self.bearish_matches,
            'neutral_matches': self.neutral_matches,
            'scanner_type': self.scanner_type.value,
            'criteria': self.criteria.to_dict(),
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp),
            'results': [r.to_dict() for r in self.results],
            'metadata': self.metadata
        } 