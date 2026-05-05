# Dependencies for FastAPI DI

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.database import get_session
from app.infrastructure.persistence.projects.sqlalchemy_repository import SQLAlchemyProjectRepository
from app.application.projects.create_project import CreateProjectUseCase
from app.application.projects.get_project import GetProjectUseCase
from app.application.projects.list_projects import ListProjectsUseCase
from app.application.projects.update_project import UpdateProjectUseCase
from app.application.projects.delete_project import DeleteProjectUseCase

def get_create_project_uc(session: AsyncSession = Depends(get_session)) -> CreateProjectUseCase:
    repo = SQLAlchemyProjectRepository(session)
    return CreateProjectUseCase(project_repo=repo)

def get_get_project_uc(session: AsyncSession = Depends(get_session)) -> GetProjectUseCase:
    repo = SQLAlchemyProjectRepository(session)
    return GetProjectUseCase(project_repo=repo)

def get_list_projects_uc(session: AsyncSession = Depends(get_session)) -> ListProjectsUseCase:
    repo = SQLAlchemyProjectRepository(session)
    return ListProjectsUseCase(project_repo=repo)

def get_update_project_uc(session: AsyncSession = Depends(get_session)) -> UpdateProjectUseCase:
    repo = SQLAlchemyProjectRepository(session)
    return UpdateProjectUseCase(project_repo=repo)

def get_delete_project_uc(session: AsyncSession = Depends(get_session)) -> DeleteProjectUseCase:
    repo = SQLAlchemyProjectRepository(session)
    return DeleteProjectUseCase(project_repo=repo)
