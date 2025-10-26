# Docker Deployment Guide

This guide covers deploying the LeetCode Analytics API using Docker and Docker Compose.

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- 10GB free disk space

### Development Setup

1. **Clone and prepare the environment:**
   ```bash
   git clone <repository-url>
   cd leetcode-analytics-api
   cp .env.template .env
   # Edit .env with your configuration
   ```

2. **Start development environment:**
   ```bash
   ./docker/manage.sh dev
   ```

3. **Access the API:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/v1/health

### Production Setup

1. **Configure environment:**
   ```bash
   cp .env.template .env
   # Edit .env for production settings
   ```

2. **Start production services:**
   ```bash
   ./docker/manage.sh up --build
   ```

3. **Verify deployment:**
   ```bash
   ./docker/manage.sh health
   ```

## Architecture

### Services

- **api**: Main FastAPI application
- **postgres**: PostgreSQL database (optional)
- **redis**: Redis cache (optional)
- **nginx**: Reverse proxy and load balancer (optional)

### Volumes

- `postgres_data`: Database persistence
- `redis_data`: Redis persistence
- `leetcode_cache`: Application cache
- `leetcode_logs`: Application logs

### Networks

- `leetcode_network`: Internal communication network

## Configuration

### Environment Variables

Key environment variables for Docker deployment:

```bash
# Environment
ENVIRONMENT=production

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=2

# Data Paths
DATA_ROOT_PATH=/app/data
CACHE_DIR=/app/cache

# Database (optional)
DATABASE_ENABLED=true
DATABASE_URL=postgresql://leetcode:password@postgres:5432/leetcode_analytics

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/app/logs/app.log

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=30
```

### Resource Limits

Default resource limits:

- **API Container**: 2GB RAM, 1 CPU
- **Database**: 512MB RAM, 0.5 CPU
- **Redis**: 256MB RAM, 0.25 CPU
- **Nginx**: 128MB RAM, 0.25 CPU

Adjust in `docker-compose.yml` as needed.

## Management Commands

Use the management script for common operations:

```bash
# Build images
./docker/manage.sh build [--no-cache]

# Start services
./docker/manage.sh up [--build]
./docker/manage.sh dev

# Stop services
./docker/manage.sh down

# View logs
./docker/manage.sh logs [--follow] [service-name]

# Open shell
./docker/manage.sh shell [service-name]
./docker/manage.sh db-shell

# Health check
./docker/manage.sh health

# Database operations
./docker/manage.sh backup
./docker/manage.sh restore backup_file.sql

# Cleanup
./docker/manage.sh clean
```

## Data Management

### Data Directory

Mount your CSV data directory to `/app/data` in the container:

```yaml
volumes:
  - ./your-data-directory:/app/data:ro
```

### Database Initialization

The database is automatically initialized with:
- Required tables and indexes
- Sample topic data
- Optimized schema for analytics queries

### Cache Management

The application uses file-based caching by default. Cache files are stored in the `leetcode_cache` volume.

## Monitoring and Logging

### Health Checks

- **API**: `GET /api/v1/health`
- **Database**: `pg_isready` command
- **Redis**: `redis-cli ping`

### Logging

Logs are structured JSON format in production:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "logger": "src.api.app",
  "message": "Request processed",
  "duration_ms": 45.2,
  "endpoint": "/api/v1/problems/top"
}
```

### Metrics

Application metrics are collected automatically:
- Request counts and response times
- Data processing metrics
- System resource usage
- Cache hit rates

Access metrics via the health endpoint or monitoring tools.

## Security

### Container Security

- Non-root user (`appuser`)
- Read-only data mounts
- Resource limits
- Security headers via Nginx

### Network Security

- Internal network isolation
- Rate limiting via Nginx
- Restricted metrics endpoint access

### Database Security

- Dedicated database user
- Connection pooling
- Prepared statements

## Troubleshooting

### Common Issues

1. **Port conflicts:**
   ```bash
   # Change ports in .env file
   API_PORT=8001
   ```

2. **Memory issues:**
   ```bash
   # Increase Docker memory limit
   # Reduce API_WORKERS in .env
   API_WORKERS=1
   ```

3. **Database connection:**
   ```bash
   # Check database logs
   ./docker/manage.sh logs postgres
   
   # Test connection
   ./docker/manage.sh db-shell
   ```

4. **Cache issues:**
   ```bash
   # Clear cache volume
   docker volume rm leetcode-analytics_leetcode_cache
   ```

### Debug Mode

Enable debug logging:

```bash
# In .env file
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### Container Inspection

```bash
# Check container status
docker-compose ps

# Inspect container
docker inspect leetcode-analytics-api

# View resource usage
docker stats
```

## Performance Tuning

### API Performance

- Adjust `API_WORKERS` based on CPU cores
- Tune `PARALLEL_WORKERS` for data processing
- Configure `CHUNK_SIZE` for memory usage

### Database Performance

- Monitor connection pool usage
- Adjust `DATABASE_POOL_SIZE`
- Consider read replicas for high load

### Cache Optimization

- Set appropriate `CACHE_TTL_HOURS`
- Monitor cache hit rates
- Consider Redis for distributed caching

## Backup and Recovery

### Database Backup

```bash
# Create backup
./docker/manage.sh backup

# Restore from backup
./docker/manage.sh restore backup_20240101_120000.sql
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v leetcode-analytics_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v leetcode-analytics_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## Scaling

### Horizontal Scaling

1. **Load Balancer**: Use external load balancer
2. **Database**: Configure read replicas
3. **Cache**: Use Redis cluster
4. **Storage**: Use shared storage for cache

### Vertical Scaling

Adjust resource limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
```

## Production Checklist

- [ ] Configure environment variables
- [ ] Set up SSL certificates
- [ ] Configure monitoring
- [ ] Set up log aggregation
- [ ] Configure backups
- [ ] Test disaster recovery
- [ ] Security audit
- [ ] Performance testing
- [ ] Documentation update