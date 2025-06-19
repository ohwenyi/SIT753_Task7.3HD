from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uvicorn
from contextlib import asynccontextmanager


from .config import get_settings
from .utils.logging import setup_logging, get_logger, log_request
from .routers import health, echo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    settings = get_settings()
    logger = get_logger(__name__)

    logger.info("Application starting up", extra={
        "app_name": settings.app_name,
        "debug": settings.debug,
        "log_level": settings.log_level
    })

    yield

    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.
    Returns:
        Configured FastAPI application
    """
    settings = get_settings()

    setup_logging(
        log_level=settings.log_level,
        json_format=settings.debug  # Use JSON format in production
    )

    logger = get_logger(__name__)

    app = FastAPI(
        title=settings.app_name,
        description="A minimal FastAPI Microservice Health Checker",
        version="1.0.0",
        debug=settings.debug,
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests with timing information."""
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        log_request(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        return response
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Global exception handler for unexpected errors.
        """
        logger.error("Unhandled exception occurred", extra={
            "method": request.method,
            "path": str(request.url.path),
            "error": str(exc),
            "error_type": type(exc).__name__
        }, exc_info=True)

        # Don't expose internal errors in production
        if settings.debug:
            detail = f"Internal server error: {str(exc)}"
        else:
            detail = "Internal server error"

        return JSONResponse(
            status_code=500,
            content={"detail": detail, "type": "internal_server_error"}
        )
    
    # Add HTTP exception handler for consistent error responses
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Handle HTTP exceptions with consistent formatting.
        """
        logger.warning("HTTP exception occurred", extra={
            "method": request.method,
            "path": str(request.url.path),
            "status_code": exc.status_code,
            "detail": exc.detail
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "type": "http_exception",
                "status_code": exc.status_code
            }
        )
    
    app.include_router(health.router)
    app.include_router(echo.router)

    # Root endpoint
    async def root():
        """Root endpoint with basic API information."""
        return {
            "name": settings.app_name,
            "version": "1.0.0",
            "status": "running",
            "timestamp": time.time(),
            "endpoints": {
                "health": "/health/",
                "echo": "/echo/",
                "docs": "/docs",
                "redoc": "/redoc"
            }
        }
    
    logger.info("FastAPI application created successfully")
    return app

app = create_app()

if __name__ == "__main__":
    """
    Run the application directly.
    """
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_config=None,
        access_log=False
    )