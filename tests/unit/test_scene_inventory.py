import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.domain.generations.entities import SceneInventory
from app.domain.images.entities import ImageAsset
from app.domain.shared.exceptions import ResourceNotFoundError
from app.application.generations.analyze_scene import AnalyzeSceneUseCase
from app.application.generations.get_scene_inventory import GetSceneInventoryUseCase
from app.application.generations.process_scene_analysis import ProcessSceneAnalysisUseCase
from app.application.ports.ai_provider_port import SceneInventoryData

@pytest.mark.asyncio
async def test_analyze_scene_creates_pending_and_enqueues():
    mock_scene_repo = AsyncMock()
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

    def mock_save(inv):
        return inv
    mock_scene_repo.save.side_effect = mock_save

    use_case = AnalyzeSceneUseCase(
        scene_repo=mock_scene_repo,
        image_repo=mock_image_repo,
        task_queue=mock_task_queue
    )

    result = await use_case.execute(image_id, correlation_id="test-corr-id")

    assert result.status == "pending"
    assert result.image_id == image_id
    mock_scene_repo.save.assert_called_once()
    mock_task_queue.enqueue.assert_called_once_with(
        "app.infrastructure.tasks.celery_tasks.analyze_scene",
        str(image_id),
        correlation_id="test-corr-id"
    )

@pytest.mark.asyncio
async def test_get_scene_inventory_raises_not_found():
    mock_scene_repo = AsyncMock()
    mock_scene_repo.get_by_image_id.return_value = None

    use_case = GetSceneInventoryUseCase(scene_repo=mock_scene_repo)

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid4())

@pytest.mark.asyncio
async def test_process_scene_analysis_completes_successfully():
    mock_scene_repo = AsyncMock()
    mock_image_repo = AsyncMock()
    mock_storage = AsyncMock()
    mock_registry = MagicMock()
    mock_provider = AsyncMock()

    image_id = uuid4()
    inventory = SceneInventory(id=uuid4(), image_id=image_id, status="pending")

    mock_scene_repo.get_by_image_id.return_value = inventory
    mock_image_repo.get_by_id.return_value = ImageAsset(
        project_id=uuid4(),
        type="original",
        filename="test.jpg",
        mime_type="image/jpeg",
        id=image_id,
        storage_path="path.jpg"
    )

    mock_storage.download.return_value = b"image_data"

    mock_registry.get.return_value = mock_provider
    mock_provider.analyze_scene.return_value = SceneInventoryData(
        inventory={"scene_type": "kitchen", "preservation_rules": ["Keep layout"]},
        provider_name="openai",
        model_name="gpt-4o"
    )

    use_case = ProcessSceneAnalysisUseCase(
        scene_repo=mock_scene_repo,
        image_repo=mock_image_repo,
        storage=mock_storage,
        ai_provider_registry=mock_registry
    )

    await use_case.execute(image_id)

    assert inventory.status == "completed"
    assert inventory.provider == "openai"
    assert inventory.model == "gpt-4o"
    assert inventory.inventory_data == {"scene_type": "kitchen", "preservation_rules": ["Keep layout"]}
    assert inventory.completed_at is not None

    mock_scene_repo.save.assert_called_once_with(inventory)

@pytest.mark.asyncio
async def test_process_scene_analysis_marks_failed_on_error():
    mock_scene_repo = AsyncMock()
    mock_image_repo = AsyncMock()
    mock_storage = AsyncMock()
    mock_registry = MagicMock()
    mock_provider = AsyncMock()

    image_id = uuid4()
    inventory = SceneInventory(id=uuid4(), image_id=image_id, status="pending")

    mock_scene_repo.get_by_image_id.return_value = inventory
    mock_image_repo.get_by_id.return_value = ImageAsset(
        project_id=uuid4(),
        type="original",
        filename="test.jpg",
        mime_type="image/jpeg",
        id=image_id,
        storage_path="path.jpg"
    )

    mock_storage.download.return_value = b"image_data"

    mock_registry.get.return_value = mock_provider
    mock_provider.analyze_scene.side_effect = Exception("API Error")

    use_case = ProcessSceneAnalysisUseCase(
        scene_repo=mock_scene_repo,
        image_repo=mock_image_repo,
        storage=mock_storage,
        ai_provider_registry=mock_registry
    )

    with pytest.raises(Exception, match="API Error"):
        await use_case.execute(image_id)

    assert inventory.status == "failed"
    assert "API Error" in inventory.error_message
    assert inventory.completed_at is not None

    mock_scene_repo.save.assert_called_with(inventory)
