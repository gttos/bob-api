import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.domain.images.entities import ImageAsset
from app.domain.shared.exceptions import DomainValidationError
from app.api.schemas.images import ImageResponse
from app.application.images.upload_image import UploadImageUseCase, UploadImageCommand
from app.infrastructure.storage.local_storage_adapter import LocalStorageAdapter


# Property 4
@settings(max_examples=100)
@given(filename=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))).map(lambda s: s + ".jpg"))
def test_storage_path_never_exposed_in_response(filename):
    image = ImageAsset(
        project_id=uuid4(),
        type="original",
        filename=filename,
        mime_type="image/jpeg",
        storage_path=f"path/to/{filename}",
        thumbnail_path=f"path/to/{filename}_thumb.jpg"
    )

    mock_storage = MagicMock()
    mock_storage.get_url.side_effect = lambda path: f"/media/{path}"

    response = ImageResponse.from_entity(image, mock_storage)
    dump = response.model_dump()

    assert "storage_path" not in dump
    assert "thumbnail_path" not in dump
    assert response.url.startswith("/media")
    if response.thumbnail_url:
        assert response.thumbnail_url.startswith("/media")


# Property 5
@settings(max_examples=100)
@given(path=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P'))))
def test_url_uses_media_prefix(path):
    storage = LocalStorageAdapter(base_path="/tmp", media_url_prefix="/media")
    clean_path = path.lstrip("/")
    assert storage.get_url(path) == f"/media/{clean_path}"


# Property 23
@settings(max_examples=100)
@given(mime=st.sampled_from(["image/jpeg", "image/png", "image/webp"]))
@pytest.mark.asyncio
async def test_mime_type_validation_valid(mime):
    mock_image_repo = AsyncMock()
    mock_project_repo = AsyncMock()
    mock_storage = AsyncMock()
    mock_thumbnail_service = MagicMock()

    mock_project_repo.get_by_id.return_value = MagicMock()
    mock_thumbnail_service.get_image_dimensions.return_value = (800, 600)
    mock_thumbnail_service.generate.return_value = b"fake"

    use_case = UploadImageUseCase(
        image_repo=mock_image_repo,
        project_repo=mock_project_repo,
        storage=mock_storage,
        thumbnail_service=mock_thumbnail_service,
        allowed_mime_types=["image/jpeg", "image/png", "image/webp"],
        max_upload_size_mb=5
    )

    command = UploadImageCommand(
        project_id=uuid4(),
        filename="test",
        content_type=mime,
        file_data=b"data"
    )

    # Should not raise
    await use_case.execute(command)


@settings(max_examples=100)
@given(mime=st.text(min_size=1).filter(lambda s: s not in {"image/jpeg", "image/png", "image/webp"}))
@pytest.mark.asyncio
async def test_mime_type_validation_invalid(mime):
    mock_image_repo = AsyncMock()
    mock_project_repo = AsyncMock()
    mock_storage = AsyncMock()
    mock_thumbnail_service = MagicMock()

    mock_project_repo.get_by_id.return_value = MagicMock()

    use_case = UploadImageUseCase(
        image_repo=mock_image_repo,
        project_repo=mock_project_repo,
        storage=mock_storage,
        thumbnail_service=mock_thumbnail_service,
        allowed_mime_types=["image/jpeg", "image/png", "image/webp"],
        max_upload_size_mb=5
    )

    command = UploadImageCommand(
        project_id=uuid4(),
        filename="test",
        content_type=mime,
        file_data=b"data"
    )

    with pytest.raises(DomainValidationError):
        await use_case.execute(command)
