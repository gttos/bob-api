from hypothesis import given, settings
from hypothesis import strategies as st
from unittest.mock import AsyncMock
import pytest

from app.application.projects.create_project import CreateProjectUseCase, CreateProjectCommand
from app.application.projects.update_project import UpdateProjectUseCase, UpdateProjectCommand
from app.domain.projects.entities import Project

@given(
    name=st.text(
        min_size=1,
        max_size=255,
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
    ),
    description=st.one_of(st.none(), st.text(max_size=500)),
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
    original_name=st.text(min_size=1, max_size=100),
    original_desc=st.text(max_size=200),
    new_name=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
)
@settings(max_examples=100)
@pytest.mark.asyncio
async def test_update_preserves_unmodified_fields(original_name, original_desc, new_name):
    """Propiedad 2: Partial update de Proyecto"""
    project = Project(name=original_name, description=original_desc)
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = project
    mock_repo.save.side_effect = lambda p: p

    use_case = UpdateProjectUseCase(project_repo=mock_repo)
    result = await use_case.execute(UpdateProjectCommand(
        project_id=project.id,
        name=new_name,
    ))

    if new_name is None:
        assert result.name == original_name
    else:
        assert result.name == new_name

    assert result.description == original_desc
