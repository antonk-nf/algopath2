#!/bin/bash
set -e

# LeetCode Analytics API Docker Entrypoint Script

echo "Starting LeetCode Analytics API..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "API Host: ${API_HOST:-0.0.0.0}"
echo "API Port: ${API_PORT:-8000}"

# Function to handle shutdown gracefully
shutdown_handler() {
    echo "Received shutdown signal, stopping gracefully..."
    if [ ! -z "$API_PID" ]; then
        kill -TERM "$API_PID"
        wait "$API_PID"
    fi
    exit 0
}

# Set up signal handlers
trap shutdown_handler SIGTERM SIGINT

# Validate environment
echo "Validating environment..."

# Check if data directory exists and is accessible
if [ ! -d "${DATA_ROOT_PATH:-/app/data}" ]; then
    echo "Warning: Data directory ${DATA_ROOT_PATH:-/app/data} does not exist"
    echo "Creating data directory..."
    mkdir -p "${DATA_ROOT_PATH:-/app/data}"
fi

# Check if cache directory exists and is writable
if [ ! -d "${CACHE_DIR:-/app/cache}" ]; then
    echo "Creating cache directory..."
    mkdir -p "${CACHE_DIR:-/app/cache}"
fi

# Test cache directory write permissions
if ! touch "${CACHE_DIR:-/app/cache}/.write_test" 2>/dev/null; then
    echo "Error: Cannot write to cache directory ${CACHE_DIR:-/app/cache}"
    exit 1
fi
rm -f "${CACHE_DIR:-/app/cache}/.write_test"

# Create logs directory if log file is specified
if [ ! -z "$LOG_FILE" ]; then
    LOG_DIR=$(dirname "$LOG_FILE")
    if [ ! -d "$LOG_DIR" ]; then
        echo "Creating log directory: $LOG_DIR"
        mkdir -p "$LOG_DIR"
    fi
fi

# Validate required environment variables for production
if [ "${ENVIRONMENT}" = "production" ]; then
    echo "Validating production environment..."
    
    # Check critical settings
    if [ -z "$DATA_ROOT_PATH" ]; then
        echo "Warning: DATA_ROOT_PATH not set, using default"
    fi
    
    # Validate numeric settings
    if ! [[ "$API_PORT" =~ ^[0-9]+$ ]] || [ "$API_PORT" -lt 1 ] || [ "$API_PORT" -gt 65535 ]; then
        echo "Error: Invalid API_PORT: $API_PORT"
        exit 1
    fi
    
    if ! [[ "${API_WORKERS:-1}" =~ ^[0-9]+$ ]] || [ "${API_WORKERS:-1}" -lt 1 ]; then
        echo "Error: Invalid API_WORKERS: ${API_WORKERS:-1}"
        exit 1
    fi
fi

# Display configuration summary
echo "Configuration Summary:"
echo "  Environment: ${ENVIRONMENT:-production}"
echo "  Data Path: ${DATA_ROOT_PATH:-/app/data}"
echo "  Cache Dir: ${CACHE_DIR:-/app/cache}"
echo "  Log Level: ${LOG_LEVEL:-INFO}"
echo "  API Workers: ${API_WORKERS:-1}"
echo "  Database Enabled: ${DATABASE_ENABLED:-false}"
echo "  Cache Enabled: ${CACHE_ENABLED:-true}"
echo "  Metrics Enabled: ${METRICS_ENABLED:-true}"

# Wait for database if enabled
if [ "${DATABASE_ENABLED}" = "true" ] && [ ! -z "$DATABASE_URL" ]; then
    echo "Waiting for database connection..."
    
    # Simple connection test (you might want to use a more sophisticated health check)
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Database connection attempt $attempt/$max_attempts..."
        
        # This is a placeholder - you'd implement actual database connectivity check
        # For now, just wait a bit
        sleep 2
        
        # In a real implementation, you'd test the database connection here
        # if database_connection_test; then
        #     echo "Database connection successful"
        #     break
        # fi
        
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        echo "Warning: Could not verify database connection after $max_attempts attempts"
        echo "Proceeding anyway..."
    fi
fi

# Pre-flight checks
echo "Running pre-flight checks..."

# Check Python environment
python --version
echo "Python path: $(which python)"

# Check if the application can import successfully
if ! python -c "from src.config.settings import config; print('Configuration loaded successfully')" 2>/dev/null; then
    echo "Error: Failed to load application configuration"
    exit 1
fi

# Run health check if in production
if [ "${ENVIRONMENT}" = "production" ]; then
    echo "Running initial health check..."
    if ! python -c "
from src.config.settings import create_config
from src.monitoring import HealthMonitor
import asyncio

async def health_check():
    try:
        config = create_config()
        monitor = HealthMonitor(config)
        result = await monitor.run_all_checks()
        if result['status'] != 'healthy':
            print('Health check failed:', result)
            exit(1)
        print('Health check passed')
    except Exception as e:
        print('Health check error:', e)
        exit(1)

asyncio.run(health_check())
"; then
        echo "Error: Initial health check failed"
        exit 1
    fi
fi

echo "Pre-flight checks completed successfully"

# Start the application
echo "Starting application..."

if [ "${ENVIRONMENT}" = "development" ]; then
    # Development mode with reload
    echo "Starting in development mode with auto-reload..."
    exec python -m uvicorn src.api.app:app \
        --host "${API_HOST:-0.0.0.0}" \
        --port "${API_PORT:-8000}" \
        --reload \
        --log-level "${LOG_LEVEL:-debug}" \
        --access-log
else
    # Production mode
    echo "Starting in production mode..."
    exec python src/main.py &
    API_PID=$!
    
    # Wait for the process
    wait $API_PID
fi