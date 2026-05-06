import asyncio
import structlog
from uuid import UUID

from app.infrastructure.tasks.celery_app import celery_app
from app.infrastructure.persistence.database import AsyncSessionLocal
from app.infrastructure.persistence.generations.sqlalchemy_repository import SQLAlchemyGenerationRepository
from app.infrastructure.persistence.images.sqlalchemy_repository import SQLAlchemyImageRepository
from app.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from app.infrastructure.thumbnail.pillow_thumbnail import ThumbnailService
from app.infrastructure.ai_providers.registry import AIProviderRegistry
from app.infrastructure.ai_providers.openai_provider import OpenAIProvider
from app.domain.generations.services import PromptBuilder
from app.application.generations.process_generation import ProcessGenerationUseCase
from app.config.settings import settings

logger = structlog.get_logger(__name__)

def get_ai_provider_registry() -> AIProviderRegistry:
    registry = AIProviderRegistry()
    registry.register(OpenAIProvider(api_key=settings.OPENAI_API_KEY))
    return registry

async def _process_generation_async(generation_request_id_str: str, correlation_id: str = ""):
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
    logger.info("Starting process_generation task", generation_request_id=generation_request_id_str)

    generation_request_id = UUID(generation_request_id_str)

    async with AsyncSessionLocal() as session:
        generation_repo = SQLAlchemyGenerationRepository(session)
        image_repo = SQLAlchemyImageRepository(session)
        storage = LocalStorageAdapter(
            base_path=settings.STORAGE_LOCAL_PATH,
            media_url_prefix=settings.MEDIA_URL_PREFIX
        )
        ai_provider_registry = get_ai_provider_registry()
        prompt_builder = PromptBuilder()
        thumbnail_service = ThumbnailService()

        use_case = ProcessGenerationUseCase(
            generation_repo=generation_repo,
            image_repo=image_repo,
            storage=storage,
            ai_provider_registry=ai_provider_registry,
            prompt_builder=prompt_builder,
            thumbnail_service=thumbnail_service
        )

        await use_case.execute(generation_request_id)

    logger.info("Finished process_generation task", generation_request_id=generation_request_id_str)

@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def process_generation(self, generation_request_id: str, correlation_id: str = ""):
    # Clear contextvars
    structlog.contextvars.clear_contextvars()
    if correlation_id:
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    try:
        # Run async function in sync task
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(_process_generation_async(generation_request_id, correlation_id))
    except Exception as exc:
        logger.error("Error in process_generation task", exc_info=True, generation_request_id=generation_request_id)
        # Note: In a real environment we might want to catch specific provider errors and self.retry() here.
        # For now we'll just log and let it fail.
        # ProcessGenerationUseCase already marks as failed in db
        raise

from app.infrastructure.persistence.generations.scene_inventory_repository import SQLAlchemySceneInventoryRepository
from app.application.generations.process_scene_analysis import ProcessSceneAnalysisUseCase

async def _analyze_scene_async(image_id_str: str, correlation_id: str = ""):
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
    logger.info("Starting analyze_scene task", image_id=image_id_str)

    image_id = UUID(image_id_str)

    async with AsyncSessionLocal() as session:
        scene_repo = SQLAlchemySceneInventoryRepository(session)
        image_repo = SQLAlchemyImageRepository(session)
        storage = LocalStorageAdapter(
            base_path=settings.STORAGE_LOCAL_PATH,
            media_url_prefix=settings.MEDIA_URL_PREFIX
        )
        ai_provider_registry = get_ai_provider_registry()

        use_case = ProcessSceneAnalysisUseCase(
            scene_repo=scene_repo,
            image_repo=image_repo,
            storage=storage,
            ai_provider_registry=ai_provider_registry
        )

        await use_case.execute(image_id)

    logger.info("Finished analyze_scene task", image_id=image_id_str)

@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def analyze_scene(self, image_id: str, correlation_id: str = ""):
    # Clear contextvars
    structlog.contextvars.clear_contextvars()
    if correlation_id:
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    try:
        # Run async function in sync task
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(_analyze_scene_async(image_id, correlation_id))
    except Exception as exc:
        logger.error("Error in analyze_scene task", exc_info=True, image_id=image_id)
        # Note: In a real environment we might want to catch specific provider errors and self.retry() here.
        raise
