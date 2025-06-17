import logging
import sys
from loguru import logger
from typing import Optional, Any
import json


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging and redirect to loguru.
    This ensures all logs (including from FastAPI, uvicorn, etc.) go through our structured logger.
    """
    
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logged message originated
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:  # type: ignore
            frame = frame.f_back # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(log_level: str = "INFO", json_format: bool = False) -> None:
    """
    Configure structured logging with loguru.
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to output logs in JSON format (useful for production)
    """
    
    # Remove default loguru handler
    logger.remove()
    
    # Configure format based on environment
    if json_format:
        # Structured JSON format for production
        format_string = json.dumps({
            "timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}",
            "level": "{level}",
            "module": "{name}",
            "function": "{function}",
            "line": "{line}",
            "message": "{message}"
        })
    else:
        # Human-readable format for development
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
    
    # Add loguru handler
    logger.add(
        sys.stdout,
        format=format_string,
        level=log_level.upper(),
        colorize=not json_format,  # Only colorize in development
        serialize=json_format      # Serialize to JSON in production
    )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Set specific loggers to appropriate levels
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        logging.getLogger(logger_name).handlers = [InterceptHandler()]


def get_logger(name: str) -> Any:
    """
    Get a logger instance for a specific module.
    Args:
        name: Usually __name__ from the calling module
    Returns:
        Configured logger instance
    """
    return logger.bind(module=name)


def log_request(method: str, path: str, status_code: int, duration_ms: float) -> None:
    """
    Log HTTP request in a structured way.
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
    """
    logger.info(
        "HTTP Request",
        extra={
            "http_method": method,
            "http_path": path, 
            "http_status": status_code,
            "duration_ms": duration_ms
        }
    )


def log_health_check(service: str, status: str, duration_ms: float, error: Optional[str] = None) -> None:
    """
    Log health check results in a structured way.
    Args:
        service: Name of the service being checked (database, redis, etc.)
        status: Status of the check (healthy, unhealthy)
        duration_ms: Check duration in milliseconds
        error: Error message if check failed
    """
    log_data = {
        "health_check": True,
        "service": service,
        "status": status,
        "duration_ms": duration_ms
    }
    
    if error:
        log_data["error"] = error
        logger.warning("Health check failed", extra=log_data)
    else:
        logger.info("Health check passed", extra=log_data)