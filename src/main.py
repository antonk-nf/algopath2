"""Main entry point for the LeetCode Analytics API."""

import asyncio
import logging
import signal
import sys
import uvicorn
import time
import os
from pathlib import Path

from src.config.settings import config, ConfigValidationError
from src.config.logging import setup_logging, log_system_info
from src.monitoring import HealthMonitor, MetricsCollector, SystemMonitor
from src.api.dependencies import get_dataset_manager


# Global monitoring instances
health_monitor: HealthMonitor = None
metrics_collector: MetricsCollector = None
system_monitor: SystemMonitor = None


def setup_monitoring():
    """Set up monitoring systems."""
    global health_monitor, metrics_collector, system_monitor
    
    try:
        # Initialize metrics collector
        metrics_collector = MetricsCollector(config)
        
        # Initialize health monitor
        health_monitor = HealthMonitor(config)
        
        # Initialize system monitor
        system_monitor = SystemMonitor(config, metrics_collector)
        
        # Log startup info
        system_monitor.log_startup_info()
        
        return True
    except Exception as e:
        logging.error(f"Failed to setup monitoring: {e}")
        return False


def initialize_datasets() -> bool:
    """Ensure required datasets are available (and optionally refresh them)."""
    try:
        from src.services.dataset_manager import DatasetManager

        dataset_manager: DatasetManager = get_dataset_manager()
        root_path = config.get_config("DATA_ROOT_PATH", ".")

        auto_refresh_flag = os.getenv("AUTO_REFRESH_DATASETS", "false").lower() in ("1", "true", "yes")
        start = time.time()

        if auto_refresh_flag:
            logging.info("AUTO_REFRESH_DATASETS enabled. Refreshing all datasets on startup...")
            dataset_manager.refresh_all_datasets(root_path)
            duration = time.time() - start
            logging.info("Dataset refresh complete in %.2f seconds", duration)
            return True

        unified_df = dataset_manager.get_unified_dataset(root_path=root_path)
        if unified_df is None or unified_df.empty:
            logging.warning("Unified dataset unavailable; running refresh.")
            dataset_manager.refresh_all_datasets(root_path)
            duration = time.time() - start
            logging.info("Dataset refresh complete in %.2f seconds", duration)
        else:
            logging.info("Unified dataset ready with %d records", len(unified_df))
        return True
    except Exception as e:
        logging.error(f"Dataset initialization failed: {e}")
        return False


async def start_background_monitoring():
    """Start background monitoring tasks."""
    global health_monitor, system_monitor
    
    try:
        if health_monitor:
            await health_monitor.start_monitoring()
        
        if system_monitor:
            await system_monitor.start_monitoring()
        
        logging.info("Background monitoring started")
    except Exception as e:
        logging.error(f"Failed to start background monitoring: {e}")


async def stop_background_monitoring():
    """Stop background monitoring tasks."""
    global health_monitor, system_monitor
    
    try:
        if health_monitor:
            await health_monitor.stop_monitoring()
        
        if system_monitor:
            await system_monitor.stop_monitoring()
        
        logging.info("Background monitoring stopped")
    except Exception as e:
        logging.error(f"Failed to stop background monitoring: {e}")


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}, initiating graceful shutdown...")
        
        # Stop monitoring
        if health_monitor or system_monitor:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(stop_background_monitoring())
            loop.close()
        
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def validate_environment():
    """Validate the environment and configuration."""
    try:
        # Ensure required directories exist
        config.ensure_directories()
        
        # Validate configuration
        config._validate_configuration()
        
        return True
    except ConfigValidationError as e:
        logging.error(f"Configuration validation failed: {e}")
        return False
    except Exception as e:
        logging.error(f"Environment validation failed: {e}")
        return False


def main():
    """Main application entry point."""
    try:
        # Set up logging first
        setup_logging(config)
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting LeetCode Analytics API in {config.environment} mode")
        
        # Log system information
        log_system_info(config)
        
        # Validate environment
        if not validate_environment():
            logger.error("Environment validation failed, exiting")
            sys.exit(1)
        
        # Set up monitoring
        if not setup_monitoring():
            logger.error("Monitoring setup failed, exiting")
            sys.exit(1)

        # Ensure datasets are ready before serving requests
        if not initialize_datasets():
            logger.error("Dataset initialization failed, exiting")
            sys.exit(1)
        
        # Set up signal handlers
        setup_signal_handlers()
        
        # Get API configuration
        api_config = config.get_api_config()
        
        logger.info(f"Starting server on {api_config['host']}:{api_config['port']}")
        logger.info(f"Workers: {api_config['workers']}")
        logger.info(f"Environment: {config.environment}")
        
        # Record startup metrics
        if metrics_collector:
            metrics_collector.increment("application.startup")
            metrics_collector.record_gauge("application.workers", api_config['workers'])
        
        # Start background monitoring in a separate thread for uvicorn compatibility
        import threading
        
        def start_monitoring_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_background_monitoring())
            
            # Keep the loop running
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                loop.run_until_complete(stop_background_monitoring())
            finally:
                loop.close()
        
        monitoring_thread = threading.Thread(target=start_monitoring_thread, daemon=True)
        monitoring_thread.start()
        
        # Start the FastAPI server
        uvicorn.run(
            "src.api.app:app",
            host=api_config["host"],
            port=api_config["port"],
            workers=api_config["workers"] if config.environment == "production" else 1,
            log_level=config.get_logging_config()["level"].lower(),
            access_log=True,
            reload=config.environment == "development"
        )
        
    except ConfigValidationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Startup error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
