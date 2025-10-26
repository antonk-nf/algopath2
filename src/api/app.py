"""FastAPI application factory and configuration."""

import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from ..config.settings import config
from .middleware import setup_all_middleware
from .exceptions import setup_exception_handlers
from .routers import problems, topics, companies, analytics, health

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Application metadata
    app_config = {
        "title": "LeetCode Analytics API",
        "description": """
        A comprehensive analytics API for LeetCode interview data across 470+ companies.
        
        ## Features
        
        * **Cross-Company Analysis**: Compare problem frequencies across different companies
        * **Topic Trends**: Analyze trending topics and skill areas
        * **Difficulty Analysis**: Understand difficulty distributions and correlations
        * **Temporal Trends**: Track changes in problem popularity over time
        * **Advanced Filtering**: Flexible filtering by company, difficulty, topics, and more
        
        ## Data Sources
        
        The API processes CSV data from company-specific directories containing:
        - Problem titles and LeetCode links
        - Frequency scores and acceptance rates
        - Difficulty levels and topic tags
        - Multiple timeframe windows (30d, 3m, 6m, 6m+, all)
        
        ## Rate Limiting
        
        API requests are rate-limited to ensure fair usage. See response headers for current limits.
        
        ## Support
        
        For questions or issues, please check the documentation or contact the development team.
        """,
        "version": config.get_config("API_VERSION", "1.0.0"),
        "contact": {
            "name": "LeetCode Analytics API Team",
            "email": config.get_config("CONTACT_EMAIL", "support@example.com"),
        },
        "license_info": {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
    }
    
    # Create FastAPI app
    app = FastAPI(**app_config)
    
    # Set up middleware
    setup_all_middleware(app, config)
    
    # Set up exception handlers
    setup_exception_handlers(app)
    
    # Include API routers
    setup_routers(app)
    
    # Add startup and shutdown event handlers
    setup_event_handlers(app)
    
    logger.info(f"FastAPI application created: {app_config['title']} v{app_config['version']}")
    
    return app


def setup_routers(app: FastAPI):
    """Set up API routers."""
    # Include all routers with API v1 prefix
    app.include_router(problems.router, prefix="/api/v1")
    app.include_router(topics.router, prefix="/api/v1")
    app.include_router(companies.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(health.router, prefix="/api/v1")
    
    logger.info("API routers configured successfully")


def setup_event_handlers(app: FastAPI):
    """Set up application startup and shutdown event handlers."""
    
    @app.on_event("startup")
    async def startup_event():
        """Handle application startup."""
        logger.info("Starting LeetCode Analytics API")
        
        # Log configuration
        logger.info(f"Environment: {config.environment}")
        logger.info(f"Debug mode: {config.debug}")
        logger.info(f"Data root: {config.get_config('DATA_ROOT_PATH')}")
        logger.info(f"Cache directory: {config.get_config('CACHE_DIR')}")
        
        # Initialize services (if needed)
        try:
            # Initialize metadata lookup service
            from ..services.metadata_lookup_service import metadata_lookup_service
            
            metadata_file_path = config.get_config("LEETCODE_METADATA_PATH", "leetcode_metadata.parquet")
            if metadata_lookup_service.initialize(metadata_file_path):
                logger.warning("Metadata lookup service initialized successfully")
            else:
                logger.warning("Metadata lookup service initialization failed - quality features will be unavailable")
            
            logger.warning("Application startup completed successfully")
        except Exception as e:
            logger.error(f"Error during startup: {str(e)}", exc_info=True)
            raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Handle application shutdown."""
        logger.info("Shutting down LeetCode Analytics API")
        
        # Cleanup resources
        try:
            # Close database connections, cleanup caches, etc.
            logger.info("Application shutdown completed successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}", exc_info=True)


def get_app() -> FastAPI:
    """Get configured FastAPI application instance."""
    return create_app()


# Create the app instance
app = create_app()


# Root endpoint
@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to LeetCode Analytics API",
        "version": config.get_config("API_VERSION", "1.0.0"),
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "health": "/api/v1/health"
    }


# API info endpoint
@app.get("/info", response_class=JSONResponse)
async def api_info():
    """Get API information and capabilities."""
    return {
        "name": "LeetCode Analytics API",
        "version": config.get_config("API_VERSION", "1.0.0"),
        "description": "Analytics API for LeetCode interview data",
        "environment": config.environment,
        "features": [
            "Cross-company problem analysis",
            "Topic trend analysis",
            "Difficulty correlation analysis",
            "Temporal trend tracking",
            "Advanced filtering and search",
            "Comprehensive statistics"
        ],
        "endpoints": {
            "problems": "/api/v1/problems/",
            "topics": "/api/v1/topics/",
            "companies": "/api/v1/companies/",
            "analytics": "/api/v1/analytics/",
            "health": "/api/v1/health"
        }
    }