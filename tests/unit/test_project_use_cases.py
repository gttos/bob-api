import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.application.projects.create_project import CreateProjectUseCase, CreateProjectCommand
from app.application.projects.get_project import GetProjectUseCase
from app.application.projects.list_projects import ListProjectsUseCase
from app.application.projects.update_project import UpdateProjectUseCase, UpdateProjectCommand
from app.application.projects.delete_project import DeleteProjectUseCase
from app.domain.projects.entities import Project
from app.domain.shared.exceptions import ResourceNotFoundError


@pytest.mark.asyncio
async def test_create_project_saves_and_returns():
    mock_repo = AsyncMock()
    mock_repo.save.side_effect = lambda p: p

    use_case = CreateProjectUseCase(project_repo=mock_repo)
    result = await use_case.execute(CreateProjectCommand(name="Test", description="Desc"))

    mock_repo.save.assert_called_once()
    assert result.name == "Test"
    assert result.description == "Desc"


@pytest.mark.asyncio
async def test_get_project_returns_project():
    mock_repo = AsyncMock()
    project = Project(name="Test Project", description="Desc")
    mock_repo.get_by_id.return_value = project

    use_case = GetProjectUseCase(project_repo=mock_repo)
    result = await use_case.execute(project.id)

    assert result == project


@pytest.mark.asyncio
async def test_get_project_raises_not_found():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    use_case = GetProjectUseCase(project_repo=mock_repo)
    project_id = uuid4()
    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(project_id)


@pytest.mark.asyncio
async def test_update_project_only_changes_provided_fields():
    mock_repo = AsyncMock()
    project = Project(name="Original", description="Original desc")
    mock_repo.get_by_id.return_value = project
    mock_repo.save.side_effect = lambda p: p

    use_case = UpdateProjectUseCase(project_repo=mock_repo)
    result = await use_case.execute(UpdateProjectCommand(project_id=project.id, name="New name"))

    assert result.name == "New name"
    assert result.description == "Original desc"


@pytest.mark.asyncio
async def test_delete_project_raises_not_found():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    use_case = DeleteProjectUseCase(project_repo=mock_repo)
    project_id = uuid4()
    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(project_id)


@pytest.mark.asyncio
async def test_list_projects_returns_paginated_result():
    mock_repo = AsyncMock()
    p1 = Project(name="Test 1")
    p2 = Project(name="Test 2")
    mock_repo.list_all.return_value = [p1, p2]
    mock_repo.count.return_value = 5

    use_case = ListProjectsUseCase(project_repo=mock_repo)
    result = await use_case.execute(page=1, page_size=2)

    assert len(result.items) == 2
    assert result.total == 5
