from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import time
from ..utils.logging import get_logger


logger = get_logger(__name__)

router = APIRouter(prefix="/echo", tags=["echo"])

class EchoResponse(BaseModel):
    """Echo response model."""
    echo: str = Field(..., description="Echoed message")
    timestamp: float = Field(..., description="When the echo was processed.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class EchoRequest(BaseModel):
    """Echo request model for POST endpoint."""
    message: str = Field(..., min_length=1, max_length=1000, description="Message to echo")
    uppercase: bool = Field(default=False, description="Whether to return uppercase")
    prefix: Optional[str] = Field(default=None, max_length=50, description="Optional prefix to add")


@router.get("/", response_model=EchoResponse)
async def echo_query(
    msg: str = Query(..., min_length=1, max_length=1000, description="Message to echo"),
    uppercase: bool = Query(default=False, description="Return message in uppercase"),
    prefix: Optional[str] = Query(default=None, max_length=50, description="Optional prefix")
):
    """
    Echo a message from query parameters.
    Args:
        msg: The message to echo back
        uppercase: Whether to convert to uppercase
        prefix: Optional prefix to add to the message
    Returns:
        EchoResponse with the processed message
    """
    start_time = time.time()
    
    processed_msg = msg
    if uppercase:
        processed_msg = processed_msg.upper()

    response = EchoResponse(
        echo=processed_msg,
        timestamp=time.time(),
        metadata ={
            "original_message": msg,
            "transformations_applied": {
                "uppercase": uppercase,
                "prefix_added": prefix is not None
            },
            "processing_time_ms": (time.time() - start_time) * 1000
        }
    )

    # Log the request
    logger.info("Echo request processed", extra={
        "endpoint": "echo_query",
        "original_message": msg,
        "processed_message": processed_msg,
        "uppercase": uppercase,
        "prefix": prefix,
        "processing_time_ms": response.metadata["processing_time_ms"]
    })
    
    return response

@router.post("/", response_model=EchoResponse)
async def echo_post(request: EchoRequest):
    """
    Echo a message from POST request body.
    Args:
        request: EchoRequest with message and options 
    Returns:
        EchoResponse with the processed message
    """
    start_time = time.time()

    processed_msg = request.message
    if request.uppercase:
        processed_msg = processed_msg.upper()

    if request.prefix:
        processed_msg = f"{request.prefix}: {processed_msg}"

    response = EchoResponse(
        echo=processed_msg,
        timestamp=time.time(),
        metadata={
            "original_message": request.message,
            "transformations_applied": {
                "uppercase": request.uppercase,
                "prefix_added": request.prefix is not None
            },
            "processing_time_ms": (time.time() - start_time) * 1000
        }
    )       

    # Log the request
    logger.info("Echo POST request processed", extra={
        "endpoint": "echo_post",
        "original_message": request.message,
        "processed_message": processed_msg,
        "uppercase": request.uppercase,
        "prefix": request.prefix,
        "processing_time_ms": response.metadata["processing_time_ms"]
    })
    
    return response

@router.get("/reverse", response_model=EchoResponse)
async def echo_reverse(
    msg: str = Query(..., min_length=1, max_length=1000, description="Message to reverse and echo")
):
    """
    Reverse a message and echo it back.
    Args:
        msg: The message to reverse
    Returns:
        EchoResponse with the reversed message
    """
    start_time = time.time()

    try:
        reversed_msg = msg[::-1]

        response = EchoResponse(
            echo=reversed_msg,
            timestamp=time.time(),
            metadata={
                "original_message": msg,
                "transformation": "reverse",
                "processing_time_ms": (time.time() - start_time) * 1000
            }
        )

        logger.info("Echo reverse request processed", extra={
            "endpoint": "echo_reverse",
            "original_message": msg,
            "reversed_message": reversed_msg,
            "processing_time_ms": response.metadata["processing_time_ms"]
        })
        
        return response
    except Exception as e:
        logger.error("Error processing reverse request", extra={
            "endpoint": "echo_reverse",
            "original_message": msg,
            "error": str(e)
        })

        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to process reverse request", "message": str(e)}
        )
    
@router.get("/stats")
async def echo_stats():
    """
    Get statistics about the echo service.
    Returns:
        Dictionary with service statistics
    """
    return {
        "service": "echo",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/echo/", "method": "GET", "description": "Echo message from query params"},
            {"path": "/echo/", "method": "POST", "description": "Echo message from request body"},
            {"path": "/echo/reverse", "method": "GET", "description": "Reverse and echo message"},
            {"path": "/echo/stats", "method": "GET", "description": "Get service statistics"}
        ],
        "timestamp": time.time()
    }