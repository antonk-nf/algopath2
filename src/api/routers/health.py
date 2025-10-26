"""Health check and system monitoring endpoints."""

import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
import pandas as pd

from ..dependencies import (
    get_dataset_manager,
    get_analytics_engine,
    get_correlation_id
)
from ..models import HealthResponse
from ..exceptions import DataProcessingError
from ...config.settings import config
from ...services.dataset_manager import DatasetManager
from ...analytics.analytics_engine import AnalyticsEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any])
async def health_check(
    # Dependencies
    dataset_manager: DatasetManager = Depends(get_dataset_manager),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Comprehensive health check endpoint.
    
    Returns system status, data freshness, cache status, and performance metrics.
    """
    try:
        logger.info("Performing health check", extra={"correlation_id": correlation_id})
        
        start_time = time.time()
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": config.get_config("API_VERSION", "1.0.0"),
            "environment": config.environment,
            "checks": {}
        }
        
        # System metrics
        try:
            system_metrics = _get_system_metrics()
            health_status["system_metrics"] = system_metrics
            health_status["checks"]["system_metrics"] = "pass"
        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            health_status["checks"]["system_metrics"] = "warn"
            health_status["system_metrics"] = {"error": str(e)}
        
        # Data freshness check
        try:
            data_freshness = _check_data_freshness(dataset_manager)
            health_status["data_freshness"] = data_freshness
            
            # Determine if data is stale (older than 24 hours)
            if data_freshness.get("hours_since_last_update", 0) > 24:
                health_status["checks"]["data_freshness"] = "warn"
            else:
                health_status["checks"]["data_freshness"] = "pass"
                
        except Exception as e:
            logger.warning(f"Failed to check data freshness: {e}")
            health_status["checks"]["data_freshness"] = "fail"
            health_status["data_freshness"] = {"error": str(e)}
        
        # Cache status check
        try:
            cache_status = _check_cache_status(dataset_manager)
            health_status["cache_status"] = cache_status
            health_status["checks"]["cache_status"] = "pass"
        except Exception as e:
            logger.warning(f"Failed to check cache status: {e}")
            health_status["checks"]["cache_status"] = "warn"
            health_status["cache_status"] = {"error": str(e)}
        
        # Analytics engine check
        try:
            analytics_status = _check_analytics_engine(analytics_engine)
            health_status["analytics_status"] = analytics_status
            health_status["checks"]["analytics_engine"] = "pass"
        except Exception as e:
            logger.warning(f"Failed to check analytics engine: {e}")
            health_status["checks"]["analytics_engine"] = "warn"
            health_status["analytics_status"] = {"error": str(e)}
        
        # Configuration check
        try:
            config_status = _check_configuration()
            health_status["configuration"] = config_status
            health_status["checks"]["configuration"] = "pass"
        except Exception as e:
            logger.warning(f"Failed to check configuration: {e}")
            health_status["checks"]["configuration"] = "warn"
            health_status["configuration"] = {"error": str(e)}
        
        # Overall health determination
        failed_checks = [k for k, v in health_status["checks"].items() if v == "fail"]
        warning_checks = [k for k, v in health_status["checks"].items() if v == "warn"]
        
        if failed_checks:
            health_status["status"] = "unhealthy"
        elif warning_checks:
            health_status["status"] = "degraded"
        else:
            health_status["status"] = "healthy"
        
        # Add response time
        health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        logger.info(
            f"Health check completed: {health_status['status']} ({health_status['response_time_ms']}ms)",
            extra={"correlation_id": correlation_id}
        )
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", extra={"correlation_id": correlation_id})
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "correlation_id": correlation_id
        }


@router.get("/quick", response_model=Dict[str, Any])
async def quick_health_check(correlation_id: str = Depends(get_correlation_id)):
    """
    Quick health check endpoint for load balancers.
    
    Returns minimal health status for fast response times.
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": config.get_config("API_VERSION", "1.0.0")
        }
    except Exception as e:
        logger.error(f"Quick health check failed: {str(e)}", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/data", response_model=Dict[str, Any])
async def data_health_check(
    dataset_manager: DatasetManager = Depends(get_dataset_manager),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Data-specific health check endpoint.
    
    Returns detailed information about data availability, freshness, and quality.
    """
    try:
        logger.info("Performing data health check", extra={"correlation_id": correlation_id})
        
        # Get dataset info
        root_path = config.get_config("DATA_ROOT_PATH", ".")
        dataset_info = dataset_manager.get_dataset_info(root_path)
        
        # Try to load a small sample of data
        try:
            sample_dataset = dataset_manager.get_unified_dataset(root_path)
            data_available = sample_dataset is not None and not sample_dataset.empty
            sample_size = len(sample_dataset) if data_available else 0
        except Exception as e:
            logger.warning(f"Failed to load sample dataset: {e}")
            data_available = False
            sample_size = 0
        
        data_health = {
            "data_available": data_available,
            "sample_size": sample_size,
            "source_files": dataset_info.get("source_files", {}),
            "cache_status": dataset_info.get("cache_status", {}),
            "cache_stats": dataset_info.get("cache_stats", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        # Determine health status
        if not data_available:
            data_health["status"] = "unhealthy"
            data_health["message"] = "No data available"
        elif sample_size < 100:
            data_health["status"] = "degraded"
            data_health["message"] = f"Limited data available ({sample_size} records)"
        else:
            data_health["status"] = "healthy"
            data_health["message"] = f"Data available ({sample_size} records)"
        
        logger.info(
            f"Data health check completed: {data_health['status']}",
            extra={"correlation_id": correlation_id}
        )
        
        return data_health
        
    except Exception as e:
        logger.error(f"Data health check failed: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to check data health: {str(e)}")


@router.get("/metrics", response_model=Dict[str, Any])
async def system_metrics(correlation_id: str = Depends(get_correlation_id)):
    """
    Detailed system metrics endpoint.
    
    Returns comprehensive system performance and resource utilization metrics.
    """
    try:
        logger.info("Getting system metrics", extra={"correlation_id": correlation_id})
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": _get_system_metrics(),
            "process": _get_process_metrics(),
            "application": _get_application_metrics()
        }
        
        logger.info("System metrics retrieved successfully", extra={"correlation_id": correlation_id})
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to get system metrics: {str(e)}")


def _get_system_metrics() -> Dict[str, Any]:
    """Get system-level metrics."""
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        }
    except Exception as e:
        logger.warning(f"Failed to get system metrics: {e}")
        return {"error": str(e)}


def _get_process_metrics() -> Dict[str, Any]:
    """Get current process metrics."""
    try:
        process = psutil.Process()
        
        # Memory info
        memory_info = process.memory_info()
        
        # CPU info
        cpu_percent = process.cpu_percent()
        
        # File descriptors (Unix only)
        try:
            num_fds = process.num_fds()
        except (AttributeError, psutil.AccessDenied):
            num_fds = None
        
        return {
            "pid": process.pid,
            "memory": {
                "rss": memory_info.rss,
                "vms": memory_info.vms,
                "percent": process.memory_percent()
            },
            "cpu": {
                "percent": cpu_percent,
                "times": process.cpu_times()._asdict()
            },
            "file_descriptors": num_fds,
            "threads": process.num_threads(),
            "create_time": process.create_time(),
            "status": process.status()
        }
    except Exception as e:
        logger.warning(f"Failed to get process metrics: {e}")
        return {"error": str(e)}


def _get_application_metrics() -> Dict[str, Any]:
    """Get application-specific metrics."""
    try:
        return {
            "environment": config.environment,
            "debug_mode": config.debug,
            "version": config.get_config("API_VERSION", "1.0.0"),
            "uptime_seconds": time.time() - psutil.Process().create_time(),
            "configuration": {
                "data_root_path": config.get_config("DATA_ROOT_PATH"),
                "cache_dir": config.get_config("CACHE_DIR"),
                "log_level": config.get_config("LOG_LEVEL", "INFO")
            }
        }
    except Exception as e:
        logger.warning(f"Failed to get application metrics: {e}")
        return {"error": str(e)}


def _check_data_freshness(dataset_manager: DatasetManager) -> Dict[str, Any]:
    """Check data freshness."""
    try:
        root_path = config.get_config("DATA_ROOT_PATH", ".")
        dataset_info = dataset_manager.get_dataset_info(root_path)
        
        # Get cache stats
        cache_stats = dataset_info.get("cache_stats", {})
        
        # Find the most recent cache update
        last_update = None
        for cache_type, stats in cache_stats.items():
            if isinstance(stats, dict) and "last_updated" in stats:
                cache_time = pd.to_datetime(stats["last_updated"])
                if last_update is None or cache_time > last_update:
                    last_update = cache_time
        
        if last_update:
            hours_since_update = (datetime.now() - last_update.to_pydatetime()).total_seconds() / 3600
            return {
                "last_update": last_update.isoformat(),
                "hours_since_last_update": round(hours_since_update, 2),
                "is_stale": hours_since_update > 24,
                "cache_stats": cache_stats
            }
        else:
            return {
                "last_update": None,
                "hours_since_last_update": None,
                "is_stale": True,
                "message": "No cache data found"
            }
            
    except Exception as e:
        logger.warning(f"Failed to check data freshness: {e}")
        return {"error": str(e)}


def _check_cache_status(dataset_manager: DatasetManager) -> Dict[str, Any]:
    """Check cache system status."""
    try:
        root_path = config.get_config("DATA_ROOT_PATH", ".")
        dataset_info = dataset_manager.get_dataset_info(root_path)
        
        cache_status = dataset_info.get("cache_status", {})
        cache_stats = dataset_info.get("cache_stats", {})
        
        # Count cached vs non-cached datasets
        cached_count = sum(1 for status in cache_status.values() if status.get("cached", False))
        total_count = len(cache_status)
        
        return {
            "cache_hit_rate": (cached_count / total_count) if total_count > 0 else 0,
            "cached_datasets": cached_count,
            "total_datasets": total_count,
            "cache_details": cache_status,
            "cache_statistics": cache_stats
        }
        
    except Exception as e:
        logger.warning(f"Failed to check cache status: {e}")
        return {"error": str(e)}


def _check_analytics_engine(analytics_engine: AnalyticsEngine) -> Dict[str, Any]:
    """Check analytics engine status."""
    try:
        # Test basic functionality
        test_df = pd.DataFrame({
            'title': ['Test Problem'],
            'company': ['Test Company'],
            'frequency': [1.0],
            'acceptance_rate': [0.5],
            'difficulty': ['EASY'],
            'topics': ['Array'],
            'timeframe': ['30d']
        })
        
        # Try a simple analytics operation
        summary = analytics_engine.get_analytics_summary(test_df)
        
        return {
            "status": "operational",
            "components": {
                "cross_company_analyzer": "available",
                "topic_analyzer": "available", 
                "trend_analyzer": "available",
                "difficulty_analyzer": "available"
            },
            "test_result": "passed" if summary else "failed"
        }
        
    except Exception as e:
        logger.warning(f"Analytics engine check failed: {e}")
        return {
            "status": "degraded",
            "error": str(e)
        }


def _check_configuration() -> Dict[str, Any]:
    """Check configuration status."""
    try:
        required_configs = [
            "DATA_ROOT_PATH",
            "CACHE_DIR",
            "LOG_LEVEL"
        ]
        
        config_status = {}
        missing_configs = []
        
        for config_key in required_configs:
            value = config.get_config(config_key)
            if value:
                config_status[config_key] = "configured"
            else:
                config_status[config_key] = "missing"
                missing_configs.append(config_key)
        
        return {
            "status": "valid" if not missing_configs else "incomplete",
            "missing_configurations": missing_configs,
            "configuration_status": config_status,
            "environment": config.environment,
            "debug_mode": config.debug
        }
        
    except Exception as e:
        logger.warning(f"Configuration check failed: {e}")
        return {"error": str(e)}