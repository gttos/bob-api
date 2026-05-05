from uuid import UUID
from fastapi import APIRouter, Depends, status, Query

from app.api.dependencies import (
    get_create_project_uc,
    get_get_project_uc,
    get_list_projects_uc,
    get_update_project_uc,
    get_delete_project_uc,
)
from app.api.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse
from app.api.schemas.pagination import PaginatedResponse
from app.application.projects.create_project import CreateProjectUseCase, CreateProjectCommand
from app.application.projects.get_project import GetProjectUseCase
from app.application.projects.list_projects import ListProjectsUseCase
from app.application.projects.update_project import UpdateProjectUseCase, UpdateProjectCommand
from app.application.projects.delete_project import DeleteProjectUseCase

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    use_case: CreateProjectUseCase = Depends(get_create_project_uc)
):
    command = CreateProjectCommand(name=data.name, description=data.description)
    project = await use_case.execute(command)
    return ProjectResponse.from_entity(project)


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_case: ListProjectsUseCase = Depends(get_list_projects_uc)
):
    result = await use_case.execute(page=page, page_size=page_size)
    return PaginatedResponse(
        items=[ProjectResponse.from_entity(p) for p in result.items],
        total=result.total,
        page=page,
        page_size=page_size
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    use_case: GetProjectUseCase = Depends(get_get_project_uc)
):
    project = await use_case.execute(project_id)
    return ProjectResponse.from_entity(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    use_case: UpdateProjectUseCase = Depends(get_update_project_uc)
):
    command = UpdateProjectCommand(
        project_id=project_id,
        name=data.name,
        description=data.description
    )
    project = await use_case.execute(command)
    return ProjectResponse.from_entity(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    use_case: DeleteProjectUseCase = Depends(get_delete_project_uc)
):
    await use_case.execute(project_id)
