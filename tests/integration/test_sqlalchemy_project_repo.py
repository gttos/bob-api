import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import configure_mappers

from app.domain.projects.entities import Project
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.projects.sqlalchemy_repository import SQLAlchemyProjectRepository

# This is necessary because of the use_alter issue with Circular references in SQLAlchemy Models
from app.infrastructure.persistence.models import ProjectModel
try:
    configure_mappers()
except Exception:
    pass

@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

@pytest.mark.asyncio
async def test_save_and_get_project(session):
    repo = SQLAlchemyProjectRepository(session)
    project = Project(name="Test")

    saved = await repo.save(project)
    retrieved = await repo.get_by_id(saved.id)

    assert retrieved is not None
    assert retrieved.name == "Test"
    assert retrieved.id == project.id

@pytest.mark.asyncio
async def test_list_and_count_projects(session):
    repo = SQLAlchemyProjectRepository(session)
    p1 = Project(name="P1")
    p2 = Project(name="P2")

    await repo.save(p1)
    await repo.save(p2)

    count = await repo.count()
    assert count == 2

    projects = await repo.list_all()
    assert len(projects) == 2

    names = [p.name for p in projects]
    assert "P1" in names
    assert "P2" in names

@pytest.mark.asyncio
async def test_delete_project(session):
    repo = SQLAlchemyProjectRepository(session)
    project = Project(name="Test")

    saved = await repo.save(project)
    await repo.delete(saved.id)

    retrieved = await repo.get_by_id(saved.id)
    assert retrieved is None
