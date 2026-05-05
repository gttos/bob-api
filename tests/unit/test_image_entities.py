import pytest
import io
from PIL import Image
from uuid import UUID, uuid4
from datetime import datetime

from app.domain.images.entities import ImageAsset
from app.infrastructure.thumbnail.pillow_thumbnail import ThumbnailService


def test_image_asset_creation():
    project_id = uuid4()
    asset = ImageAsset(
        project_id=project_id,
        type="original",
        filename="test.jpg",
        mime_type="image/jpeg"
    )
    assert asset.project_id == project_id
    assert asset.type == "original"
    assert asset.filename == "test.jpg"
    assert asset.mime_type == "image/jpeg"
    assert isinstance(asset.id, UUID)
    assert isinstance(asset.created_at, datetime)
    assert asset.width is None
    assert asset.height is None
    assert asset.storage_path == ""
    assert asset.thumbnail_path is None


def test_thumbnail_service():
    # Create a dummy image
    img = Image.new('RGB', (800, 600), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()

    service = ThumbnailService()

    # Test dimension extraction
    width, height = service.get_image_dimensions(img_bytes)
    assert width == 800
    assert height == 600

    # Test thumbnail generation
    thumbnail_bytes = service.generate(img_bytes, max_size=(400, 400))
    thumb_img = Image.open(io.BytesIO(thumbnail_bytes))

    # The aspect ratio is 800/600 = 1.33
    # The max size is 400x400
    # The height will be 400 / 1.33 = 300
    assert thumb_img.width == 400
    assert thumb_img.height == 300
    assert thumb_img.format == 'JPEG'
