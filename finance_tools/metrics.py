# finance_tools/metrics.py
"""
Metrics collection module for finance-tools.

This module provides functionality for collecting and tracking
various metrics including API calls, performance, and usage statistics.
"""

import time
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
from pathlib import Path

from .config import get_config
from .logging import get_logger


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class APICall:
    """Represents an API call with timing and result information."""
    service: str
    endpoint: str
    method: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status_code: Optional[int] = None
    success: Optional[bool] = None
    error: Optional[str] = None
    response_size: Optional[int] = None


class MetricsCollector:
    """Collects and manages metrics for finance-tools."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.config = get_config()
        self.logger = get_logger("metrics")
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Metrics storage
        self._api_calls: List[APICall] = []
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        
        # Performance tracking
        self._start_time = datetime.now()
        self._operation_times: Dict[str, List[float]] = defaultdict(list)
        
        # Rate limiting tracking
        self._rate_limit_hits: Dict[str, int] = defaultdict(int)
        self._rate_limit_resets: Dict[str, datetime] = {}
        
        # Cache statistics
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Token usage tracking (for LLM calls)
        self._token_usage: Dict[str, int] = defaultdict(int)
        self._token_costs: Dict[str, float] = defaultdict(float)
    
    def record_api_call(self, service: str, endpoint: str, method: str = "GET") -> 'APICallTracker':
        """Record an API call and return a tracker for completion."""
        call = APICall(
            service=service,
            endpoint=endpoint,
            method=method,
            start_time=datetime.now()
        )
        
        with self._lock:
            self._api_calls.append(call)
        
        return APICallTracker(call, self)
    
    def complete_api_call(self, call: APICall, status_code: int, success: bool, 
                         error: Optional[str] = None, response_size: Optional[int] = None) -> None:
        """Complete an API call with results."""
        call.end_time = datetime.now()
        call.duration = (call.end_time - call.start_time).total_seconds()
        call.status_code = status_code
        call.success = success
        call.error = error
        call.response_size = response_size
        
        # Update counters
        with self._lock:
            self._counters[f"api_calls_total_{service}_{endpoint}"] += 1
            if success:
                self._counters[f"api_calls_success_{service}_{endpoint}"] += 1
            else:
                self._counters[f"api_calls_error_{service}_{endpoint}"] += 1
            
            # Record duration
            self._timers[f"api_call_duration_{service}_{endpoint}"].append(call.duration)
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            self._counters[name] += value
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric."""
        with self._lock:
            self._gauges[name] = value
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram metric."""
        with self._lock:
            self._histograms[name].append(value)
    
    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timer metric."""
        with self._lock:
            self._timers[name].append(duration)
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        with self._lock:
            self._cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        with self._lock:
            self._cache_misses += 1
    
    def record_token_usage(self, model: str, tokens: int, cost: float = 0.0) -> None:
        """Record token usage for LLM calls."""
        with self._lock:
            self._token_usage[model] += tokens
            self._token_costs[model] += cost
    
    def record_rate_limit_hit(self, service: str) -> None:
        """Record a rate limit hit."""
        with self._lock:
            self._rate_limit_hits[service] += 1
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "total": total,
            "hit_rate_percent": hit_rate
        }
    
    def get_api_stats(self, service: Optional[str] = None, 
                     endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get API call statistics."""
        with self._lock:
            calls = self._api_calls.copy()
        
        if service:
            calls = [c for c in calls if c.service == service]
        if endpoint:
            calls = [c for c in calls if c.endpoint == endpoint]
        
        if not calls:
            return {"total_calls": 0, "success_rate": 0, "avg_duration": 0}
        
        successful_calls = [c for c in calls if c.success]
        durations = [c.duration for c in calls if c.duration is not None]
        
        return {
            "total_calls": len(calls),
            "successful_calls": len(successful_calls),
            "failed_calls": len(calls) - len(successful_calls),
            "success_rate": len(successful_calls) / len(calls) * 100,
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0
        }
    
    def get_token_usage(self) -> Dict[str, Any]:
        """Get token usage statistics."""
        with self._lock:
            return {
                "total_tokens": sum(self._token_usage.values()),
                "total_cost": sum(self._token_costs.values()),
                "by_model": dict(self._token_usage),
                "costs_by_model": dict(self._token_costs)
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        uptime = datetime.now() - self._start_time
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "start_time": self._start_time.isoformat(),
            "cache_stats": self.get_cache_stats(),
            "api_stats": self.get_api_stats(),
            "token_usage": self.get_token_usage(),
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "rate_limit_hits": dict(self._rate_limit_hits)
        }
    
    def export_metrics(self, filepath: Optional[str] = None) -> None:
        """Export metrics to a JSON file."""
        if not filepath:
            filepath = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        metrics = self.get_summary()
        
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        self.logger.info(f"Metrics exported to {filepath}")
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._api_calls.clear()
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
            self._rate_limit_hits.clear()
            self._rate_limit_resets.clear()
            self._cache_hits = 0
            self._cache_misses = 0
            self._token_usage.clear()
            self._token_costs.clear()
            self._start_time = datetime.now()


class APICallTracker:
    """Context manager for tracking API calls."""
    
    def __init__(self, call: APICall, collector: MetricsCollector):
        """Initialize the tracker."""
        self.call = call
        self.collector = collector
    
    def __enter__(self):
        """Enter the context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and record the call."""
        success = exc_type is None
        error = str(exc_val) if exc_val else None
        
        self.collector.complete_api_call(
            self.call,
            status_code=200 if success else 500,
            success=success,
            error=error
        )


# Global metrics collector
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    return _metrics_collector


def record_api_call(service: str, endpoint: str, method: str = "GET") -> APICallTracker:
    """Record an API call."""
    return _metrics_collector.record_api_call(service, endpoint, method)


def increment_counter(name: str, value: int = 1) -> None:
    """Increment a counter."""
    _metrics_collector.increment_counter(name, value)


def set_gauge(name: str, value: float) -> None:
    """Set a gauge."""
    _metrics_collector.set_gauge(name, value)


def record_timer(name: str, duration: float) -> None:
    """Record a timer."""
    _metrics_collector.record_timer(name, duration)


def record_cache_hit() -> None:
    """Record a cache hit."""
    _metrics_collector.record_cache_hit()


def record_cache_miss() -> None:
    """Record a cache miss."""
    _metrics_collector.record_cache_miss()


def record_token_usage(model: str, tokens: int, cost: float = 0.0) -> None:
    """Record token usage."""
    _metrics_collector.record_token_usage(model, tokens, cost) 