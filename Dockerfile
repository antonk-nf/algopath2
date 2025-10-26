# Multi-stage build for LeetCode Analytics API
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_ENV=production

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create necessary directories
RUN mkdir -p /app/data /app/cache /app/logs && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser .env.template ./

# Copy startup script
COPY --chown=appuser:appuser docker/entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${API_PORT}/api/v1/health || exit 1

# Expose port
EXPOSE ${API_PORT}

# Set resource limits (can be overridden by docker-compose)
ENV MAX_MEMORY_MB=2048 \
    PARALLEL_WORKERS=4

# Default command
CMD ["./entrypoint.sh"]

# Development stage
FROM production as development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    flake8 \
    mypy

# Set development environment
ENV ENVIRONMENT=development \
    LOG_LEVEL=DEBUG

# Switch back to appuser
USER appuser

# Development command (with reload)
CMD ["python", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]