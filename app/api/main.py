import os
from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config.settings import settings
from app.config.logging import configure_logging
from app.api.middleware.correlation import CorrelationIDMiddleware
from app.api.middleware.request_logging import RequestLoggingMiddleware
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.api.routers.health import router as health_router
from app.api.routers.projects import router as projects_router
from app.api.routers.images import project_images_router, images_router
from app.api.routers.generations import images_generations_router, generations_router
from app.api.routers.scene_inventory import router as scene_inventory_router
from app.api.routers.evaluations import router as evaluations_router
from app.api.routers.stats import router as stats_router
from app.domain.shared.exceptions import (
    DomainError,

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
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CorrelationIDMiddleware)

# Mount Static Files
os.makedirs(settings.STORAGE_LOCAL_PATH, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.STORAGE_LOCAL_PATH), name="media")

# Setup Main API Router
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(projects_router)
api_router.include_router(project_images_router)
api_router.include_router(images_router)
api_router.include_router(images_generations_router)
api_router.include_router(generations_router)
api_router.include_router(scene_inventory_router)
api_router.include_router(evaluations_router)
api_router.include_router(stats_router)

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

@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    # Just generic fallback, some like DomainValidationError have specific handlers
    if isinstance(exc, (ResourceNotFoundError, InvalidStateTransitionError, DomainValidationError, DuplicateResourceError)):
        raise exc
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(DuplicateResourceError)
async def duplicate_resource_handler(request: Request, exc: DuplicateResourceError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})
