"""Middleware components for the FastAPI application."""

import time
import uuid
import logging
from typing import Callable, Iterable, List
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate correlation ID for request tracking
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Log request details
        start_time = time.time()
        logger.info(
            f"Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response details
            logger.info(
                f"Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "status_code": response.status_code,
                    "process_time": round(process_time, 4),
                }
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            return response
            
        except Exception as e:
            # Log error details
            process_time = time.time() - start_time
            logger.error(
                f"Request failed",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "process_time": round(process_time, 4),
                },
                exc_info=True
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        return response


def setup_cors_middleware(app, config):
    """Set up CORS middleware with configuration."""
    allowed_origins = _normalize_config_list(config.get_config("CORS_ORIGINS", "*")) or ["*"]
    allowed_methods = _normalize_config_list(config.get_config("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS"))
    allowed_headers = _normalize_config_list(config.get_config("CORS_HEADERS", "*")) or ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=allowed_methods,
        allow_headers=allowed_headers,
        expose_headers=["X-Correlation-ID", "X-Process-Time"]
    )
    
    logger.info(f"CORS middleware configured with origins: {allowed_origins}")


def setup_trusted_host_middleware(app, config):
    """Set up trusted host middleware with configuration."""
    allowed_hosts = _normalize_config_list(config.get_config("ALLOWED_HOSTS", "*")) or ["*"]
    
    if "*" not in allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )
        logger.info(f"Trusted host middleware configured with hosts: {allowed_hosts}")
    else:
        logger.info("Trusted host middleware disabled (allowing all hosts)")


def setup_all_middleware(app, config):
    """Set up all middleware components."""
    # Order matters - add in reverse order of execution
    
    # Security headers (executed last)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Request logging (executed second)
    app.add_middleware(RequestLoggingMiddleware)
    
    # CORS (executed first)
    setup_cors_middleware(app, config)
    
    # Trusted hosts (if configured)
    setup_trusted_host_middleware(app, config)
    
    logger.info("All middleware components configured successfully")


def _normalize_config_list(value: object) -> List[str]:
    """Normalize config values that may be string, list, or iterable into a list of strings."""
    if value is None:
        return []

    if isinstance(value, str):
        parts = [part.strip() for part in value.split(',') if part.strip()]
        return parts or []

    if isinstance(value, Iterable):
        return [str(item).strip() for item in value if str(item).strip()]

    return [str(value)]
