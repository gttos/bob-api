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
    def side_effect(p):
        return p
    mock_repo.save.side_effect = side_effect

    use_case = CreateProjectUseCase(project_repo=mock_repo)
    result = await use_case.execute(CreateProjectCommand(name="Test Project", description="Desc"))

    mock_repo.save.assert_called_once()
    assert result.name == "Test Project"
    assert result.description == "Desc"


@pytest.mark.asyncio
async def test_get_project_success():
    mock_repo = AsyncMock()
    project = Project(name="Test Project", description="Desc")
    mock_repo.get_by_id.return_value = project

    use_case = GetProjectUseCase(project_repo=mock_repo)
    result = await use_case.execute(project.id)

    mock_repo.get_by_id.assert_called_once_with(project.id)
    assert result == project


@pytest.mark.asyncio
async def test_get_project_not_found():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    use_case = GetProjectUseCase(project_repo=mock_repo)
    project_id = uuid4()
    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(project_id)


@pytest.mark.asyncio
async def test_list_projects_success():
    mock_repo = AsyncMock()
    project = Project(name="Test Project", description="Desc")
    mock_repo.list_all.return_value = [project]
    mock_repo.count.return_value = 1

    use_case = ListProjectsUseCase(project_repo=mock_repo)
    result = await use_case.execute(page=1, page_size=20)

    mock_repo.list_all.assert_called_once_with(offset=0, limit=20)
    mock_repo.count.assert_called_once()
    assert result.items == [project]
    assert result.total == 1


@pytest.mark.asyncio
async def test_update_project_success():
    mock_repo = AsyncMock()
    project = Project(name="Test Project", description="Desc")
    mock_repo.get_by_id.return_value = project
    def side_effect(p):
        return p
    mock_repo.save.side_effect = side_effect

    use_case = UpdateProjectUseCase(project_repo=mock_repo)
    result = await use_case.execute(UpdateProjectCommand(project_id=project.id, name="Updated", description="Updated Desc"))

    mock_repo.get_by_id.assert_called_once_with(project.id)
    mock_repo.save.assert_called_once_with(project)
    assert result.name == "Updated"
    assert result.description == "Updated Desc"


@pytest.mark.asyncio
async def test_update_project_not_found():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    use_case = UpdateProjectUseCase(project_repo=mock_repo)
    project_id = uuid4()
    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(UpdateProjectCommand(project_id=project_id, name="Updated"))


@pytest.mark.asyncio
async def test_delete_project_success():
    mock_repo = AsyncMock()
    project = Project(name="Test Project", description="Desc")
    mock_repo.get_by_id.return_value = project

    use_case = DeleteProjectUseCase(project_repo=mock_repo)
    await use_case.execute(project.id)

    mock_repo.get_by_id.assert_called_once_with(project.id)
    mock_repo.delete.assert_called_once_with(project.id)


@pytest.mark.asyncio
async def test_delete_project_not_found():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    use_case = DeleteProjectUseCase(project_repo=mock_repo)
    project_id = uuid4()
    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(project_id)
