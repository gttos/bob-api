# Tasks — Backend MVP

Implementación dividida en 7 fases. Cada fase es independientemente deployable y testeable. Jules debe completar una fase antes de pasar a la siguiente.

**Referencia arquitectónica**: ver `architecture-patterns.md` antes de implementar cualquier tarea.
**Regla fundamental**: las dependencias solo apuntan hacia adentro (infraestructura → aplicación → dominio).

---

## Fase 1 — Fundación: Estructura, Configuración y Base de Datos

> Objetivo: tener el proyecto corriendo con Docker Compose, la estructura hexagonal en su lugar, y las migraciones de base de datos funcionando.

- [ ] 1.1 Crear estructura de directorios del proyecto siguiendo arquitectura hexagonal
  - Crear `app/domain/`, `app/application/`, `app/infrastructure/`, `app/api/`, `app/config/`
  - Crear `__init__.py` en cada módulo
  - Crear subdirectorios por dominio: `projects/`, `images/`, `generations/`, `evaluations/`, `shared/`

- [ ] 1.2 Configurar dependencias y entorno Python
  - Crear `requirements.txt` con versiones fijadas: fastapi, uvicorn, sqlalchemy[asyncio], alembic, asyncpg, celery, redis, pillow, structlog, pydantic-settings, python-multipart, hypothesis, pytest, pytest-asyncio
  - Crear `requirements-dev.txt` con dependencias de desarrollo: pytest, httpx, aiosqlite

- [ ] 1.3 Implementar configuración con pydantic-settings
  - Crear `app/config/settings.py` con todas las variables de entorno definidas en design.md
  - Incluir: DATABASE_URL, REDIS_URL, STORAGE_LOCAL_PATH, MEDIA_URL_PREFIX, OPENAI_API_KEY, FLUX_ENABLED, MAX_UPLOAD_SIZE_MB, ALLOWED_MIME_TYPES, RATE_LIMIT_ENABLED, RATE_LIMIT_GENERATIONS_PER_DAY, LOG_LEVEL, APP_ENV

- [ ] 1.4 Implementar excepciones de dominio
  - Crear `app/domain/shared/exceptions.py` con: DomainError, ResourceNotFoundError, InvalidStateTransitionError, DomainValidationError, DuplicateResourceError

- [ ] 1.5 Implementar modelos SQLAlchemy
  - Crear `app/infrastructure/persistence/models.py` con todos los modelos ORM: ProjectModel, ImageAssetModel, SceneInventoryModel, GenerationRequestModel, ImageVariantModel, EvaluationModel
  - Incluir `owner_id` (UUID nullable) en ProjectModel
  - Usar JSONB para inventory_data y provider_params

- [ ] 1.6 Configurar SQLAlchemy async y sesión
  - Crear `app/infrastructure/persistence/database.py` con engine async, SessionLocal, y función `get_session` para FastAPI DI

- [ ] 1.7 Configurar Alembic y crear migración inicial
  - Inicializar Alembic con soporte async
  - Crear migración inicial con todas las tablas
  - Verificar que `alembic upgrade head` crea el schema correctamente

- [ ] 1.8 Crear aplicación FastAPI base
  - Crear `app/api/main.py` con app FastAPI, prefijo `/api/v1/`, middleware CORS básico
  - Registrar exception handlers globales para todas las excepciones de dominio
  - Montar endpoint `/media/` con StaticFiles para servir imágenes locales
  - Agregar endpoint `GET /api/v1/health`

- [ ] 1.9 Configurar Docker Compose
  - Crear `Dockerfile` multi-stage (base → dependencies → production)
  - Crear `docker-compose.yml` con servicios: api, celery-worker, db (postgres:16-alpine), redis (redis:7-alpine)
  - Configurar volúmenes: `media_data` y `pg_data`
  - Configurar healthchecks para db y redis
  - Crear `.env.example` con todas las variables documentadas
  - Crear `docker-compose.override.yml` para desarrollo local (hot reload, puertos expuestos)

- [ ] 1.10 Configurar logging estructurado con structlog
  - Crear `app/config/logging.py` con structlog en formato JSON
  - Crear `app/api/middleware/correlation.py` con CorrelationIDMiddleware
  - Registrar middleware en main.py
  - Verificar que los logs incluyen correlation_id en formato JSON

- [ ] 1.11 Configurar Celery
  - Crear `app/infrastructure/tasks/celery_app.py` con configuración Celery + Redis broker
  - Crear `app/infrastructure/tasks/celery_tasks.py` con estructura base (sin lógica aún)

- [ ] 1.12 Tests de la fase 1
  - Test: `docker compose up` levanta todos los servicios sin errores
  - Test: `GET /api/v1/health` retorna 200
  - Test: `alembic upgrade head` crea todas las tablas
  - Test: logs aparecen en formato JSON con correlation_id

---

## Fase 2 — Projects API

> Objetivo: CRUD completo de proyectos con paginación, owner_id, tests unitarios y de propiedades.

- [ ] 2.1 Implementar entidad de dominio Project
  - Crear `app/domain/projects/entities.py` con dataclass Project
  - Incluir campos: id (UUID), name, description, owner_id (nullable), created_at, updated_at
  - Implementar método `update(name, description)`

- [ ] 2.2 Implementar puerto ProjectRepository
  - Crear `app/application/ports/repository_ports.py` con interfaz abstracta ProjectRepository
  - Métodos: save, get_by_id, list_all(offset, limit), count, delete

- [ ] 2.3 Implementar casos de uso de proyectos
  - Crear `app/application/projects/create_project.py` — CreateProjectUseCase + CreateProjectCommand
  - Crear `app/application/projects/get_project.py` — GetProjectUseCase
  - Crear `app/application/projects/list_projects.py` — ListProjectsUseCase (con paginación)
  - Crear `app/application/projects/update_project.py` — UpdateProjectUseCase + UpdateProjectCommand
  - Crear `app/application/projects/delete_project.py` — DeleteProjectUseCase

- [ ] 2.4 Implementar SQLAlchemyProjectRepository
  - Crear `app/infrastructure/persistence/projects/sqlalchemy_repository.py`
  - Implementar todos los métodos del puerto con traducción entidad ↔ modelo ORM
  - Incluir filtro por owner_id preparado (pero no activo en MVP)

- [ ] 2.5 Implementar schemas Pydantic para proyectos
  - Crear `app/api/schemas/projects.py`: ProjectCreate, ProjectUpdate, ProjectResponse
  - ProjectResponse incluye método `from_entity(project)`
  - Crear `app/api/schemas/pagination.py`: PaginatedResponse[T] genérico

- [ ] 2.6 Implementar router de proyectos
  - Crear `app/api/routers/projects.py` con endpoints bajo `/api/v1/projects`
  - POST / → 201 Created
  - GET / → 200 PaginatedResponse[ProjectResponse] (params: page, page_size)
  - GET /{project_id} → 200 ProjectResponse
  - PATCH /{project_id} → 200 ProjectResponse
  - DELETE /{project_id} → 204 No Content

- [ ] 2.7 Configurar inyección de dependencias para proyectos
  - Crear `app/api/dependencies.py` con funciones get_*_uc para todos los use cases de proyectos

- [ ] 2.8 Tests unitarios de proyectos
  - Tests de CreateProjectUseCase con mock de ProjectRepository
  - Tests de UpdateProjectUseCase (verifica que solo cambian campos enviados)
  - Tests de DeleteProjectUseCase (verifica 404 si no existe)
  - Tests de ListProjectsUseCase (verifica paginación)

- [ ] 2.9 Tests de propiedades de proyectos
  - Propiedad 1: Round-trip crear → obtener retorna mismos datos
  - Propiedad 2: PATCH parcial preserva campos no modificados
  - Usar Hypothesis con `@settings(max_examples=100)`

- [ ] 2.10 Tests de integración del router de proyectos
  - Usar TestClient de FastAPI con base de datos SQLite en memoria
  - Cubrir todos los endpoints y casos de error (404, 422)

---

## Fase 3 — Images API y Storage Local

> Objetivo: subida de imágenes, almacenamiento local, thumbnails, y listado paginado.

- [ ] 3.1 Implementar entidad de dominio ImageAsset
  - Crear `app/domain/images/entities.py` con dataclass ImageAsset
  - Campos: id, project_id, type (original/generated), filename, mime_type, width, height, storage_path, thumbnail_path, created_at

- [ ] 3.2 Implementar puerto ImageRepository
  - Agregar ImageRepository a `app/application/ports/repository_ports.py`
  - Métodos: save, get_by_id, list_by_project(project_id, offset, limit), count_by_project, delete

- [ ] 3.3 Implementar puerto StoragePort
  - Crear `app/application/ports/storage_port.py` con interfaz abstracta StoragePort
  - Métodos async: upload, download, delete, get_url

- [ ] 3.4 Implementar LocalStorageAdapter
  - Crear `app/infrastructure/storage/local_storage_adapter.py`
  - Implementar todos los métodos de StoragePort
  - Crear directorios automáticamente si no existen
  - `get_url` retorna `/media/{path}`

- [ ] 3.5 Implementar ThumbnailService
  - Crear `app/infrastructure/thumbnail/pillow_thumbnail.py`
  - Generar thumbnail con Pillow, max 400x400, preservando aspect ratio
  - Retornar bytes del thumbnail

- [ ] 3.6 Implementar casos de uso de imágenes
  - Crear `app/application/images/upload_image.py` — UploadImageUseCase
    - Validar MIME type contra lista blanca configurable
    - Validar tamaño máximo configurable
    - Generar storage_path con convención: `projects/{project_id}/originals/{image_id}.{ext}`
    - Subir imagen y thumbnail a storage
    - Extraer width/height con Pillow
    - Guardar ImageAsset en repositorio
  - Crear `app/application/images/get_image.py` — GetImageUseCase
  - Crear `app/application/images/list_images.py` — ListImagesUseCase (paginado)
  - Crear `app/application/images/delete_image.py` — DeleteImageUseCase (elimina de storage y BD)

- [ ] 3.7 Implementar SQLAlchemyImageRepository
  - Crear `app/infrastructure/persistence/images/sqlalchemy_repository.py`

- [ ] 3.8 Implementar schemas y router de imágenes
  - Crear `app/api/schemas/images.py`: ImageUploadResponse, ImageResponse (con url, thumbnail_url, sin storage_path)
  - Crear `app/api/routers/images.py`:
    - POST /api/v1/projects/{project_id}/images → 201 (multipart/form-data)
    - GET /api/v1/projects/{project_id}/images → 200 PaginatedResponse[ImageResponse]
    - GET /api/v1/images/{image_id} → 200 ImageResponse
    - DELETE /api/v1/images/{image_id} → 204
    - GET /api/v1/images/{image_id}/download → redirect o stream del archivo

- [ ] 3.9 Tests unitarios de imágenes
  - Tests de UploadImageUseCase con mock de ImageRepository y StoragePort
  - Test: MIME type inválido retorna error antes de llamar a storage
  - Test: archivo demasiado grande retorna error antes de llamar a storage
  - Test: storage_path nunca aparece en la respuesta

- [ ] 3.10 Tests de propiedades de imágenes
  - Propiedad 3: Round-trip subir → obtener retorna metadatos correctos
  - Propiedad 4: storage_path nunca se expone en respuestas
  - Propiedad 5: url retornada usa prefijo /media/
  - Propiedad 6: thumbnail existe para toda imagen creada
  - Propiedad 23: MIME types fuera de lista blanca son rechazados

---

## Fase 4 — Generation Pipeline: Celery, PromptBuilder y AI Provider

> Objetivo: pipeline completo de generación asíncrona — desde la solicitud hasta la imagen generada guardada.

- [ ] 4.1 Implementar entidades de dominio de generaciones
  - Crear `app/domain/generations/entities.py`:
    - Enum GenerationMode: commercial_enhancement, style_redesign, functional_variant, localized_edit
    - Enum GenerationStatus: pending, analyzing, generating, completed, failed
    - GenerationStatus.can_transition_to() con tabla de transiciones válidas
    - Dataclass GenerationRequest con método transition_to() y mark_failed()
    - Dataclass ImageVariant

- [ ] 4.2 Implementar puertos de generaciones
  - Agregar GenerationRepository a `app/application/ports/repository_ports.py`
  - Crear `app/application/ports/ai_provider_port.py` con AIProviderPort, PromptResult, GenerationResult, SceneInventoryData
  - Crear `app/application/ports/task_queue_port.py` con TaskQueuePort

- [ ] 4.3 Implementar PromptBuilder (servicio de dominio puro)
  - Crear `app/domain/generations/services.py` con PromptBuilder y PromptConfig
  - Implementar todas las plantillas de presets definidas en requirements (13 plantillas)
  - Lógica de preservación para modo localized_edit
  - Adaptación de parámetros por proveedor (openai vs flux)
  - Sin I/O, sin dependencias externas — solo lógica pura

- [ ] 4.4 Implementar OpenAIProvider
  - Crear `app/infrastructure/ai_providers/openai_provider.py`
  - Implementar AIProviderPort: generate_variant() usando gpt-image-1 con imagen de referencia
  - Implementar analyze_scene() usando GPT-4o Vision para análisis de escena
  - Manejo de errores de la API de OpenAI con excepciones de dominio

- [ ] 4.5 Implementar AIProviderRegistry
  - Crear `app/infrastructure/ai_providers/registry.py` con AIProviderRegistry
  - Registro de proveedores por nombre, resolución sin lógica condicional

- [ ] 4.6 Implementar CeleryTaskQueueAdapter
  - Crear `app/infrastructure/tasks/celery_queue_adapter.py` implementando TaskQueuePort
  - Propagar correlation_id al encolar tareas

- [ ] 4.7 Implementar casos de uso de generaciones
  - Crear `app/application/generations/request_generation.py` — RequestGenerationUseCase
    - Verificar que la imagen existe
    - Crear GenerationRequest con estado pending
    - Encolar tarea con correlation_id
  - Crear `app/application/generations/get_generation.py` — GetGenerationUseCase
  - Crear `app/application/generations/list_generations.py` — ListGenerationsUseCase (paginado)
  - Crear `app/application/generations/process_generation.py` — ProcessGenerationUseCase
    - Transiciones de estado: pending → analyzing → generating → completed/failed
    - Invocar PromptBuilder, AIProvider, StoragePort
    - Crear ImageVariant con version_number incremental
    - Guardar prompt_final, provider, model en GenerationRequest
    - mark_failed() en cualquier excepción

- [ ] 4.8 Implementar tarea Celery process_generation
  - Actualizar `app/infrastructure/tasks/celery_tasks.py`
  - Resolver dependencias manualmente (sin FastAPI DI)
  - Invocar ProcessGenerationUseCase
  - Reintentar solo errores transitorios (max_retries=2)
  - Propagar correlation_id al contexto de structlog

- [ ] 4.9 Implementar SQLAlchemyGenerationRepository
  - Crear `app/infrastructure/persistence/generations/sqlalchemy_repository.py`
  - Incluir lógica de version_number incremental (SELECT MAX + 1 con lock)

- [ ] 4.10 Implementar schemas y router de generaciones
  - Crear `app/api/schemas/generations.py`: GenerationRequestCreate, GenerationRequestResponse, ImageVariantResponse
  - Crear `app/api/routers/generations.py`:
    - POST /api/v1/images/{image_id}/generations → 202 Accepted
    - GET /api/v1/generations/{generation_id} → 200
    - GET /api/v1/images/{image_id}/generations → 200 PaginatedResponse

- [ ] 4.11 Tests unitarios del pipeline de generación
  - Tests de RequestGenerationUseCase con mocks
  - Tests de ProcessGenerationUseCase con mocks (flujo completo, incluyendo fallo)
  - Tests de PromptBuilder para cada modo y preset
  - Test: transición de estado inválida lanza InvalidStateTransitionError
  - Test: mark_failed() siempre resulta en status=failed con error_message

- [ ] 4.12 Tests de propiedades del pipeline
  - Propiedad 8: RequestGeneration retorna inmediatamente con status=pending
  - Propiedad 9: modos inválidos retornan 422
  - Propiedad 10: transiciones de estado siguen secuencia válida
  - Propiedad 11: fallo del worker siempre resulta en status=failed
  - Propiedad 12: PromptBuilder produce salida válida para toda configuración válida
  - Propiedad 13: PromptBuilder incluye reglas de preservación en localized_edit
  - Propiedad 15: version_number es secuencial sin huecos
  - Propiedad 16: generaciones nunca sobrescriben imágenes existentes

---

## Fase 5 — Scene Inventory

> Objetivo: análisis de escena con OpenAI Vision, almacenamiento del inventario JSON, y endpoint de consulta.

- [ ] 5.1 Implementar entidad SceneInventory
  - Agregar dataclass SceneInventory a `app/domain/generations/entities.py`
  - Campos: id, image_id, inventory_data (dict), status, error_message, provider, model, created_at, completed_at

- [ ] 5.2 Implementar puerto SceneInventoryRepository
  - Agregar SceneInventoryRepository a `app/application/ports/repository_ports.py`
  - Métodos: save, get_by_image_id

- [ ] 5.3 Implementar casos de uso de scene inventory
  - Crear `app/application/generations/analyze_scene.py` — AnalyzeSceneUseCase
    - Verificar que la imagen existe
    - Crear SceneInventory con status=pending
    - Encolar tarea analyze_scene con correlation_id
  - Crear `app/application/generations/get_scene_inventory.py` — GetSceneInventoryUseCase

- [ ] 5.4 Implementar tarea Celery analyze_scene
  - Agregar tarea en `app/infrastructure/tasks/celery_tasks.py`
  - Invocar AnalyzeSceneUseCase (o directamente AIProvider.analyze_scene)
  - Guardar resultado en SceneInventory con status=completed
  - En error: status=failed con error_message

- [ ] 5.5 Implementar SQLAlchemySceneInventoryRepository
  - Crear `app/infrastructure/persistence/generations/scene_inventory_repository.py`

- [ ] 5.6 Implementar schemas y router de scene inventory
  - Crear schemas: SceneInventoryResponse con inventory_data como dict
  - Crear `app/api/routers/scene_inventory.py`:
    - POST /api/v1/images/{image_id}/scene-inventory → 202 Accepted
    - GET /api/v1/images/{image_id}/scene-inventory → 200 SceneInventoryResponse o 404

- [ ] 5.7 Tests de scene inventory
  - Test unitario: AnalyzeSceneUseCase con mock de AIProvider
  - Test: GET retorna 404 si no existe inventario
  - Propiedad 7: SceneInventory completado contiene campos requeridos (scene_type, architecture, preservation_rules)

---

## Fase 6 — Evaluaciones, Comparación y Estadísticas

> Objetivo: evaluación manual de variantes, comparador antes/después, y endpoint de estadísticas de uso.

- [ ] 6.1 Implementar entidad Evaluation
  - Crear `app/domain/evaluations/entities.py` con dataclass Evaluation
  - Campos: id, variant_id, scores (10 dimensiones 1-5), verdict, notes, created_at, updated_at
  - Validación: scores deben estar en rango [1, 5]
  - Enum EvaluationVerdict: approved, usable_with_retouch, rejected

- [ ] 6.2 Implementar puerto EvaluationRepository
  - Agregar EvaluationRepository a `app/application/ports/repository_ports.py`

- [ ] 6.3 Implementar casos de uso de evaluaciones
  - Crear `app/application/evaluations/create_evaluation.py` — CreateEvaluationUseCase
  - Crear `app/application/evaluations/get_evaluation.py` — GetEvaluationUseCase
  - Crear `app/application/evaluations/update_evaluation.py` — UpdateEvaluationUseCase (PATCH parcial)

- [ ] 6.4 Implementar SQLAlchemyEvaluationRepository
  - Crear `app/infrastructure/persistence/evaluations/sqlalchemy_repository.py`

- [ ] 6.5 Implementar schemas y router de evaluaciones
  - Crear `app/api/schemas/evaluations.py`: EvaluationCreate, EvaluationUpdate, EvaluationResponse
  - Crear `app/api/routers/evaluations.py`:
    - POST /api/v1/image-variants/{variant_id}/evaluation → 201
    - GET /api/v1/image-variants/{variant_id}/evaluation → 200 o 404
    - PATCH /api/v1/evaluations/{evaluation_id} → 200

- [ ] 6.6 Implementar endpoint de comparación
  - Crear `app/application/generations/get_comparison.py` — GetComparisonUseCase
    - Retorna imagen original + lista de variantes ordenadas por version_number
    - Incluye metadatos del GenerationRequest en cada variante
    - Incluye url servida para cada imagen (nunca storage_path)
  - Agregar endpoint GET /api/v1/images/{image_id}/comparison al router de imágenes

- [ ] 6.7 Implementar endpoint de estadísticas
  - Crear `app/application/stats/get_generation_stats.py` — GetGenerationStatsUseCase
    - Agrupación por proveedor, por proyecto, por período
    - Separar completadas de fallidas
  - Crear `app/api/routers/stats.py`:
    - GET /api/v1/stats/generations → 200 con conteos agrupados

- [ ] 6.8 Tests de evaluaciones
  - Tests unitarios de CreateEvaluationUseCase con mocks
  - Test: score fuera de [1,5] lanza DomainValidationError
  - Test: veredicto inválido lanza DomainValidationError
  - Propiedad 17: validación de scores y veredictos
  - Propiedad 18: round-trip crear → obtener evaluación
  - Propiedad 19: PATCH parcial preserva campos no modificados

- [ ] 6.9 Tests de comparación
  - Propiedad 20: comparación retorna original + todas las variantes con metadatos
  - Test: storage_path nunca aparece en respuesta de comparación

---

## Fase 7 — Observabilidad, Rate Limiting y Hardening Final

> Objetivo: sistema listo para producción con observabilidad completa, rate limiting activable, y tests de integración end-to-end.

- [ ] 7.1 Completar observabilidad
  - Verificar que correlation_id se propaga correctamente en todos los flujos (HTTP → Celery → logs)
  - Agregar log de request/response en middleware (método, path, status, duration_ms)
  - Agregar logs estructurados en todos los use cases críticos (generación, análisis, errores)
  - Verificar formato JSON en todos los logs

- [ ] 7.2 Implementar Rate Limiting
  - Crear `app/api/middleware/rate_limit.py` con RateLimitMiddleware
  - Usar Redis como contador con ventana de 24h
  - Activable con `RATE_LIMIT_ENABLED=true`
  - Retornar 429 con tiempo de reset cuando se supera el límite
  - Registrar middleware en main.py (solo si RATE_LIMIT_ENABLED=true)

- [ ] 7.3 Hardening de seguridad
  - Verificar que ningún endpoint retorna storage_path en ninguna respuesta
  - Verificar que el endpoint /media/ no permite path traversal
  - Agregar validación de Content-Type en upload de imágenes (no solo MIME del archivo)
  - Limitar tamaño de body en todos los endpoints (no solo uploads)

- [ ] 7.4 Tests de integración end-to-end
  - Test flujo completo Fase 1: crear proyecto → subir imagen → verificar thumbnail
  - Test flujo completo Fase 2: crear proyecto → subir imagen → solicitar generación → verificar estado pending → simular worker → verificar estado completed → comparar → evaluar
  - Test flujo de error: generación falla → verificar status=failed con error_message → verificar que imagen original no fue modificada
  - Test rate limiting: con RATE_LIMIT_ENABLED=true, superar límite retorna 429

- [ ] 7.5 Documentación de API
  - Verificar que la documentación OpenAPI en `/docs` está completa y correcta
  - Agregar descripciones a todos los endpoints y schemas
  - Verificar que el health check retorna información útil (versión, estado de BD, estado de Redis)

- [ ] 7.6 Verificación final de Docker
  - Verificar que `docker compose up` levanta todo sin errores desde cero
  - Verificar que las migraciones corren automáticamente al iniciar
  - Verificar que el volumen `media_data` persiste imágenes entre reinicios
  - Crear `docker-compose.prod.yml` con configuración de producción (sin puertos expuestos de BD/Redis, workers con concurrency=4)
