from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request
from typing import Optional

from app.api.schemas.generations import GenerationRequestCreate, GenerationRequestResponse
from app.api.schemas.shared import PaginatedResponse
from app.application.generations.request_generation import RequestGenerationUseCase, RequestGenerationCommand
from app.application.generations.get_generation import GetGenerationUseCase
from app.application.generations.list_generations import ListGenerationsUseCase
from app.domain.generations.entities import GenerationMode

# Need these dependencies defined later in app/api/dependencies.py
from app.api.dependencies import (
    get_request_generation_uc,
    get_get_generation_uc,
    get_list_generations_uc
)

# Shared routers
# Add POST and GET list endpoints to images router
# Since app/api/routers/images.py already has an `images_router`
# We'll just define the routes here and include this router in main.py
# under the same /images and /generations paths.

images_generations_router = APIRouter(prefix="/images/{image_id}/generations", tags=["Generations"])
generations_router = APIRouter(prefix="/generations", tags=["Generations"])

@images_generations_router.post("", response_model=GenerationRequestResponse, status_code=202)
async def request_generation(
    image_id: UUID,
    request_data: GenerationRequestCreate,
    request: Request,
    use_case: RequestGenerationUseCase = Depends(get_request_generation_uc)
):
    correlation_id = request.headers.get("X-Correlation-ID")

    try:
        mode = GenerationMode(request_data.mode)
    except ValueError:
        from app.domain.shared.exceptions import DomainValidationError
        raise DomainValidationError(f"Invalid mode: {request_data.mode}")

    command = RequestGenerationCommand(
        image_id=image_id,
        mode=mode,
        provider=request_data.provider,
        preset=request_data.preset,
        instructions=request_data.instructions
    )

    result = await use_case.execute(command, correlation_id=correlation_id)
    return GenerationRequestResponse.from_entity(result)

@images_generations_router.get("", response_model=PaginatedResponse[GenerationRequestResponse])
async def list_generations(
    image_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_case: ListGenerationsUseCase = Depends(get_list_generations_uc)
):
    result = await use_case.execute(image_id=image_id, page=page, page_size=page_size)
    items = [GenerationRequestResponse.from_entity(item) for item in result.items]

    return PaginatedResponse(
        items=items,
        total=result.total,
        page=page,
        page_size=page_size
    )

@generations_router.get("/{generation_id}", response_model=GenerationRequestResponse)
async def get_generation(
    generation_id: UUID,
    use_case: GetGenerationUseCase = Depends(get_get_generation_uc)
):
    result = await use_case.execute(generation_id)
    return GenerationRequestResponse.from_entity(result)
