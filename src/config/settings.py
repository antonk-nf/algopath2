"""Configuration settings for different environments."""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from src.models.interfaces import ConfigManagerInterface


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class Settings:
    """Base configuration settings."""
    
    # Required configuration parameters for validation
    REQUIRED_CONFIGS: List[str] = []
    
    def __init__(self):
        """Initialize settings with validation."""
        self._load_settings()
        self._validate_required_configs()
    
    def _load_settings(self):
        """Load configuration from environment variables."""
        # Data paths
        self.DATA_ROOT_PATH: str = os.getenv("DATA_ROOT_PATH", ".")
        self.CACHE_DIR: str = os.getenv("CACHE_DIR", ".cache")
        self.LEETCODE_METADATA_PATH: Optional[str] = os.getenv("LEETCODE_METADATA_PATH")
        
        # API settings
        self.API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT: int = self._get_int_env("API_PORT", 8000)
        self.API_WORKERS: int = self._get_int_env("API_WORKERS", 1)
        self.API_TITLE: str = os.getenv("API_TITLE", "LeetCode Analytics API")
        self.API_VERSION: str = os.getenv("API_VERSION", "1.0.0")
        self.API_DESCRIPTION: str = os.getenv("API_DESCRIPTION", "Analytics API for LeetCode interview data")
        
        # Database settings (optional)
        self.DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
        self.DATABASE_ENABLED: bool = self._get_bool_env("DATABASE_ENABLED", False)
        self.DATABASE_POOL_SIZE: int = self._get_int_env("DATABASE_POOL_SIZE", 5)
        self.DATABASE_MAX_OVERFLOW: int = self._get_int_env("DATABASE_MAX_OVERFLOW", 10)
        
        # Cache settings
        self.CACHE_ENABLED: bool = self._get_bool_env("CACHE_ENABLED", True)
        self.CACHE_TTL_HOURS: int = self._get_int_env("CACHE_TTL_HOURS", 24)
        self.CACHE_MAX_SIZE_MB: int = self._get_int_env("CACHE_MAX_SIZE_MB", 1024)
        
        # Processing settings
        self.PARALLEL_WORKERS: int = self._get_int_env("PARALLEL_WORKERS", 4)
        self.CHUNK_SIZE: int = self._get_int_env("CHUNK_SIZE", 10000)
        self.MAX_MEMORY_MB: int = self._get_int_env("MAX_MEMORY_MB", 2048)
        
        # Logging settings
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
        self.LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
        self.LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
        self.LOG_MAX_SIZE_MB: int = self._get_int_env("LOG_MAX_SIZE_MB", 100)
        self.LOG_BACKUP_COUNT: int = self._get_int_env("LOG_BACKUP_COUNT", 5)
        
        # Security settings
        self.CORS_ORIGINS: List[str] = self._get_list_env("CORS_ORIGINS", ["*"])
        self.API_KEY: Optional[str] = os.getenv("API_KEY")
        self.RATE_LIMIT_PER_MINUTE: int = self._get_int_env("RATE_LIMIT_PER_MINUTE", 100)
        
        # Monitoring settings
        self.METRICS_ENABLED: bool = self._get_bool_env("METRICS_ENABLED", True)
        self.HEALTH_CHECK_INTERVAL: int = self._get_int_env("HEALTH_CHECK_INTERVAL", 30)
        
        # Debug mode (derived from environment and log level)
        self.DEBUG: bool = self._get_bool_env("DEBUG", self.LOG_LEVEL == "DEBUG")
    
    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer environment variable with validation."""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            raise ConfigValidationError(f"Invalid integer value for {key}: {os.getenv(key)}")
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean environment variable with validation."""
        value = os.getenv(key, str(default)).lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        else:
            raise ConfigValidationError(f"Invalid boolean value for {key}: {os.getenv(key)}")
    
    def _get_list_env(self, key: str, default: List[str]) -> List[str]:
        """Get list environment variable (comma-separated)."""
        value = os.getenv(key)
        if value is None:
            return default
        return [item.strip() for item in value.split(",") if item.strip()]
    
    def _validate_required_configs(self):
        """Validate that all required configuration parameters are set."""
        missing_configs = []
        for config_key in self.REQUIRED_CONFIGS:
            if not hasattr(self, config_key) or getattr(self, config_key) is None:
                missing_configs.append(config_key)
        
        if missing_configs:
            raise ConfigValidationError(
                f"Missing required configuration parameters: {', '.join(missing_configs)}"
            )
    
    def validate_paths(self):
        """Validate that required paths exist and are accessible."""
        data_path = Path(self.DATA_ROOT_PATH)
        if not data_path.exists():
            raise ConfigValidationError(f"Data root path does not exist: {self.DATA_ROOT_PATH}")
        
        if not data_path.is_dir():
            raise ConfigValidationError(f"Data root path is not a directory: {self.DATA_ROOT_PATH}")
        
        # Ensure cache directory can be created
        try:
            Path(self.CACHE_DIR).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ConfigValidationError(f"Cannot create cache directory {self.CACHE_DIR}: {e}")
    
    def validate_log_level(self):
        """Validate log level setting."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.LOG_LEVEL not in valid_levels:
            raise ConfigValidationError(
                f"Invalid log level '{self.LOG_LEVEL}'. Valid levels: {', '.join(valid_levels)}"
            )


class DevelopmentSettings(Settings):
    """Development environment settings."""
    
    def _load_settings(self):
        """Load development-specific settings."""
        super()._load_settings()
        self.API_HOST = "127.0.0.1"
        self.LOG_LEVEL = "DEBUG"
        self.DATABASE_ENABLED = False
        self.METRICS_ENABLED = True
        self.RATE_LIMIT_PER_MINUTE = 1000  # Higher limit for development
        self.DEBUG = True  # Enable debug mode in development


class ProductionSettings(Settings):
    """Production environment settings."""
    
    # Required configs for production
    REQUIRED_CONFIGS = ["DATA_ROOT_PATH"]
    
    def _load_settings(self):
        """Load production-specific settings."""
        super()._load_settings()
        self.API_WORKERS = self._get_int_env("API_WORKERS", 4)
        self.LOG_LEVEL = "INFO"
        # Only enable database if URL is provided
        self.DATABASE_ENABLED = bool(self.DATABASE_URL) if self.DATABASE_URL else self._get_bool_env("DATABASE_ENABLED", False)
        self.METRICS_ENABLED = True
        self.DEBUG = False  # Disable debug mode in production
        
        # Production-specific validations
        if self.DATABASE_ENABLED and not self.DATABASE_URL:
            raise ConfigValidationError("DATABASE_URL is required when DATABASE_ENABLED is true")


class TestSettings(Settings):
    """Test environment settings."""
    
    def _load_settings(self):
        """Load test-specific settings."""
        super()._load_settings()
        self.DATA_ROOT_PATH = "tests/fixtures"
        self.CACHE_DIR = ".test_cache"
        self.DATABASE_ENABLED = False
        self.LOG_LEVEL = "WARNING"
        self.METRICS_ENABLED = False
        self.PARALLEL_WORKERS = 1  # Single-threaded for predictable tests
        self.DEBUG = False  # Disable debug mode in tests


class ConfigManager(ConfigManagerInterface):
    """Configuration manager implementation."""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.settings = self._get_settings()
        self._validate_configuration()
    
    def _get_settings(self) -> Settings:
        """Get settings based on environment."""
        try:
            if self.environment == "production":
                return ProductionSettings()
            elif self.environment == "test":
                return TestSettings()
            else:
                return DevelopmentSettings()
        except Exception as e:
            raise ConfigValidationError(f"Failed to load {self.environment} settings: {e}")
    
    def _validate_configuration(self):
        """Validate the complete configuration."""
        try:
            # Validate paths
            self.settings.validate_paths()
            
            # Validate log level
            self.settings.validate_log_level()
            
            # Validate numeric ranges
            self._validate_numeric_ranges()
            
            # Environment-specific validations
            if self.environment == "production":
                self._validate_production_config()
                
        except Exception as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}")
    
    def _validate_numeric_ranges(self):
        """Validate numeric configuration values are within acceptable ranges."""
        if self.settings.API_PORT < 1 or self.settings.API_PORT > 65535:
            raise ConfigValidationError(f"API_PORT must be between 1 and 65535, got {self.settings.API_PORT}")
        
        if self.settings.API_WORKERS < 1:
            raise ConfigValidationError(f"API_WORKERS must be at least 1, got {self.settings.API_WORKERS}")
        
        if self.settings.PARALLEL_WORKERS < 1:
            raise ConfigValidationError(f"PARALLEL_WORKERS must be at least 1, got {self.settings.PARALLEL_WORKERS}")
        
        if self.settings.CHUNK_SIZE < 1:
            raise ConfigValidationError(f"CHUNK_SIZE must be at least 1, got {self.settings.CHUNK_SIZE}")
        
        if self.settings.CACHE_TTL_HOURS < 1:
            raise ConfigValidationError(f"CACHE_TTL_HOURS must be at least 1, got {self.settings.CACHE_TTL_HOURS}")
    
    def _validate_production_config(self):
        """Additional validations for production environment."""
        if self.settings.LOG_LEVEL == "DEBUG":
            logging.warning("DEBUG log level is not recommended for production")
        
        if self.settings.API_HOST == "127.0.0.1":
            logging.warning("API_HOST is set to localhost in production environment")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return getattr(self.settings, key, default)
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            "url": self.settings.DATABASE_URL,
            "enabled": self.settings.DATABASE_ENABLED,
            "pool_size": self.settings.DATABASE_POOL_SIZE,
            "max_overflow": self.settings.DATABASE_MAX_OVERFLOW,
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration."""
        return {
            "enabled": self.settings.CACHE_ENABLED,
            "directory": self.settings.CACHE_DIR,
            "ttl_hours": self.settings.CACHE_TTL_HOURS,
            "max_size_mb": self.settings.CACHE_MAX_SIZE_MB,
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        return {
            "host": self.settings.API_HOST,
            "port": self.settings.API_PORT,
            "workers": self.settings.API_WORKERS,
            "title": self.settings.API_TITLE,
            "version": self.settings.API_VERSION,
            "description": self.settings.API_DESCRIPTION,
            "cors_origins": self.settings.CORS_ORIGINS,
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            "level": self.settings.LOG_LEVEL,
            "format": self.settings.LOG_FORMAT,
            "file": self.settings.LOG_FILE,
            "max_size_mb": self.settings.LOG_MAX_SIZE_MB,
            "backup_count": self.settings.LOG_BACKUP_COUNT,
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get data processing configuration."""
        return {
            "parallel_workers": self.settings.PARALLEL_WORKERS,
            "chunk_size": self.settings.CHUNK_SIZE,
            "max_memory_mb": self.settings.MAX_MEMORY_MB,
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            "api_key": self.settings.API_KEY,
            "rate_limit_per_minute": self.settings.RATE_LIMIT_PER_MINUTE,
            "cors_origins": self.settings.CORS_ORIGINS,
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return {
            "metrics_enabled": self.settings.METRICS_ENABLED,
            "health_check_interval": self.settings.HEALTH_CHECK_INTERVAL,
        }
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        Path(self.settings.CACHE_DIR).mkdir(parents=True, exist_ok=True)
        
        # Create logs directory if log file is specified
        if self.settings.LOG_FILE:
            log_path = Path(self.settings.LOG_FILE)
            log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information for debugging."""
        return {
            "environment": self.environment,
            "config_class": self.settings.__class__.__name__,
            "data_root_path": self.settings.DATA_ROOT_PATH,
            "cache_enabled": self.settings.CACHE_ENABLED,
            "database_enabled": self.settings.DATABASE_ENABLED,
            "log_level": self.settings.LOG_LEVEL,
        }
    
    @property
    def debug(self) -> bool:
        """Get debug mode status."""
        return self.settings.DEBUG


def create_config(environment: str = None) -> ConfigManager:
    """Create and validate configuration manager."""
    try:
        return ConfigManager(environment)
    except ConfigValidationError as e:
        logging.error(f"Configuration validation failed: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during configuration setup: {e}")
        raise ConfigValidationError(f"Failed to create configuration: {e}")


def validate_config_file(config_file_path: str) -> bool:
    """Validate a configuration file (for external config files)."""
    try:
        config_path = Path(config_file_path)
        if not config_path.exists():
            raise ConfigValidationError(f"Configuration file not found: {config_file_path}")
        
        if not config_path.is_file():
            raise ConfigValidationError(f"Configuration path is not a file: {config_file_path}")
        
        # Additional validation logic for config files can be added here
        return True
    except Exception as e:
        logging.error(f"Configuration file validation failed: {e}")
        return False


# Global config instance - will be created when first imported
config = create_config()
