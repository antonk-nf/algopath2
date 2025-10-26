"""Health monitoring system for the application."""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import psutil
import pandas as pd

from src.config.settings import ConfigManager


class HealthCheck:
    """Individual health check implementation."""
    
    def __init__(self, name: str, check_func, timeout: float = 5.0):
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
        self.last_check_time: Optional[datetime] = None
        self.last_result: Optional[Dict[str, Any]] = None
        self.consecutive_failures = 0
    
    async def run_check(self) -> Dict[str, Any]:
        """Run the health check with timeout."""
        start_time = time.time()
        
        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                self.check_func(), 
                timeout=self.timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            check_result = {
                "name": self.name,
                "status": "healthy" if result.get("healthy", True) else "unhealthy",
                "duration_ms": round(duration_ms, 2),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "details": result.get("details", {}),
                "message": result.get("message", "Check passed")
            }
            
            if check_result["status"] == "healthy":
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
            
            self.last_check_time = datetime.utcnow()
            self.last_result = check_result
            
            return check_result
            
        except asyncio.TimeoutError:
            self.consecutive_failures += 1
            return {
                "name": self.name,
                "status": "unhealthy",
                "duration_ms": self.timeout * 1000,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": f"Health check timed out after {self.timeout}s",
                "error": "timeout"
            }
        except Exception as e:
            self.consecutive_failures += 1
            return {
                "name": self.name,
                "status": "unhealthy",
                "duration_ms": (time.time() - start_time) * 1000,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": f"Health check failed: {str(e)}",
                "error": str(e)
            }


class HealthMonitor:
    """Health monitoring system."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.health_checks: List[HealthCheck] = []
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Register default health checks
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks."""
        self.register_check("system_resources", self._check_system_resources)
        self.register_check("data_directory", self._check_data_directory)
        self.register_check("cache_directory", self._check_cache_directory)
        
        # Add database check if enabled
        if self.config.get_database_config()["enabled"]:
            self.register_check("database", self._check_database)
    
    def register_check(self, name: str, check_func, timeout: float = 5.0):
        """Register a new health check."""
        health_check = HealthCheck(name, check_func, timeout)
        self.health_checks.append(health_check)
        self.logger.info(f"Registered health check: {name}")
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return aggregated results."""
        start_time = time.time()
        
        # Run all checks concurrently
        check_tasks = [check.run_check() for check in self.health_checks]
        check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Process results
        healthy_checks = []
        unhealthy_checks = []
        
        for result in check_results:
            if isinstance(result, Exception):
                unhealthy_checks.append({
                    "name": "unknown",
                    "status": "unhealthy",
                    "message": f"Check execution failed: {str(result)}",
                    "error": str(result)
                })
            elif result["status"] == "healthy":
                healthy_checks.append(result)
            else:
                unhealthy_checks.append(result)
        
        total_duration_ms = (time.time() - start_time) * 1000
        overall_status = "healthy" if len(unhealthy_checks) == 0 else "unhealthy"
        
        health_report = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "duration_ms": round(total_duration_ms, 2),
            "checks": {
                "total": len(self.health_checks),
                "healthy": len(healthy_checks),
                "unhealthy": len(unhealthy_checks)
            },
            "details": {
                "healthy": healthy_checks,
                "unhealthy": unhealthy_checks
            }
        }
        
        # Log health status
        if overall_status == "healthy":
            self.logger.info("All health checks passed", extra={
                "extra_fields": {
                    "health_summary": health_report["checks"],
                    "duration_ms": total_duration_ms
                }
            })
        else:
            self.logger.warning("Some health checks failed", extra={
                "extra_fields": {
                    "health_summary": health_report["checks"],
                    "failed_checks": [check["name"] for check in unhealthy_checks]
                }
            })
        
        return health_report
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        interval = self.config.get_monitoring_config()["health_check_interval"]
        
        self.logger.info(f"Starting health monitoring with {interval}s interval")
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
    
    async def stop_monitoring(self):
        """Stop continuous health monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self, interval: int):
        """Continuous monitoring loop."""
        while self.is_monitoring:
            try:
                await self.run_all_checks()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(interval)
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage for data directory
            data_path = Path(self.config.get_config("DATA_ROOT_PATH"))
            disk_usage = psutil.disk_usage(str(data_path))
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Check thresholds
            cpu_threshold = 90.0
            memory_threshold = 90.0
            disk_threshold = 90.0
            
            issues = []
            if cpu_percent > cpu_threshold:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory_percent > memory_threshold:
                issues.append(f"High memory usage: {memory_percent:.1f}%")
            if disk_percent > disk_threshold:
                issues.append(f"High disk usage: {disk_percent:.1f}%")
            
            return {
                "healthy": len(issues) == 0,
                "message": "System resources OK" if len(issues) == 0 else f"Resource issues: {', '.join(issues)}",
                "details": {
                    "cpu_percent": round(cpu_percent, 1),
                    "memory_percent": round(memory_percent, 1),
                    "disk_percent": round(disk_percent, 1),
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_free_gb": round(disk_usage.free / (1024**3), 2)
                }
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Failed to check system resources: {str(e)}"
            }
    
    async def _check_data_directory(self) -> Dict[str, Any]:
        """Check data directory accessibility."""
        try:
            data_path = Path(self.config.get_config("DATA_ROOT_PATH"))
            
            if not data_path.exists():
                return {
                    "healthy": False,
                    "message": f"Data directory does not exist: {data_path}"
                }
            
            if not data_path.is_dir():
                return {
                    "healthy": False,
                    "message": f"Data path is not a directory: {data_path}"
                }
            
            # Check if we can read the directory
            try:
                list(data_path.iterdir())
            except PermissionError:
                return {
                    "healthy": False,
                    "message": f"No read permission for data directory: {data_path}"
                }
            
            # Count CSV files
            csv_count = len(list(data_path.glob("**/*.csv")))
            
            return {
                "healthy": True,
                "message": "Data directory accessible",
                "details": {
                    "path": str(data_path),
                    "csv_files_found": csv_count
                }
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Failed to check data directory: {str(e)}"
            }
    
    async def _check_cache_directory(self) -> Dict[str, Any]:
        """Check cache directory accessibility."""
        try:
            cache_config = self.config.get_cache_config()
            cache_path = Path(cache_config["directory"])
            
            # Ensure cache directory exists
            cache_path.mkdir(parents=True, exist_ok=True)
            
            # Test write access
            test_file = cache_path / ".health_check"
            try:
                test_file.write_text("health_check")
                test_file.unlink()
            except Exception:
                return {
                    "healthy": False,
                    "message": f"No write permission for cache directory: {cache_path}"
                }
            
            # Check cache size
            cache_size_mb = sum(f.stat().st_size for f in cache_path.glob("**/*") if f.is_file()) / (1024**2)
            max_size_mb = cache_config["max_size_mb"]
            
            return {
                "healthy": True,
                "message": "Cache directory accessible",
                "details": {
                    "path": str(cache_path),
                    "size_mb": round(cache_size_mb, 2),
                    "max_size_mb": max_size_mb,
                    "usage_percent": round((cache_size_mb / max_size_mb) * 100, 1) if max_size_mb > 0 else 0
                }
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Failed to check cache directory: {str(e)}"
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity (if enabled)."""
        try:
            # This would need to be implemented based on the actual database manager
            # For now, return a placeholder
            return {
                "healthy": True,
                "message": "Database check not implemented",
                "details": {
                    "note": "Database connectivity check needs implementation"
                }
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Database check failed: {str(e)}"
            }