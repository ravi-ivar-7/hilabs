from typing import Any, Optional, Dict
from datetime import datetime


def create_response(
    success: bool,
    message: str,
    data: Optional[Any] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized API response"""
    response = {
        "success": success,
        "message": message,
        "error": error,
        "data": data,
        "metadata": metadata or {}
    }
    
    # Add timestamp to metadata
    if "timestamp" not in response["metadata"]:
        response["metadata"]["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    return response


def create_success_response(
    message: str,
    data: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create success response"""
    return create_response(
        success=True,
        message=message,
        data=data,
        metadata=metadata
    )


def create_error_response(
    message: str,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create error response"""
    return create_response(
        success=False,
        message=message,
        error=error,
        metadata=metadata
    )

def success_response(
    message: str,
    data: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create success response (alias for backward compatibility)"""
    return create_success_response(message, data, metadata)


def error_response(
    message: str,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create error response (alias for backward compatibility)"""
    return create_error_response(message, error, metadata)
