"""Custom exceptions and error handlers for the API."""

import logging
from typing import Dict, Any
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class APIException(HTTPException):
    """Base API exception with correlation ID support."""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: str = None,
        correlation_id: str = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details
        self.correlation_id = correlation_id
        super().__init__(status_code=status_code, detail=message)


class DataNotFoundError(APIException):
    """Exception for when requested data is not found."""
    
    def __init__(self, message: str = "Requested data not found", correlation_id: str = None):
        super().__init__(
            status_code=404,
            error_code="DATA_NOT_FOUND",
            message=message,
            correlation_id=correlation_id
        )


class ValidationError(APIException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, details: str = None, correlation_id: str = None):
        super().__init__(
            status_code=400,
            error_code="VALIDATION_ERROR",
            message=message,
            details=details,
            correlation_id=correlation_id
        )


class DataProcessingError(APIException):
    """Exception for data processing errors."""
    
    def __init__(self, message: str = "Error processing data", correlation_id: str = None):
        super().__init__(
            status_code=500,
            error_code="DATA_PROCESSING_ERROR",
            message=message,
            correlation_id=correlation_id
        )


class CacheError(APIException):
    """Exception for cache-related errors."""
    
    def __init__(self, message: str = "Cache operation failed", correlation_id: str = None):
        super().__init__(
            status_code=500,
            error_code="CACHE_ERROR",
            message=message,
            correlation_id=correlation_id
        )


class RateLimitError(APIException):
    """Exception for rate limiting."""
    
    def __init__(self, message: str = "Rate limit exceeded", correlation_id: str = None):
        super().__init__(
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            message=message,
            correlation_id=correlation_id
        )


def create_error_response(
    error_code: str,
    message: str,
    details: str = None,
    correlation_id: str = None,
    status_code: int = 500
) -> Dict[str, Any]:
    """Create a standardized error response."""
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if correlation_id:
        error_response["error"]["correlation_id"] = correlation_id
    
    return error_response


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom API exceptions."""
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    logger.error(
        f"API Exception: {exc.error_code}",
        extra={
            "correlation_id": correlation_id,
            "error_code": exc.error_code,
            "error_message": exc.message,
            "details": exc.details,
            "status_code": exc.status_code,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            correlation_id=correlation_id or exc.correlation_id
        )
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions."""
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    # Map HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    logger.error(
        f"HTTP Exception: {error_code}",
        extra={
            "correlation_id": correlation_id,
            "status_code": exc.status_code,
            "detail": exc.detail,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=error_code,
            message=str(exc.detail),
            correlation_id=correlation_id
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    # Extract validation error details
    error_details = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_details.append(f"{field}: {message}")
    
    details = "; ".join(error_details)
    
    logger.warning(
        f"Validation Error",
        extra={
            "correlation_id": correlation_id,
            "errors": exc.errors(),
        }
    )
    
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details=details,
            correlation_id=correlation_id
        )
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    logger.error(
        f"Unexpected error: {type(exc).__name__}",
        extra={
            "correlation_id": correlation_id,
            "error": str(exc),
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details="Please try again later or contact support if the problem persists",
            correlation_id=correlation_id
        )
    )


def setup_exception_handlers(app):
    """Set up all exception handlers for the FastAPI app."""
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers configured successfully")
