"""Metrics collection and aggregation system."""

import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from collections import defaultdict, deque
from dataclasses import dataclass, field
import threading
import json

from src.config.settings import ConfigManager


@dataclass
class Metric:
    """Individual metric data point."""
    name: str
    value: Union[int, float]
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: str = "gauge"  # gauge, counter, histogram, timer


class MetricsCollector:
    """Collects and aggregates application metrics."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.enabled = config.get_monitoring_config()["metrics_enabled"]
        
        # Thread-safe storage for metrics
        self._lock = threading.RLock()
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        
        # Aggregated statistics
        self._stats_cache: Dict[str, Dict[str, Any]] = {}
        self._last_stats_update = datetime.utcnow()
        self._stats_cache_ttl = timedelta(seconds=30)
        
        if self.enabled:
            self.logger.info("Metrics collection enabled")
        else:
            self.logger.info("Metrics collection disabled")
    
    def record_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Record a counter metric (cumulative value)."""
        if not self.enabled:
            return
        
        with self._lock:
            key = self._get_metric_key(name, tags)
            self._counters[key] += value
            
            metric = Metric(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                metric_type="counter"
            )
            self._metrics[key].append(metric)
    
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a gauge metric (current value)."""
        if not self.enabled:
            return
        
        with self._lock:
            key = self._get_metric_key(name, tags)
            self._gauges[key] = value
            
            metric = Metric(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                metric_type="gauge"
            )
            self._metrics[key].append(metric)
    
    def record_timer(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer metric (duration measurement)."""
        if not self.enabled:
            return
        
        with self._lock:
            key = self._get_metric_key(name, tags)
            self._timers[key].append(duration_ms)
            
            # Keep only recent timer values
            if len(self._timers[key]) > 1000:
                self._timers[key] = self._timers[key][-1000:]
            
            metric = Metric(
                name=name,
                value=duration_ms,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                metric_type="timer"
            )
            self._metrics[key].append(metric)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram metric (distribution of values)."""
        if not self.enabled:
            return
        
        # For now, treat histograms like timers
        self.record_timer(name, value, tags)
    
    def increment(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Increment a counter by 1."""
        self.record_counter(name, 1.0, tags)
    
    def decrement(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Decrement a counter by 1."""
        self.record_counter(name, -1.0, tags)
    
    def time_function(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Decorator to time function execution."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    self.record_timer(name, duration_ms, tags)
            return wrapper
        return decorator
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all collected metrics."""
        if not self.enabled:
            return {"enabled": False}
        
        # Check if we need to update stats cache
        now = datetime.utcnow()
        if now - self._last_stats_update > self._stats_cache_ttl:
            self._update_stats_cache()
            self._last_stats_update = now
        
        with self._lock:
            return {
                "enabled": True,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timers": self._stats_cache.get("timers", {}),
                "total_metrics": sum(len(metrics) for metrics in self._metrics.values())
            }
    
    def get_api_metrics(self) -> Dict[str, Any]:
        """Get API-specific metrics."""
        if not self.enabled:
            return {"enabled": False}
        
        api_metrics = {}
        
        with self._lock:
            for key, value in self._counters.items():
                if "api_request" in key:
                    api_metrics[key] = value
        
        return {
            "enabled": True,
            "request_counts": api_metrics,
            "response_times": self._get_timer_stats_for_prefix("api_response_time")
        }
    
    def get_data_processing_metrics(self) -> Dict[str, Any]:
        """Get data processing metrics."""
        if not self.enabled:
            return {"enabled": False}
        
        processing_metrics = {}
        
        with self._lock:
            for key, value in self._counters.items():
                if "data_processing" in key:
                    processing_metrics[key] = value
        
        return {
            "enabled": True,
            "processing_counts": processing_metrics,
            "processing_times": self._get_timer_stats_for_prefix("data_processing_time")
        }
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache-specific metrics."""
        if not self.enabled:
            return {"enabled": False}
        
        cache_metrics = {}
        
        with self._lock:
            for key, value in self._counters.items():
                if "cache" in key:
                    cache_metrics[key] = value
        
        return {
            "enabled": True,
            "cache_operations": cache_metrics,
            "cache_times": self._get_timer_stats_for_prefix("cache_time")
        }
    
    def reset_metrics(self):
        """Reset all collected metrics."""
        if not self.enabled:
            return
        
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._gauges.clear()
            self._timers.clear()
            self._stats_cache.clear()
        
        self.logger.info("All metrics reset")
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Export metrics in specified format."""
        if not self.enabled:
            return json.dumps({"enabled": False})
        
        if format_type == "json":
            return json.dumps(self.get_metrics_summary(), indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _get_metric_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Generate a unique key for a metric with tags."""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def _update_stats_cache(self):
        """Update cached statistics for timers."""
        timer_stats = {}
        
        for key, values in self._timers.items():
            if values:
                timer_stats[key] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "p50": self._percentile(values, 50),
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99)
                }
        
        self._stats_cache["timers"] = timer_stats
    
    def _get_timer_stats_for_prefix(self, prefix: str) -> Dict[str, Any]:
        """Get timer statistics for metrics with a specific prefix."""
        stats = {}
        
        for key, values in self._timers.items():
            if key.startswith(prefix) and values:
                stats[key] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "p95": self._percentile(values, 95)
                }
        
        return stats
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of a list of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]


# Context manager for timing operations
class TimerContext:
    """Context manager for timing operations."""
    
    def __init__(self, metrics_collector: MetricsCollector, metric_name: str, 
                 tags: Optional[Dict[str, str]] = None):
        self.metrics_collector = metrics_collector
        self.metric_name = metric_name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.metrics_collector.record_timer(self.metric_name, duration_ms, self.tags)