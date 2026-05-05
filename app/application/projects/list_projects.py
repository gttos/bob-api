from dataclasses import dataclass

from app.application.ports.repository_ports import ProjectRepository
from app.domain.projects.entities import Project


@dataclass
class ListProjectsResult:
    items: list[Project]
    total: int


class ListProjectsUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self._project_repo = project_repo

    async def execute(self, page: int = 1, page_size: int = 20) -> ListProjectsResult:
        offset = (page - 1) * page_size
        items = await self._project_repo.list_all(offset=offset, limit=page_size)
        total = await self._project_repo.count()
        return ListProjectsResult(items=items, total=total)
