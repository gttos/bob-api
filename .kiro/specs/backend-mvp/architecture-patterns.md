# Patrones de Arquitectura — Backend MVP

Este documento es la referencia de patrones que **todo el código del backend debe seguir**. Es el contrato arquitectónico que Jules debe respetar al implementar cada tarea.

---

## 1. Arquitectura Hexagonal (Ports & Adapters)

### Regla de Dependencias

Las dependencias **solo apuntan hacia adentro**:

```
Infraestructura → Aplicación → Dominio
```

- El **dominio** no importa nada de aplicación, infraestructura ni frameworks.
- La **aplicación** importa del dominio y define puertos (interfaces). No importa de infraestructura.
- La **infraestructura** importa de aplicación y dominio para implementar los puertos.

### Verificación rápida

Si un archivo en `app/domain/` tiene un `import` de `app/infrastructure/`, `app/api/`, `sqlalchemy`, `fastapi`, `celery` o `openai` → **es un error arquitectónico**.

Si un archivo en `app/application/` tiene un `import` de `app/infrastructure/`, `sqlalchemy`, `fastapi`, `celery` o `openai` → **es un error arquitectónico**.

---

## 2. Entidades de Dominio

### Reglas

- Las entidades son **dataclasses Python puras**. Sin herencia de SQLAlchemy, Pydantic ni ningún ORM.
- Contienen **lógica de negocio** (validaciones, transiciones de estado, invariantes).
- Los IDs son `UUID` generados en el dominio, no en la base de datos.
- Los timestamps son `datetime` de Python, no columnas de BD.

### Patrón: Transiciones de Estado con Validación

```python
# CORRECTO: la entidad valida sus propias transiciones
@dataclass
class GenerationRequest:
    status: GenerationStatus = GenerationStatus.PENDING

    def transition_to(self, new_status: GenerationStatus) -> None:
        if not self.status.can_transition_to(new_status):
            raise InvalidStateTransitionError(f"{self.status} → {new_status}")
        self.status = new_status

# INCORRECTO: lógica de transición fuera de la entidad
generation.status = "generating"  # No hacer esto
```

### Patrón: Value Objects para tipos con semántica

```python
# CORRECTO: usar value objects para tipos con reglas
@dataclass(frozen=True)
class GenerationMode(str, Enum):
    COMMERCIAL_ENHANCEMENT = "commercial_enhancement"
    STYLE_REDESIGN = "style_redesign"
    FUNCTIONAL_VARIANT = "functional_variant"
    LOCALIZED_EDIT = "localized_edit"

# INCORRECTO: strings sueltos
mode = "commercial_enhancement"  # Sin validación, sin semántica
```

---

## 3. Puertos (Interfaces)

### Reglas

- Los puertos se definen en `app/application/ports/`.
- Son clases abstractas (`ABC`) con métodos abstractos.
- Los nombres terminan en `Port` o `Repository`.
- Los métodos son `async` cuando la implementación típica es I/O.

### Patrón: Puerto de Repositorio

```python
# app/application/ports/repository_ports.py
from abc import ABC, abstractmethod
from uuid import UUID

class ProjectRepository(ABC):
    @abstractmethod
    async def save(self, project: Project) -> Project: ...

    @abstractmethod
    async def get_by_id(self, project_id: UUID) -> Project | None: ...

    @abstractmethod
    async def list_all(self) -> list[Project]: ...

    @abstractmethod
    async def delete(self, project_id: UUID) -> None: ...
```

### Patrón: Puerto de Servicio Externo

```python
# app/application/ports/ai_provider_port.py
class AIProviderPort(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def generate_variant(self, image: bytes, prompt_result: PromptResult) -> GenerationResult: ...

    @abstractmethod
    async def analyze_scene(self, image: bytes) -> SceneInventoryData: ...
```

---

## 4. Casos de Uso (Use Cases)

### Reglas

- Un caso de uso por archivo, en `app/application/{dominio}/`.
- Cada use case tiene un método `execute()`.
- Recibe un **Command** (para escrituras) o parámetros simples (para lecturas).
- Retorna una entidad de dominio o un resultado simple.
- **No conoce HTTP, SQL, Celery ni ningún framework**.
- Las dependencias se inyectan en el constructor.

### Patrón: Command + Use Case

```python
# app/application/projects/create_project.py
from dataclasses import dataclass
from app.domain.projects.entities import Project
from app.application.ports.repository_ports import ProjectRepository

@dataclass
class CreateProjectCommand:
    name: str
    description: str | None = None

class CreateProjectUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self._repo = project_repo

    async def execute(self, command: CreateProjectCommand) -> Project:
        project = Project(name=command.name, description=command.description)
        return await self._repo.save(project)
```

### Patrón: Use Case con múltiples puertos

```python
class ProcessGenerationUseCase:
    def __init__(
        self,
        generation_repo: GenerationRepository,
        image_repo: ImageRepository,
        storage: StoragePort,
        ai_provider_registry: AIProviderRegistry,
        prompt_builder: PromptBuilder,
    ):
        self._generation_repo = generation_repo
        self._image_repo = image_repo
        self._storage = storage
        self._ai_registry = ai_provider_registry
        self._prompt_builder = prompt_builder

    async def execute(self, generation_request_id: UUID) -> None:
        request = await self._generation_repo.get_by_id(generation_request_id)
        if not request:
            raise ResourceNotFoundError(...)

        try:
            request.transition_to(GenerationStatus.ANALYZING)
            await self._generation_repo.save(request)

            image = await self._image_repo.get_by_id(request.source_image_id)
            image_data = await self._storage.download(image.storage_path)

            prompt_result = self._prompt_builder.build(PromptConfig(...))

            request.transition_to(GenerationStatus.GENERATING)
            await self._generation_repo.save(request)

            provider = self._ai_registry.get(request.provider)
            result = await provider.generate_variant(image_data, prompt_result)

            # ... guardar resultado, crear variante, etc.

            request.transition_to(GenerationStatus.COMPLETED)
            await self._generation_repo.save(request)

        except Exception as e:
            request.mark_failed(str(e))
            await self._generation_repo.save(request)
            raise
```

---

## 5. Adaptadores de Repositorio (SQLAlchemy)

### Reglas

- Los modelos SQLAlchemy viven en `app/infrastructure/persistence/models.py`.
- Son **completamente separados** de las entidades de dominio.
- Cada repositorio implementa su puerto correspondiente.
- El repositorio traduce entre entidades de dominio y modelos ORM con métodos `_to_entity()` y `_to_model()`.
- **Nunca** se expone un modelo SQLAlchemy fuera de la capa de infraestructura.

### Patrón: Repositorio con traducción

```python
class SQLAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, project: Project) -> Project:
        # Buscar si existe para decidir insert vs update
        existing = await self._session.get(ProjectModel, project.id)
        if existing:
            existing.name = project.name
            existing.description = project.description
            existing.updated_at = project.updated_at
            model = existing
        else:
            model = self._to_model(project)
            self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    def _to_entity(self, model: ProjectModel) -> Project:
        return Project(
            id=model.id,
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Project) -> ProjectModel:
        return ProjectModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
```

---

## 6. Adaptadores HTTP (FastAPI Routers)

### Reglas

- Los routers son **adaptadores primarios**. Solo traducen HTTP ↔ use cases.
- No contienen lógica de negocio.
- Traducen excepciones de dominio a respuestas HTTP.
- Los schemas Pydantic (DTOs) viven en `app/api/schemas/` y son distintos de las entidades de dominio.
- Los schemas tienen métodos `from_entity()` para construirse desde entidades de dominio.

### Patrón: Router como adaptador

```python
# app/api/routers/projects.py
router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: ProjectCreate,
    use_case: CreateProjectUseCase = Depends(get_create_project_uc),
):
    # 1. Traducir HTTP body → Command
    command = CreateProjectCommand(name=body.name, description=body.description)
    # 2. Ejecutar use case
    project = await use_case.execute(command)
    # 3. Traducir entidad → HTTP response
    return ProjectResponse.from_entity(project)
```

### Patrón: Manejo de excepciones de dominio

```python
# app/api/main.py — exception handlers globales
@app.exception_handler(ResourceNotFoundError)
async def not_found_handler(request: Request, exc: ResourceNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(InvalidStateTransitionError)
async def invalid_state_handler(request: Request, exc: InvalidStateTransitionError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})

@app.exception_handler(DomainValidationError)
async def validation_handler(request: Request, exc: DomainValidationError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})
```

### Patrón: Schema con from_entity

```python
# app/api/schemas/projects.py
class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, project: Project) -> "ProjectResponse":
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
```

---

## 7. Inyección de Dependencias

### Reglas

- Las dependencias se resuelven en `app/api/dependencies.py`.
- Cada use case se construye con sus dependencias concretas en este archivo.
- Se usa el sistema de DI de FastAPI (`Depends`).
- La sesión de base de datos se inyecta por request (scoped to request).

### Patrón: Wiring de dependencias

```python
# app/api/dependencies.py
from functools import lru_cache
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.database import get_session
from app.infrastructure.persistence.projects.sqlalchemy_repository import SQLAlchemyProjectRepository
from app.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from app.infrastructure.ai_providers.openai_provider import OpenAIProvider
from app.application.projects.create_project import CreateProjectUseCase
from app.config.settings import Settings, get_settings

# Storage — singleton (stateless)
@lru_cache
def get_storage_adapter(settings: Settings = Depends(get_settings)) -> LocalStorageAdapter:
    return LocalStorageAdapter(
        base_path=settings.STORAGE_LOCAL_PATH,
        media_url_prefix=settings.MEDIA_URL_PREFIX,
    )

# Use case — por request (tiene sesión de BD)
def get_create_project_uc(
    session: AsyncSession = Depends(get_session),
) -> CreateProjectUseCase:
    repo = SQLAlchemyProjectRepository(session)
    return CreateProjectUseCase(project_repo=repo)
```

---

## 8. Adaptadores de Workers (Celery)

### Reglas

- Las tareas Celery son **adaptadores primarios**, igual que los routers HTTP.
- No contienen lógica de negocio.
- Resuelven sus dependencias manualmente (sin FastAPI DI) usando el contenedor de configuración.
- Invocan use cases de la capa de aplicación.
- Manejan errores a nivel de tarea (retry, logging), pero la lógica de `mark_failed` está en el use case.

### Patrón: Tarea Celery como adaptador

```python
# app/infrastructure/tasks/celery_tasks.py
from app.infrastructure.tasks.celery_app import celery_app
from app.infrastructure.persistence.database import get_sync_session
from app.infrastructure.persistence.generations.sqlalchemy_repository import SQLAlchemyGenerationRepository
from app.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from app.infrastructure.ai_providers.openai_provider import OpenAIProvider
from app.application.generations.process_generation import ProcessGenerationUseCase
from app.config.settings import get_settings

@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def process_generation(self, generation_request_id: str):
    settings = get_settings()
    with get_sync_session() as session:
        # Resolver dependencias manualmente
        use_case = ProcessGenerationUseCase(
            generation_repo=SQLAlchemyGenerationRepository(session),
            image_repo=SQLAlchemyImageRepository(session),
            storage=LocalStorageAdapter(settings.STORAGE_LOCAL_PATH, settings.MEDIA_URL_PREFIX),
            ai_provider_registry=build_ai_registry(settings),
            prompt_builder=PromptBuilder(),
        )
        try:
            # Ejecutar use case (maneja toda la lógica incluyendo mark_failed)
            import asyncio
            asyncio.run(use_case.execute(UUID(generation_request_id)))
        except Exception as exc:
            # Solo reintentar errores transitorios
            if is_transient_error(exc):
                raise self.retry(exc=exc)
            # El use case ya marcó el estado como failed
            logger.error("Generation task failed permanently", exc_info=True)
```

---

## 9. Excepciones de Dominio

### Jerarquía

```python
# app/domain/shared/exceptions.py

class DomainError(Exception):
    """Base para todas las excepciones de dominio."""

class ResourceNotFoundError(DomainError):
    """Recurso no encontrado."""

class InvalidStateTransitionError(DomainError):
    """Transición de estado inválida en una entidad."""

class DomainValidationError(DomainError):
    """Violación de una regla de negocio."""

class DuplicateResourceError(DomainError):
    """Intento de crear un recurso que ya existe."""
```

### Reglas

- Las excepciones de dominio se lanzan desde entidades y use cases.
- Los adaptadores (routers, workers) las capturan y traducen al mecanismo de error correspondiente (HTTP status, log, retry).
- **Nunca** lanzar excepciones de infraestructura (SQLAlchemy, httpx, etc.) desde el dominio.

---

## 10. Testing con Arquitectura Hexagonal

### Ventaja principal

La arquitectura hexagonal hace que el testing sea trivial: los use cases se testean con mocks de los puertos, sin necesidad de base de datos ni servicios externos.

### Patrón: Test de Use Case con mocks

```python
# tests/unit/test_create_project.py
import pytest
from unittest.mock import AsyncMock
from app.application.projects.create_project import CreateProjectUseCase, CreateProjectCommand
from app.domain.projects.entities import Project

@pytest.mark.asyncio
async def test_create_project_saves_and_returns():
    # Arrange
    mock_repo = AsyncMock()
    mock_repo.save.return_value = Project(name="Test Project", description="Desc")
    use_case = CreateProjectUseCase(project_repo=mock_repo)

    # Act
    result = await use_case.execute(CreateProjectCommand(name="Test Project", description="Desc"))

    # Assert
    mock_repo.save.assert_called_once()
    assert result.name == "Test Project"
```

### Patrón: Test de Propiedad con mocks

```python
# tests/properties/test_project_properties.py
from hypothesis import given, settings
from hypothesis import strategies as st
from unittest.mock import AsyncMock

@given(
    name=st.text(min_size=1, max_size=255),
    description=st.one_of(st.none(), st.text(max_size=1000)),
)
@settings(max_examples=100)
async def test_create_project_round_trip(name, description):
    """Propiedad 1: Round-trip de Proyecto (crear → obtener)"""
    mock_repo = AsyncMock()
    # El mock retorna lo que recibe (simula persistencia)
    mock_repo.save.side_effect = lambda p: p
    use_case = CreateProjectUseCase(project_repo=mock_repo)

    result = await use_case.execute(CreateProjectCommand(name=name, description=description))

    assert result.name == name
    assert result.description == description
    assert result.id is not None
    assert result.created_at is not None
```

### Patrón: Test de Adaptador con base de datos real

```python
# tests/integration/test_sqlalchemy_project_repo.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
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
```

---

## 11. Convenciones de Nomenclatura

| Elemento | Convención | Ejemplo |
|---|---|---|
| Entidades de dominio | PascalCase, sustantivo | `Project`, `GenerationRequest` |
| Value Objects | PascalCase, descriptivo | `GenerationMode`, `EvaluationVerdict` |
| Puertos | PascalCase + `Port` o `Repository` | `StoragePort`, `ProjectRepository` |
| Use Cases | PascalCase + `UseCase` | `CreateProjectUseCase` |
| Commands | PascalCase + `Command` | `CreateProjectCommand` |
| Adaptadores | PascalCase + tecnología | `SQLAlchemyProjectRepository`, `LocalStorageAdapter` |
| Schemas API | PascalCase + `Request`/`Response`/`Create`/`Update` | `ProjectResponse`, `ProjectCreate` |
| Excepciones | PascalCase + `Error` | `ResourceNotFoundError` |
| Archivos | snake_case | `create_project.py`, `sqlalchemy_repository.py` |

---

## 12. Checklist de Revisión Arquitectónica

Antes de considerar una tarea completa, verificar:

- [ ] Las entidades de dominio no importan de infraestructura ni frameworks
- [ ] Los use cases no importan de infraestructura ni frameworks
- [ ] Los puertos están definidos como clases abstractas en `app/application/ports/`
- [ ] Los adaptadores implementan los puertos correspondientes
- [ ] Los routers FastAPI solo traducen HTTP ↔ use cases (sin lógica de negocio)
- [ ] Las tareas Celery solo invocan use cases (sin lógica de negocio)
- [ ] Los modelos SQLAlchemy están separados de las entidades de dominio
- [ ] Las excepciones de dominio se lanzan desde el dominio y se capturan en los adaptadores
- [ ] Los tests de use cases usan mocks de los puertos (sin BD real)
- [ ] Los tests de adaptadores usan implementaciones reales (BD en memoria o local)

---

## 13. Paginación

Todos los endpoints de listado usan offset/limit con una respuesta paginada estándar.

### Patrón: Response paginada

```python
# app/api/schemas/pagination.py
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass
class PaginatedResponse(Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

# Uso en router
@router.get("/", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_case=Depends(get_list_projects_uc),
):
    result = await use_case.execute(page=page, page_size=page_size)
    return PaginatedResponse(
        items=[ProjectResponse.from_entity(p) for p in result.items],
        total=result.total,
        page=page,
        page_size=page_size,
    )
```

### Patrón: Use case con paginación

```python
@dataclass
class ListProjectsResult:
    items: list[Project]
    total: int

class ListProjectsUseCase:
    async def execute(self, page: int = 1, page_size: int = 20) -> ListProjectsResult:
        offset = (page - 1) * page_size
        items = await self._repo.list_all(offset=offset, limit=page_size)
        total = await self._repo.count()
        return ListProjectsResult(items=items, total=total)
```

---

## 14. Correlation ID y Observabilidad

### Regla

Todo log debe incluir `correlation_id`. Nunca usar `print()` — siempre `structlog`.

### Patrón: Logging en use cases

```python
import structlog

logger = structlog.get_logger()

class ProcessGenerationUseCase:
    async def execute(self, generation_request_id: UUID) -> None:
        log = logger.bind(generation_request_id=str(generation_request_id))
        log.info("generation.started")
        try:
            # ...
            log.info("generation.completed", provider=request.provider, duration_ms=elapsed)
        except Exception as e:
            log.error("generation.failed", error=str(e), exc_info=True)
            raise
```

### Patrón: Propagación de correlation_id a Celery

```python
# Al encolar la tarea, pasar el correlation_id del contexto actual
@celery_app.task
def process_generation(generation_request_id: str, correlation_id: str):
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
    # ... resto de la tarea

# Al encolar desde el use case
async def execute(self, command):
    correlation_id = structlog.contextvars.get_contextvars().get("correlation_id", str(uuid4()))
    await self._task_queue.enqueue(
        "process_generation",
        str(saved.id),
        correlation_id=correlation_id,
    )
```

---

## 15. Preparación para Multi-tenancy (owner_id)

### Regla

`Project` tiene `owner_id: UUID | None`. En el MVP siempre es `None`. Cuando se implemente auth, se filtrará por `owner_id` en los repositorios sin cambiar el schema de BD.

### Patrón: Filtrado futuro por owner_id

```python
# Hoy (MVP): sin filtro
async def list_all(self, offset: int, limit: int) -> list[Project]:
    result = await self._session.execute(
        select(ProjectModel).offset(offset).limit(limit)
    )
    return [self._to_entity(m) for m in result.scalars()]

# Futuro (con auth): filtrar por owner_id
async def list_all(self, offset: int, limit: int, owner_id: UUID | None = None) -> list[Project]:
    query = select(ProjectModel)
    if owner_id:
        query = query.where(ProjectModel.owner_id == owner_id)
    result = await self._session.execute(query.offset(offset).limit(limit))
    return [self._to_entity(m) for m in result.scalars()]
```

El campo `owner_id` ya está en la tabla desde el inicio — agregar auth es solo añadir el filtro, sin migraciones de schema.
