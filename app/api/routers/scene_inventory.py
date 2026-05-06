from uuid import UUID
from fastapi import APIRouter, Depends, Request

from app.api.schemas.scene_inventory import SceneInventoryResponse
from app.application.generations.analyze_scene import AnalyzeSceneUseCase
from app.application.generations.get_scene_inventory import GetSceneInventoryUseCase

# We will mount this onto images_router
router = APIRouter(prefix="/images/{image_id}/scene-inventory", tags=["Scene Inventory"])

from app.api.dependencies import get_analyze_scene_uc, get_get_scene_inventory_uc

@router.post("", response_model=SceneInventoryResponse, status_code=202)
async def analyze_scene(
    image_id: UUID,
    request: Request,
    use_case: AnalyzeSceneUseCase = Depends(get_analyze_scene_uc)
):
    correlation_id = request.headers.get("X-Correlation-ID")
    inventory = await use_case.execute(image_id, correlation_id)
    return SceneInventoryResponse.from_entity(inventory)

@router.get("", response_model=SceneInventoryResponse)
async def get_scene_inventory(
    image_id: UUID,
    use_case: GetSceneInventoryUseCase = Depends(get_get_scene_inventory_uc)
):
    inventory = await use_case.execute(image_id)
    return SceneInventoryResponse.from_entity(inventory)
