import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import io
from PIL import Image

from app.domain.images.entities import ImageAsset
from app.domain.projects.entities import Project
from app.domain.shared.exceptions import ResourceNotFoundError, DomainValidationError
from app.application.images.upload_image import UploadImageUseCase, UploadImageCommand
from app.application.images.get_image import GetImageUseCase
from app.application.images.list_images import ListImagesUseCase, ListImagesResult
from app.application.images.delete_image import DeleteImageUseCase


@pytest.fixture
def mock_image_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_project_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    return storage


@pytest.fixture
def mock_thumbnail_service():
    service = MagicMock()
    service.get_image_dimensions.return_value = (800, 600)
    service.generate.return_value = b"fake_thumbnail_bytes"
    return service


@pytest.mark.asyncio
async def test_upload_image_success(mock_image_repo, mock_project_repo, mock_storage, mock_thumbnail_service):
    # Setup
    project_id = uuid4()
    mock_project_repo.get_by_id.return_value = Project(id=project_id, name="Test Project", owner_id="user1")

    command = UploadImageCommand(
        project_id=project_id,
        filename="test.png",
        content_type="image/png",
        file_data=b"fake_image_bytes"
    )

    use_case = UploadImageUseCase(
        image_repo=mock_image_repo,
        project_repo=mock_project_repo,
        storage=mock_storage,
        thumbnail_service=mock_thumbnail_service,
        allowed_mime_types=["image/jpeg", "image/png"],
        max_upload_size_mb=5
    )

    mock_image_repo.save.side_effect = lambda asset: asset

    # Execute
    result = await use_case.execute(command)

    # Assertions
    mock_project_repo.get_by_id.assert_called_once_with(project_id)
    mock_thumbnail_service.get_image_dimensions.assert_called_once_with(b"fake_image_bytes")
    mock_thumbnail_service.generate.assert_called_once_with(b"fake_image_bytes")

    assert mock_storage.upload.call_count == 2
    mock_image_repo.save.assert_called_once()

    assert result.project_id == project_id
    assert result.filename == "test.png"
    assert result.mime_type == "image/png"
    assert result.width == 800
    assert result.height == 600
    assert result.storage_path.startswith(f"projects/{project_id}/originals/")
    assert result.thumbnail_path.startswith(f"projects/{project_id}/originals/")


@pytest.mark.asyncio
async def test_upload_image_project_not_found(mock_image_repo, mock_project_repo, mock_storage, mock_thumbnail_service):
    project_id = uuid4()
    mock_project_repo.get_by_id.return_value = None

    command = UploadImageCommand(
        project_id=project_id,
        filename="test.png",
        content_type="image/png",
        file_data=b"fake_image_bytes"
    )

    use_case = UploadImageUseCase(
        image_repo=mock_image_repo,
        project_repo=mock_project_repo,
        storage=mock_storage,
        thumbnail_service=mock_thumbnail_service,
        allowed_mime_types=["image/jpeg", "image/png"],
        max_upload_size_mb=5
    )

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(command)


@pytest.mark.asyncio
async def test_upload_image_invalid_mime_type(mock_image_repo, mock_project_repo, mock_storage, mock_thumbnail_service):
    project_id = uuid4()
    mock_project_repo.get_by_id.return_value = Project(id=project_id, name="Test Project", owner_id="user1")

    command = UploadImageCommand(
        project_id=project_id,
        filename="test.txt",
        content_type="text/plain",
        file_data=b"fake_image_bytes"
    )

    use_case = UploadImageUseCase(
        image_repo=mock_image_repo,
        project_repo=mock_project_repo,
        storage=mock_storage,
        thumbnail_service=mock_thumbnail_service,
        allowed_mime_types=["image/jpeg", "image/png"],
        max_upload_size_mb=5
    )

    with pytest.raises(DomainValidationError, match="Invalid content type"):
        await use_case.execute(command)


@pytest.mark.asyncio
async def test_upload_image_file_too_large(mock_image_repo, mock_project_repo, mock_storage, mock_thumbnail_service):
    project_id = uuid4()
    mock_project_repo.get_by_id.return_value = Project(id=project_id, name="Test Project", owner_id="user1")

    # 6 MB file
    large_file = b"0" * (6 * 1024 * 1024)

    command = UploadImageCommand(
        project_id=project_id,
        filename="test.png",
        content_type="image/png",
        file_data=large_file
    )

    use_case = UploadImageUseCase(
        image_repo=mock_image_repo,
        project_repo=mock_project_repo,
        storage=mock_storage,
        thumbnail_service=mock_thumbnail_service,
        allowed_mime_types=["image/jpeg", "image/png"],
        max_upload_size_mb=5
    )

    with pytest.raises(DomainValidationError, match="File size exceeds maximum allowed"):
        await use_case.execute(command)


@pytest.mark.asyncio
async def test_get_image_success(mock_image_repo, mock_storage):
    image_id = uuid4()
    mock_image_repo.get_by_id.return_value = ImageAsset(
        id=image_id,
        project_id=uuid4(),
        type="original",
        filename="test.jpg",
        mime_type="image/jpeg"
    )

    use_case = GetImageUseCase(image_repo=mock_image_repo, storage=mock_storage)
    result = await use_case.execute(image_id)

    assert result.id == image_id
    mock_image_repo.get_by_id.assert_called_once_with(image_id)


@pytest.mark.asyncio
async def test_get_image_not_found(mock_image_repo, mock_storage):
    image_id = uuid4()
    mock_image_repo.get_by_id.return_value = None

    use_case = GetImageUseCase(image_repo=mock_image_repo, storage=mock_storage)

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(image_id)


@pytest.mark.asyncio
async def test_list_images_success(mock_image_repo):
    project_id = uuid4()
    mock_items = [
        ImageAsset(id=uuid4(), project_id=project_id, type="original", filename="1.jpg", mime_type="image/jpeg"),
        ImageAsset(id=uuid4(), project_id=project_id, type="original", filename="2.jpg", mime_type="image/jpeg")
    ]
    mock_image_repo.list_by_project.return_value = mock_items
    mock_image_repo.count_by_project.return_value = 2

    use_case = ListImagesUseCase(image_repo=mock_image_repo)
    result = await use_case.execute(project_id, page=2, page_size=10)

    assert result.items == mock_items
    assert result.total == 2
    mock_image_repo.list_by_project.assert_called_once_with(project_id=project_id, offset=10, limit=10)
    mock_image_repo.count_by_project.assert_called_once_with(project_id)


@pytest.mark.asyncio
async def test_delete_image_success(mock_image_repo, mock_storage):
    image_id = uuid4()
    mock_image_repo.get_by_id.return_value = ImageAsset(
        id=image_id,
        project_id=uuid4(),
        type="original",
        filename="test.jpg",
        mime_type="image/jpeg",
        storage_path="path/to/image.jpg",
        thumbnail_path="path/to/thumb.jpg"
    )

    use_case = DeleteImageUseCase(image_repo=mock_image_repo, storage=mock_storage)
    await use_case.execute(image_id)

    mock_image_repo.get_by_id.assert_called_once_with(image_id)
    assert mock_storage.delete.call_count == 2
    mock_storage.delete.assert_any_call("path/to/image.jpg")
    mock_storage.delete.assert_any_call("path/to/thumb.jpg")
    mock_image_repo.delete.assert_called_once_with(image_id)


@pytest.mark.asyncio
async def test_delete_image_not_found(mock_image_repo, mock_storage):
    image_id = uuid4()
    mock_image_repo.get_by_id.return_value = None

    use_case = DeleteImageUseCase(image_repo=mock_image_repo, storage=mock_storage)

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(image_id)
