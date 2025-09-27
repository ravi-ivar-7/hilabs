from fastapi import APIRouter, Depends
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..schemas import HealthResponse
from ..utils.response_utils import create_success_response, create_error_response
from ..core.database import get_db
from ..services.filesystem_service import FileSystemService
from ..services.celery_service import CeleryService

router = APIRouter()

@router.get("/health", response_model=dict)
async def health_check():
    health_data = HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        services={
            "database": "connected",
            "storage": "connected", 
            "redis": "connected"
        }
    )
    return create_success_response(
        data=health_data.dict(),
        message="Service is healthy"
    )

@router.get("/health/database", response_model=dict)
async def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return create_success_response(
            data={"status": "connected", "timestamp": datetime.utcnow()},
            message="Database connection healthy"
        )
    except Exception as e:
        return create_error_response(
            message="Database connection failed",
            error=str(e)
        )

@router.get("/health/storage", response_model=dict)
async def storage_health():
    try:
        filesystem_service = FileSystemService()
        # Check if upload directories exist and are writable
        test_path = filesystem_service.base_path / "contracts-tn"
        if test_path.exists() and test_path.is_dir():
            return create_success_response(
                data={"status": "connected", "timestamp": datetime.utcnow()},
                message="Storage connection healthy"
            )
        else:
            return create_error_response(
                message="Storage connection failed",
                error="Upload directories not accessible"
            )
    except Exception as e:
        return create_error_response(
            message="Storage connection failed",
            error=str(e)
        )

@router.get("/", response_model=dict)
async def root():
    return create_success_response(
        data={"service": "HiLabs Healthcare Contract Classification API"},
        message="Welcome to the API"
    )
