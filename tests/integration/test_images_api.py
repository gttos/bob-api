import pytest
from httpx import AsyncClient
import io
from uuid import uuid4
from PIL import Image
import os

from app.domain.projects.entities import Project
from app.infrastructure.persistence.models import ProjectModel, ImageAssetModel

@pytest.fixture
def mock_image_bytes():
    img = Image.new('RGB', (800, 600), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()


@pytest.mark.asyncio
async def test_upload_image_returns_201(test_client, async_session, mock_image_bytes):
    # Setup - Create project first
    project_id = uuid4()
    project = ProjectModel(id=project_id, name="Test Project", owner_id=uuid4())
    async_session.add(project)
    await async_session.commit()

    file_data = {
        "file": ("test_image.jpg", mock_image_bytes, "image/jpeg")
    }

    response = test_client.post(f"/api/v1/projects/{project_id}/images", files=file_data)

    assert response.status_code == 201
    data = response.json()

    assert data["filename"] == "test_image.jpg"
    assert data["mime_type"] == "image/jpeg"
    assert data["width"] == 800
    assert data["height"] == 600
    assert data["project_id"] == str(project_id)
    assert data["url"] != ""
    assert data["thumbnail_url"] != ""
    assert "id" in data
    assert "storage_path" not in data


@pytest.mark.asyncio
async def test_upload_invalid_mime_returns_422(test_client, async_session, mock_image_bytes):
    project_id = uuid4()
    project = ProjectModel(id=project_id, name="Test Project", owner_id=uuid4())
    async_session.add(project)
    await async_session.commit()

    file_data = {
        "file": ("test_image.txt", mock_image_bytes, "text/plain")
    }

    response = test_client.post(f"/api/v1/projects/{project_id}/images", files=file_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_image_returns_200(test_client, async_session):
    # Setup - Create project and image
    project_id = uuid4()
    image_id = uuid4()

    project = ProjectModel(id=project_id, name="Test Project", owner_id=uuid4())
    async_session.add(project)

    image = ImageAssetModel(
        id=image_id,
        project_id=project_id,
        type="original",
        filename="test.jpg",
        mime_type="image/jpeg",
        width=800,
        height=600,
        storage_path="path/to/test.jpg",
        thumbnail_path="path/to/test_thumb.jpg"
    )
    async_session.add(image)
    await async_session.commit()

    response = test_client.get(f"/api/v1/images/{image_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(image_id)
    assert data["filename"] == "test.jpg"
    # Ensure storage paths are not exposed directly, but generated urls are
    assert "storage_path" not in data
    assert "thumbnail_path" not in data
    assert "url" in data
    assert "thumbnail_url" in data


@pytest.mark.asyncio
async def test_list_images_returns_paginated(test_client, async_session):
    project_id = uuid4()
    project = ProjectModel(id=project_id, name="Test Project", owner_id=uuid4())
    async_session.add(project)

    # Add 3 images
    for i in range(3):
        image = ImageAssetModel(
            id=uuid4(),
            project_id=project_id,
            type="original",
            filename=f"test_{i}.jpg",
            mime_type="image/jpeg",
            width=800,
            height=600,
            storage_path=f"path/to/test_{i}.jpg",
            thumbnail_path=f"path/to/test_{i}_thumb.jpg"
        )
        async_session.add(image)

    await async_session.commit()

    response = test_client.get(f"/api/v1/projects/{project_id}/images?page=1&page_size=2")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_delete_image_returns_204(test_client, async_session):
    project_id = uuid4()
    image_id = uuid4()

    project = ProjectModel(id=project_id, name="Test Project", owner_id=uuid4())
    async_session.add(project)

    image = ImageAssetModel(
        id=image_id,
        project_id=project_id,
        type="original",
        filename="test.jpg",
        mime_type="image/jpeg",
        width=800,
        height=600,
        storage_path="path/to/test.jpg",
        thumbnail_path="path/to/test_thumb.jpg"
    )
    async_session.add(image)
    await async_session.commit()

    response = test_client.delete(f"/api/v1/images/{image_id}")

    assert response.status_code == 204

    # Verify deletion
    verify_resp = test_client.get(f"/api/v1/images/{image_id}")
    assert verify_resp.status_code == 404


@pytest.mark.asyncio
async def test_download_image_returns_file(test_client, async_session, mock_image_bytes):
    # Setup - Create project first
    project_id = uuid4()
    project = ProjectModel(id=project_id, name="Test Project", owner_id=uuid4())
    async_session.add(project)
    await async_session.commit()

    # Upload image
    file_data = {
        "file": ("test_image.jpg", mock_image_bytes, "image/jpeg")
    }
    upload_response = test_client.post(f"/api/v1/projects/{project_id}/images", files=file_data)
    assert upload_response.status_code == 201
    image_id = upload_response.json()["id"]

    # Download image
    download_response = test_client.get(f"/api/v1/images/{image_id}/download")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "image/jpeg"
