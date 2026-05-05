from hypothesis import given, settings
from hypothesis import strategies as st
from unittest.mock import AsyncMock
import pytest

from app.application.projects.create_project import CreateProjectUseCase, CreateProjectCommand
from app.application.projects.update_project import UpdateProjectUseCase, UpdateProjectCommand
from app.domain.projects.entities import Project

@given(
    name=st.text(min_size=1, max_size=255),
    description=st.one_of(st.none(), st.text(max_size=1000)),
)
@settings(max_examples=100)
@pytest.mark.asyncio
async def test_create_project_round_trip(name, description):
    """Propiedad 1: Round-trip de Proyecto (crear → obtener)"""
    mock_repo = AsyncMock()
    mock_repo.save.side_effect = lambda p: p
    use_case = CreateProjectUseCase(project_repo=mock_repo)

    result = await use_case.execute(CreateProjectCommand(name=name, description=description))

    assert result.name == name
    assert result.description == description
    assert result.id is not None
    assert result.created_at is not None

@given(
    initial_name=st.text(min_size=1, max_size=255),
    initial_desc=st.one_of(st.none(), st.text(max_size=1000)),
    update_name=st.one_of(st.none(), st.text(min_size=1, max_size=255)),
    update_desc=st.one_of(st.none(), st.text(max_size=1000)),
)
@settings(max_examples=100)
@pytest.mark.asyncio
async def test_update_project_partial(initial_name, initial_desc, update_name, update_desc):
    """Propiedad 2: Partial update de Proyecto"""
    project = Project(name=initial_name, description=initial_desc)
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = project
    mock_repo.save.side_effect = lambda p: p

    use_case = UpdateProjectUseCase(project_repo=mock_repo)
    result = await use_case.execute(UpdateProjectCommand(
        project_id=project.id,
        name=update_name,
        description=update_desc
    ))

    if update_name is not None:
        assert result.name == update_name
    else:
        assert result.name == initial_name

    if update_desc is not None:
        assert result.description == update_desc
    else:
        assert result.description == initial_desc
