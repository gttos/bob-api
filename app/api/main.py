import os
from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config.settings import settings
from app.config.logging import configure_logging
from app.api.middleware.correlation import CorrelationIDMiddleware
from app.api.routers.health import router as health_router
from app.api.routers.projects import router as projects_router
from app.domain.shared.exceptions import (
    ResourceNotFoundError,
    InvalidStateTransitionError,
    DomainValidationError,
    DuplicateResourceError,
)

# Configure structlog
configure_logging()

app = FastAPI(
    title="Interior AI Backend",
    version="1.0.0",
)

# Global Middlewares
app.add_middleware(CorrelationIDMiddleware)

# Mount Static Files
os.makedirs(settings.STORAGE_LOCAL_PATH, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.STORAGE_LOCAL_PATH), name="media")

# Setup Main API Router
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(projects_router)

# Register API Router
app.include_router(api_router)

# Exception Handlers
@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(InvalidStateTransitionError)
async def invalid_state_transition_handler(request: Request, exc: InvalidStateTransitionError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})

@app.exception_handler(DomainValidationError)
async def domain_validation_handler(request: Request, exc: DomainValidationError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(DuplicateResourceError)
async def duplicate_resource_handler(request: Request, exc: DuplicateResourceError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})
