from uuid import UUID
from fastapi import APIRouter, Depends, Response

from app.api.schemas.spaces import SpaceCreate, SpaceResponse
from app.application.spaces.create_space import CreateSpaceUseCase, CreateSpaceCommand
from app.application.spaces.list_spaces import ListSpacesUseCase
from app.application.spaces.delete_space import DeleteSpaceUseCase
from app.api.dependencies import get_create_space_uc, get_list_spaces_uc, get_delete_space_uc

project_spaces_router = APIRouter(prefix="/projects/{project_id}/spaces", tags=["Spaces"])
spaces_router = APIRouter(prefix="/spaces", tags=["Spaces"])

@project_spaces_router.post("", response_model=SpaceResponse, status_code=201)
async def create_space(
    project_id: UUID,
    schema: SpaceCreate,
    use_case: CreateSpaceUseCase = Depends(get_create_space_uc)
):
    command = CreateSpaceCommand(
        project_id=project_id,
        name=schema.name,
        description=schema.description
    )
    space = await use_case.execute(command)
    return SpaceResponse.from_entity(space)

@project_spaces_router.get("", response_model=list[SpaceResponse])
async def list_spaces(
    project_id: UUID,
    use_case: ListSpacesUseCase = Depends(get_list_spaces_uc)
):
    spaces = await use_case.execute(project_id)
    return [SpaceResponse.from_entity(s) for s in spaces]

@spaces_router.delete("/{space_id}", status_code=204)
async def delete_space(
    space_id: UUID,
    use_case: DeleteSpaceUseCase = Depends(get_delete_space_uc)
):
    await use_case.execute(space_id)
    return Response(status_code=204)
