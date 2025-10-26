#!/bin/bash
# Docker management script for LeetCode Analytics API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="leetcode-analytics"
COMPOSE_FILE="docker-compose.yml"
DEV_COMPOSE_FILE="docker-compose.dev.yml"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Docker Management Script for LeetCode Analytics API

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    build           Build Docker images
    up              Start services in production mode
    dev             Start services in development mode
    down            Stop and remove containers
    restart         Restart services
    logs            Show logs
    shell           Open shell in API container
    db-shell        Open database shell
    health          Check service health
    clean           Clean up containers, images, and volumes
    backup          Backup database
    restore         Restore database from backup
    help            Show this help message

Options:
    --build         Force rebuild images
    --no-cache      Build without cache
    --follow        Follow logs (tail -f)
    --service NAME  Target specific service

Examples:
    $0 build --no-cache
    $0 up --build
    $0 dev
    $0 logs --follow api
    $0 shell
    $0 health
    $0 clean

EOF
}

check_requirements() {
    log_info "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_success "Requirements check passed"
}

build_images() {
    local no_cache=""
    if [[ "$1" == "--no-cache" ]]; then
        no_cache="--no-cache"
    fi
    
    log_info "Building Docker images..."
    docker-compose -f $COMPOSE_FILE build $no_cache
    log_success "Images built successfully"
}

start_production() {
    local build_flag=""
    if [[ "$1" == "--build" ]]; then
        build_flag="--build"
    fi
    
    log_info "Starting services in production mode..."
    docker-compose -f $COMPOSE_FILE up -d $build_flag
    
    log_info "Waiting for services to be ready..."
    sleep 10
    
    check_health
    log_success "Production services started"
}

start_development() {
    log_info "Starting services in development mode..."
    docker-compose -f $COMPOSE_FILE -f $DEV_COMPOSE_FILE up -d --build
    
    log_info "Waiting for services to be ready..."
    sleep 10
    
    log_success "Development services started"
    log_info "API available at: http://localhost:8000"
    log_info "API docs available at: http://localhost:8000/docs"
}

stop_services() {
    log_info "Stopping services..."
    docker-compose -f $COMPOSE_FILE -f $DEV_COMPOSE_FILE down
    log_success "Services stopped"
}

restart_services() {
    log_info "Restarting services..."
    stop_services
    sleep 2
    start_production
}

show_logs() {
    local service=""
    local follow_flag=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --follow)
                follow_flag="-f"
                shift
                ;;
            --service)
                service="$2"
                shift 2
                ;;
            *)
                service="$1"
                shift
                ;;
        esac
    done
    
    if [[ -n "$service" ]]; then
        log_info "Showing logs for service: $service"
        docker-compose -f $COMPOSE_FILE logs $follow_flag $service
    else
        log_info "Showing logs for all services"
        docker-compose -f $COMPOSE_FILE logs $follow_flag
    fi
}

open_shell() {
    local service="${1:-api}"
    log_info "Opening shell in $service container..."
    
    if docker-compose -f $COMPOSE_FILE ps $service | grep -q "Up"; then
        docker-compose -f $COMPOSE_FILE exec $service /bin/bash
    else
        log_error "Service $service is not running"
        exit 1
    fi
}

open_db_shell() {
    log_info "Opening database shell..."
    
    if docker-compose -f $COMPOSE_FILE ps postgres | grep -q "Up"; then
        docker-compose -f $COMPOSE_FILE exec postgres psql -U leetcode -d leetcode_analytics
    else
        log_error "Database service is not running"
        exit 1
    fi
}

check_health() {
    log_info "Checking service health..."
    
    # Check API health
    if curl -f -s http://localhost:8000/api/v1/health > /dev/null; then
        log_success "API service is healthy"
    else
        log_warning "API service health check failed"
    fi
    
    # Check database health
    if docker-compose -f $COMPOSE_FILE ps postgres | grep -q "Up"; then
        if docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U leetcode -d leetcode_analytics > /dev/null; then
            log_success "Database service is healthy"
        else
            log_warning "Database service health check failed"
        fi
    else
        log_info "Database service is not running"
    fi
}

clean_up() {
    log_warning "This will remove all containers, images, and volumes. Are you sure? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "Cleaning up..."
        
        # Stop services
        docker-compose -f $COMPOSE_FILE -f $DEV_COMPOSE_FILE down -v --remove-orphans
        
        # Remove images
        docker images | grep $PROJECT_NAME | awk '{print $3}' | xargs -r docker rmi -f
        
        # Remove volumes
        docker volume ls | grep $PROJECT_NAME | awk '{print $2}' | xargs -r docker volume rm
        
        # Prune system
        docker system prune -f
        
        log_success "Cleanup completed"
    else
        log_info "Cleanup cancelled"
    fi
}

backup_database() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    log_info "Creating database backup: $backup_file"
    
    if docker-compose -f $COMPOSE_FILE ps postgres | grep -q "Up"; then
        docker-compose -f $COMPOSE_FILE exec -T postgres pg_dump -U leetcode leetcode_analytics > $backup_file
        log_success "Database backup created: $backup_file"
    else
        log_error "Database service is not running"
        exit 1
    fi
}

restore_database() {
    local backup_file="$1"
    
    if [[ -z "$backup_file" ]]; then
        log_error "Please specify backup file"
        exit 1
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    log_warning "This will restore database from $backup_file. Existing data will be lost. Continue? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "Restoring database from: $backup_file"
        
        if docker-compose -f $COMPOSE_FILE ps postgres | grep -q "Up"; then
            docker-compose -f $COMPOSE_FILE exec -T postgres psql -U leetcode -d leetcode_analytics < $backup_file
            log_success "Database restored from: $backup_file"
        else
            log_error "Database service is not running"
            exit 1
        fi
    else
        log_info "Restore cancelled"
    fi
}

# Main script logic
case "${1:-help}" in
    build)
        check_requirements
        build_images "$2"
        ;;
    up)
        check_requirements
        start_production "$2"
        ;;
    dev)
        check_requirements
        start_development
        ;;
    down)
        stop_services
        ;;
    restart)
        check_requirements
        restart_services
        ;;
    logs)
        shift
        show_logs "$@"
        ;;
    shell)
        open_shell "$2"
        ;;
    db-shell)
        open_db_shell
        ;;
    health)
        check_health
        ;;
    clean)
        clean_up
        ;;
    backup)
        backup_database
        ;;
    restore)
        restore_database "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac