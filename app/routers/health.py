from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import time
import asyncpg
import aioredis
from ..config import Settings, get_settings
from ..utils.logging import get_logger, log_health_check

# Get logger for this module
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str  # "healthy" or "unhealthy"
    timestamp: float
    version: str = "1.0.0"
    checks: Dict[str, Any]


class ServiceCheck(BaseModel):
    """Individual service check result."""
    status: str  # "healthy" or "unhealthy"
    duration_ms: float
    error: Optional[str] = None


async def check_database(database_url: str, timeout: float) -> ServiceCheck:
    """
    Check database connectivity.
    Args:
        database_url: Database connection string
        timeout: Timeout in seconds
    Returns:
        ServiceCheck with database status
    """
    start_time = time.time()
    
    try:
        # Attempt to connect to database
        conn = await asyncio.wait_for(
            asyncpg.connect(database_url), 
            timeout=timeout
        )
        
        # Simple query to verify connectivity
        await conn.execute("SELECT 1")
        await conn.close()
        
        duration_ms = (time.time() - start_time) * 1000
        log_health_check("database", "healthy", duration_ms)
        
        return ServiceCheck(
            status="healthy",
            duration_ms=duration_ms
        )
        
    except asyncio.TimeoutError:
        duration_ms = (time.time() - start_time) * 1000
        error = f"Database connection timeout after {timeout}s"
        log_health_check("database", "unhealthy", duration_ms, error)
        
        return ServiceCheck(
            status="unhealthy",
            duration_ms=duration_ms,
            error=error
        )
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error = f"Database connection failed: {str(e)}"
        log_health_check("database", "unhealthy", duration_ms, error)
        
        return ServiceCheck(
            status="unhealthy",
            duration_ms=duration_ms,
            error=error
        )


async def check_redis(redis_url: str, timeout: float) -> ServiceCheck:
    """
    Check Redis connectivity.
    Args:
        redis_url: Redis connection string
        timeout: Timeout in seconds
    Returns:
        ServiceCheck with Redis status
    """
    start_time = time.time()
    
    try:
        # Connect to Redis
        redis = await asyncio.wait_for(
            aioredis.from_url(redis_url),
            timeout=timeout
        )
        
        # Simple ping to verify connectivity
        await redis.ping()
        await redis.close()
        
        duration_ms = (time.time() - start_time) * 1000
        log_health_check("redis", "healthy", duration_ms)
        
        return ServiceCheck(
            status="healthy",
            duration_ms=duration_ms
        )
        
    except asyncio.TimeoutError:
        duration_ms = (time.time() - start_time) * 1000
        error = f"Redis connection timeout after {timeout}s"
        log_health_check("redis", "unhealthy", duration_ms, error)
        
        return ServiceCheck(
            status="unhealthy",
            duration_ms=duration_ms,
            error=error
        )
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error = f"Redis connection failed: {str(e)}"
        log_health_check("redis", "unhealthy", duration_ms, error)
        
        return ServiceCheck(
            status="unhealthy",
            duration_ms=duration_ms,
            error=error
        )


async def perform_health_checks(settings: Settings) -> Dict[str, ServiceCheck]:
    """
    Perform all configured health checks concurrently.
    Args:
        settings: Application settings
    Returns:
        Dictionary of service names to their check results
    """
    checks = {}
    tasks = []
    
    # Add database check if configured
    if settings.database_url:
        tasks.append(("database", check_database(settings.database_url, settings.health_check_timeout)))
    
    # Add Redis check if configured  
    if settings.redis_url:
        tasks.append(("redis", check_redis(settings.redis_url, settings.health_check_timeout)))
    
    # Run all checks concurrently
    if tasks:
        results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
        
        for i, (service_name, _) in enumerate(tasks):
            result = results[i]
            if isinstance(result, Exception):
                # Handle unexpected exceptions
                checks[service_name] = ServiceCheck(
                    status="unhealthy",
                    duration_ms=0,
                    error=f"Unexpected error: {str(result)}"
                )
            else:
                checks[service_name] = result

    return checks
@router.get("/", response_model=HealthStatus)
async def health_check(settings: Settings = Depends(get_settings)):
    """
    Comprehensive health check endpoint.
    Returns:
        HealthStatus with overall status and individual service checks
    """
    timestamp = time.time()
    
    # Perform all health checks
    checks = await perform_health_checks(settings)
    
    # Determine overall status
    overall_status = "healthy"
    if checks:
        # If any check is unhealthy, overall status is unhealthy
        if any(check.status == "unhealthy" for check in checks.values()):
            overall_status = "unhealthy"
    
    # Create response
    health_status = HealthStatus(
        status=overall_status,
        timestamp=timestamp,
        checks={name: check.model_dump() for name, check in checks.items()}
    )
    
    # Log overall health check result
    logger.info(f"Health check completed: {overall_status}", extra={
        "health_check_summary": True,
        "overall_status": overall_status,
        "services_checked": len(checks),
        "timestamp": timestamp
    })
    
    # Return appropriate HTTP status
    if overall_status == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status.model_dump())
    
    return health_status


@router.get("/live")
async def liveness_check():
    """
    Simple liveness check - just confirms the app is running.
    This is useful for Kubernetes liveness probes.
    """
    return {"status": "alive", "timestamp": time.time()}


@router.get("/ready")  
async def readiness_check(settings: Settings = Depends(get_settings)):
    """
    Readiness check - confirms the app can serve requests.
    This is useful for Kubernetes readiness probes.
    """
    checks = await perform_health_checks(settings)
    
    critical_services = ["database"]
    
    is_ready = True
    for service_name, check in checks.items():
        if service_name in critical_services and check.status == "unhealthy":
            logger.info(f"Checked services: {service_name}")
            logger.info(f"Checks status: {check.status}")
            is_ready = False
            break
    
    status_code = 200 if is_ready else 503
    return JSONResponse(
        status_code=status_code,
        content={
        "status": "ready" if is_ready else "not_ready",
        "timestamp": time.time(),
        "checks": {name: check.model_dump() for name, check in checks.items()}
        }
    )