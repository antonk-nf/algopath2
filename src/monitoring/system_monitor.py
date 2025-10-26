"""System monitoring and resource tracking."""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import psutil
import threading
from pathlib import Path

from src.config.settings import ConfigManager
from .metrics_collector import MetricsCollector


class SystemMonitor:
    """Monitors system resources and performance."""
    
    def __init__(self, config: ConfigManager, metrics_collector: MetricsCollector):
        self.config = config
        self.metrics_collector = metrics_collector
        self.logger = logging.getLogger(__name__)
        
        self.monitoring_enabled = config.get_monitoring_config()["metrics_enabled"]
        self.monitoring_interval = 30  # seconds
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # System baseline measurements
        self.baseline_metrics: Dict[str, float] = {}
        self.startup_time = datetime.utcnow()
        
        # Resource thresholds
        self.cpu_warning_threshold = 80.0
        self.memory_warning_threshold = 80.0
        self.disk_warning_threshold = 85.0
        
        if self.monitoring_enabled:
            self._collect_baseline_metrics()
    
    def _collect_baseline_metrics(self):
        """Collect baseline system metrics at startup."""
        try:
            self.baseline_metrics = {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "boot_time": psutil.boot_time(),
                "startup_time": time.time()
            }
            
            self.logger.info("Baseline system metrics collected", extra={
                "extra_fields": {
                    "baseline_metrics": self.baseline_metrics
                }
            })
        except Exception as e:
            self.logger.error(f"Failed to collect baseline metrics: {e}")
    
    async def start_monitoring(self):
        """Start continuous system monitoring."""
        if not self.monitoring_enabled or self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.logger.info(f"Starting system monitoring with {self.monitoring_interval}s interval")
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop continuous system monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("System monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in system monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_system_metrics(self):
        """Collect current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics for data directory
            data_path = Path(self.config.get_config("DATA_ROOT_PATH"))
            disk_usage = psutil.disk_usage(str(data_path))
            
            # Cache directory metrics
            cache_path = Path(self.config.get_cache_config()["directory"])
            cache_size_bytes = sum(f.stat().st_size for f in cache_path.glob("**/*") if f.is_file()) if cache_path.exists() else 0
            
            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            # Record metrics
            self.metrics_collector.record_gauge("system.cpu.percent", cpu_percent)
            self.metrics_collector.record_gauge("system.cpu.load_1m", load_avg[0])
            self.metrics_collector.record_gauge("system.cpu.load_5m", load_avg[1])
            self.metrics_collector.record_gauge("system.cpu.load_15m", load_avg[2])
            
            self.metrics_collector.record_gauge("system.memory.percent", memory.percent)
            self.metrics_collector.record_gauge("system.memory.available_gb", memory.available / (1024**3))
            self.metrics_collector.record_gauge("system.memory.used_gb", memory.used / (1024**3))
            
            self.metrics_collector.record_gauge("system.swap.percent", swap.percent)
            self.metrics_collector.record_gauge("system.swap.used_gb", swap.used / (1024**3))
            
            self.metrics_collector.record_gauge("system.disk.percent", (disk_usage.used / disk_usage.total) * 100)
            self.metrics_collector.record_gauge("system.disk.free_gb", disk_usage.free / (1024**3))
            self.metrics_collector.record_gauge("system.disk.used_gb", disk_usage.used / (1024**3))
            
            self.metrics_collector.record_gauge("system.cache.size_mb", cache_size_bytes / (1024**2))
            
            self.metrics_collector.record_gauge("process.cpu.percent", process_cpu)
            self.metrics_collector.record_gauge("process.memory.rss_mb", process_memory.rss / (1024**2))
            self.metrics_collector.record_gauge("process.memory.vms_mb", process_memory.vms / (1024**2))
            
            # Check for warnings
            await self._check_resource_warnings(cpu_percent, memory.percent, (disk_usage.used / disk_usage.total) * 100)
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
    
    async def _check_resource_warnings(self, cpu_percent: float, memory_percent: float, disk_percent: float):
        """Check for resource usage warnings."""
        warnings = []
        
        if cpu_percent > self.cpu_warning_threshold:
            warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
            self.metrics_collector.increment("system.warnings.cpu_high")
        
        if memory_percent > self.memory_warning_threshold:
            warnings.append(f"High memory usage: {memory_percent:.1f}%")
            self.metrics_collector.increment("system.warnings.memory_high")
        
        if disk_percent > self.disk_warning_threshold:
            warnings.append(f"High disk usage: {disk_percent:.1f}%")
            self.metrics_collector.increment("system.warnings.disk_high")
        
        if warnings:
            self.logger.warning("Resource usage warnings", extra={
                "extra_fields": {
                    "warnings": warnings,
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent
                }
            })
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get current system information."""
        try:
            # Current metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            # Data directory info
            data_path = Path(self.config.get_config("DATA_ROOT_PATH"))
            disk_usage = psutil.disk_usage(str(data_path))
            
            # Process info
            process = psutil.Process()
            process_info = {
                "pid": process.pid,
                "create_time": process.create_time(),
                "cpu_percent": process.cpu_percent(),
                "memory_info": {
                    "rss_mb": process.memory_info().rss / (1024**2),
                    "vms_mb": process.memory_info().vms / (1024**2)
                },
                "num_threads": process.num_threads()
            }
            
            # Uptime
            uptime_seconds = (datetime.utcnow() - self.startup_time).total_seconds()
            
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "uptime_seconds": uptime_seconds,
                "system": {
                    "cpu": {
                        "percent": cpu_percent,
                        "count": psutil.cpu_count(),
                        "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                    },
                    "memory": {
                        "total_gb": memory.total / (1024**3),
                        "available_gb": memory.available / (1024**3),
                        "percent": memory.percent
                    },
                    "disk": {
                        "total_gb": disk_usage.total / (1024**3),
                        "free_gb": disk_usage.free / (1024**3),
                        "percent": (disk_usage.used / disk_usage.total) * 100
                    }
                },
                "process": process_info,
                "baseline": self.baseline_metrics
            }
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary since startup."""
        try:
            uptime = datetime.utcnow() - self.startup_time
            
            # Get current resource usage
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            # Calculate averages (simplified - in production you'd want proper time-series data)
            performance_summary = {
                "uptime": {
                    "seconds": uptime.total_seconds(),
                    "formatted": str(uptime)
                },
                "current_usage": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3)
                },
                "warnings": {
                    "cpu_high_count": self.metrics_collector._counters.get("system.warnings.cpu_high", 0),
                    "memory_high_count": self.metrics_collector._counters.get("system.warnings.memory_high", 0),
                    "disk_high_count": self.metrics_collector._counters.get("system.warnings.disk_high", 0)
                }
            }
            
            return performance_summary
        except Exception as e:
            self.logger.error(f"Failed to get performance summary: {e}")
            return {"error": str(e)}
    
    def log_startup_info(self):
        """Log system information at startup."""
        system_info = self.get_system_info()
        
        self.logger.info("System monitoring initialized", extra={
            "extra_fields": {
                "system_info": system_info,
                "monitoring_enabled": self.monitoring_enabled,
                "monitoring_interval": self.monitoring_interval
            }
        })