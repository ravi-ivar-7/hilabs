from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import get_settings
from .core.database import init_db
from .core.logging import setup_logging, get_logger
from .api import health_router, contracts_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting up...")
    init_db()
    yield
    logger.info("Shutting down...")


def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title="HiLabs Healthcare Contract Classification API",
        description="Backend API for healthcare contract classification system",
        version="1.0.0",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(health_router, prefix="/api/v1", tags=["health"])
    app.include_router(contracts_router, prefix="/api/v1/contracts", tags=["contracts"])
    
    @app.get("/")
    async def root():
        return {
            "message": "HiLabs Healthcare Contract Classification API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/api/v1/health",
                "database_health": "/api/v1/health/database", 
                "storage_health": "/api/v1/health/storage",
                "upload_contract": "POST /api/v1/contracts/upload",
                "contract_status": "GET /api/v1/contracts/{id}/status",
                "contract_results": "GET /api/v1/contracts/{id}/results",
                "contract_details": "GET /api/v1/contracts/{id}",
                "documentation": "/docs"
            }
        }
    
    return app


app = create_app()
