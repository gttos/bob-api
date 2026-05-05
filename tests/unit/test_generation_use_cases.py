import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.domain.generations.entities import GenerationRequest, GenerationMode, GenerationStatus, ImageVariant
from app.domain.images.entities import ImageAsset
from app.domain.shared.exceptions import ResourceNotFoundError, InvalidStateTransitionError
from app.application.generations.request_generation import RequestGenerationUseCase, RequestGenerationCommand
from app.application.generations.process_generation import ProcessGenerationUseCase
from app.application.ports.ai_provider_port import GenerationResult

@pytest.mark.asyncio
async def test_request_generation_creates_pending_and_enqueues():
    mock_generation_repo = AsyncMock()
    mock_image_repo = AsyncMock()
    mock_task_queue = AsyncMock()

    image_id = uuid4()
    mock_image_repo.get_by_id.return_value = ImageAsset(
        project_id=uuid4(),
        type="original",
        filename="test.jpg",
        mime_type="image/jpeg",
        id=image_id
    )

    def mock_save(request):
        return request
    mock_generation_repo.save.side_effect = mock_save

    use_case = RequestGenerationUseCase(
        generation_repo=mock_generation_repo,
        image_repo=mock_image_repo,
        task_queue=mock_task_queue
    )

    command = RequestGenerationCommand(
        image_id=image_id,
        mode=GenerationMode.commercial_enhancement,
        provider="openai"
    )

    result = await use_case.execute(command, correlation_id="test-corr-id")

    assert result.status == GenerationStatus.pending
    mock_generation_repo.save.assert_called_once()
    mock_task_queue.enqueue.assert_called_once_with(
        "app.infrastructure.tasks.celery_tasks.process_generation",
        str(result.id),
        correlation_id="test-corr-id"
    )

@pytest.mark.asyncio
async def test_request_generation_raises_if_image_not_found():
    mock_generation_repo = AsyncMock()
    mock_image_repo = AsyncMock()
    mock_task_queue = AsyncMock()

    mock_image_repo.get_by_id.return_value = None

    use_case = RequestGenerationUseCase(
        generation_repo=mock_generation_repo,
        image_repo=mock_image_repo,
        task_queue=mock_task_queue
    )

    command = RequestGenerationCommand(
        image_id=uuid4(),
        mode=GenerationMode.commercial_enhancement,
        provider="openai"
    )

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(command)

@pytest.mark.asyncio
async def test_process_generation_full_flow():
    mock_generation_repo = AsyncMock()
    mock_image_repo = AsyncMock()
    mock_storage = AsyncMock()
    mock_registry = MagicMock()
    mock_provider = AsyncMock()
    mock_prompt_builder = MagicMock()
    mock_thumbnail_service = MagicMock()

    generation_id = uuid4()
    source_image_id = uuid4()

    request = GenerationRequest(
        id=generation_id,
        source_image_id=source_image_id,
        mode=GenerationMode.commercial_enhancement,
        provider="openai",
        status=GenerationStatus.pending
    )

    source_image = ImageAsset(
        project_id=uuid4(),
        type="original",
        filename="test.jpg",
        mime_type="image/jpeg",
        id=source_image_id,
        storage_path="some/path.jpg"
    )

    mock_generation_repo.get_by_id.return_value = request
    mock_image_repo.get_by_id.side_effect = lambda id: source_image if id == source_image_id else None

    def mock_save(req):
        return req
    mock_generation_repo.save.side_effect = mock_save

    mock_storage.download.return_value = b"image_data"
    mock_storage.upload.side_effect = ["gen_path.jpg", "thumb_path.jpg"]

    mock_registry.get.return_value = mock_provider
    mock_provider.generate_variant.return_value = GenerationResult(
        image_data=b"generated_data",
        provider_name="openai",
        model_name="dall-e-3",
        metadata={}
    )

    prompt_result = MagicMock()
    prompt_result.prompt = "final prompt"
    prompt_result.negative_prompt = "neg prompt"
    mock_prompt_builder.build.return_value = prompt_result

    mock_thumbnail_service.generate.return_value = b"thumb_data"

    def mock_image_save(img):
        img.id = uuid4()
        return img
    mock_image_repo.save.side_effect = mock_image_save

    mock_generation_repo.get_next_version_number.return_value = 1

    def mock_variant_save(variant):
        variant.id = uuid4()
        return variant
    mock_generation_repo.save_variant.side_effect = mock_variant_save

    use_case = ProcessGenerationUseCase(
        generation_repo=mock_generation_repo,
        image_repo=mock_image_repo,
        storage=mock_storage,
        ai_provider_registry=mock_registry,
        prompt_builder=mock_prompt_builder,
        thumbnail_service=mock_thumbnail_service
    )

    await use_case.execute(generation_id)

    assert request.status == GenerationStatus.completed
    assert request.prompt_final == "final prompt"

    assert mock_storage.upload.call_count == 2
    mock_generation_repo.save_variant.assert_called_once()

    assert mock_generation_repo.save.call_count >= 3

@pytest.mark.asyncio
async def test_process_generation_marks_failed_on_error():
    mock_generation_repo = AsyncMock()
    mock_image_repo = AsyncMock()
    mock_storage = AsyncMock()
    mock_registry = MagicMock()
    mock_provider = AsyncMock()
    mock_prompt_builder = MagicMock()
    mock_thumbnail_service = MagicMock()

    generation_id = uuid4()

    request = GenerationRequest(
        id=generation_id,
        source_image_id=uuid4(),
        mode=GenerationMode.commercial_enhancement,
        provider="openai",
        status=GenerationStatus.pending
    )

    mock_generation_repo.get_by_id.return_value = request
    mock_image_repo.get_by_id.return_value = ImageAsset(
        project_id=uuid4(), type="original", filename="t.jpg", mime_type="image/jpeg"
    )

    mock_registry.get.return_value = mock_provider
    mock_provider.generate_variant.side_effect = Exception("API Error")

    use_case = ProcessGenerationUseCase(
        generation_repo=mock_generation_repo,
        image_repo=mock_image_repo,
        storage=mock_storage,
        ai_provider_registry=mock_registry,
        prompt_builder=mock_prompt_builder,
        thumbnail_service=mock_thumbnail_service
    )

    with pytest.raises(Exception, match="API Error"):
        await use_case.execute(generation_id)

    assert request.status == GenerationStatus.failed
    assert "API Error" in request.error_message

def test_invalid_state_transition_raises():
    request = GenerationRequest(
        source_image_id=uuid4(),
        mode=GenerationMode.commercial_enhancement,
        provider="openai",
        status=GenerationStatus.completed
    )

    with pytest.raises(InvalidStateTransitionError):
        request.transition_to(GenerationStatus.analyzing)
