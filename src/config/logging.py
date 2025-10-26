"""Logging configuration and setup."""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import traceback

from .settings import ConfigManager


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        
        # Add correlation ID if present
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id
        
        # Add performance metrics if present
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        
        if hasattr(record, "memory_mb"):
            log_entry["memory_mb"] = record.memory_mb
        
        return json.dumps(log_entry, default=str)


class StandardFormatter(logging.Formatter):
    """Standard text formatter for human-readable logs."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


class PerformanceLogger:
    """Logger for performance metrics and monitoring."""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
    
    def log_request_metrics(self, endpoint: str, method: str, duration_ms: float, 
                          status_code: int, user_agent: Optional[str] = None):
        """Log API request metrics."""
        extra_fields = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "metric_type": "api_request"
        }
        
        if user_agent:
            extra_fields["user_agent"] = user_agent
        
        self.logger.info(
            f"{method} {endpoint} - {status_code} - {duration_ms:.2f}ms",
            extra={"extra_fields": extra_fields}
        )
    
    def log_data_processing_metrics(self, operation: str, records_processed: int, 
                                  duration_ms: float, memory_mb: Optional[float] = None):
        """Log data processing metrics."""
        extra_fields = {
            "operation": operation,
            "records_processed": records_processed,
            "duration_ms": duration_ms,
            "metric_type": "data_processing"
        }
        
        if memory_mb:
            extra_fields["memory_mb"] = memory_mb
        
        self.logger.info(
            f"Data processing: {operation} - {records_processed} records - {duration_ms:.2f}ms",
            extra={"extra_fields": extra_fields}
        )
    
    def log_cache_metrics(self, operation: str, cache_key: str, hit: bool, 
                         size_mb: Optional[float] = None):
        """Log cache operation metrics."""
        extra_fields = {
            "operation": operation,
            "cache_key": cache_key,
            "cache_hit": hit,
            "metric_type": "cache_operation"
        }
        
        if size_mb:
            extra_fields["size_mb"] = size_mb
        
        status = "HIT" if hit else "MISS"
        self.logger.info(
            f"Cache {operation}: {cache_key} - {status}",
            extra={"extra_fields": extra_fields}
        )
    
    def log_error_metrics(self, error_type: str, error_message: str, 
                         context: Optional[Dict[str, Any]] = None):
        """Log error metrics for monitoring."""
        extra_fields = {
            "error_type": error_type,
            "error_message": error_message,
            "metric_type": "error"
        }
        
        if context:
            extra_fields["context"] = context
        
        self.logger.error(
            f"Error: {error_type} - {error_message}",
            extra={"extra_fields": extra_fields}
        )


class CorrelationFilter(logging.Filter):
    """Filter to add correlation IDs to log records."""
    
    def __init__(self, correlation_id: Optional[str] = None):
        super().__init__()
        self.correlation_id = correlation_id
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        if self.correlation_id:
            record.correlation_id = self.correlation_id
        return True


def setup_logging(config: ConfigManager) -> None:
    """Set up logging configuration based on settings."""
    logging_config = config.get_logging_config()
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set log level
    log_level = getattr(logging, logging_config["level"])
    root_logger.setLevel(log_level)
    
    # Choose formatter based on format setting
    if logging_config["format"] == "json":
        formatter = JSONFormatter()
    else:
        formatter = StandardFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if logging_config["file"]:
        log_file_path = Path(logging_config["file"])
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler with size limits
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file_path,
            maxBytes=logging_config["max_size_mb"] * 1024 * 1024,
            backupCount=logging_config["backup_count"],
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
    
    # Set up specific loggers
    setup_application_loggers(log_level, formatter)
    
    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized", extra={
        "extra_fields": {
            "log_level": logging_config["level"],
            "log_format": logging_config["format"],
            "log_file": logging_config["file"],
            "environment": config.environment
        }
    })


def setup_application_loggers(log_level: int, formatter: logging.Formatter) -> None:
    """Set up application-specific loggers."""
    
    # Reduce verbosity of third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    
    # Set up application loggers
    app_loggers = [
        "src.services",
        "src.analytics", 
        "src.api",
        "src.config",
        "performance",
        "security"
    ]
    
    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        logger.propagate = True  # Allow propagation to root logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


def get_performance_logger() -> PerformanceLogger:
    """Get the performance logger instance."""
    return PerformanceLogger()


def add_correlation_id(logger: logging.Logger, correlation_id: str) -> None:
    """Add correlation ID filter to a logger."""
    correlation_filter = CorrelationFilter(correlation_id)
    logger.addFilter(correlation_filter)


def log_system_info(config: ConfigManager) -> None:
    """Log system information at startup."""
    logger = get_logger(__name__)
    
    system_info = {
        "environment": config.environment,
        "api_config": config.get_api_config(),
        "cache_config": config.get_cache_config(),
        "database_config": {
            "enabled": config.get_database_config()["enabled"]
        },
        "processing_config": config.get_processing_config(),
    }
    
    logger.info("System configuration loaded", extra={
        "extra_fields": {
            "system_info": system_info,
            "metric_type": "system_startup"
        }
    })