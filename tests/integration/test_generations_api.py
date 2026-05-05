import pytest
from httpx import AsyncClient
import io
from PIL import Image

@pytest.fixture
def mock_image_bytes():
    img = Image.new('RGB', (800, 600), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

@pytest.mark.asyncio
async def test_create_generation_returns_202(test_client, async_session, mock_image_bytes):
    # Setup: Create project and image first
    project_response = test_client.post(
        "/api/v1/projects",
        json={"name": "Test Project", "description": "Test Description"}
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # Upload image
    image_response = test_client.post(
        f"/api/v1/projects/{project_id}/images",
        files={"file": ("test.jpg", mock_image_bytes, "image/jpeg")}
    )
    assert image_response.status_code == 201
    image_id = image_response.json()["id"]

    # Request generation
    generation_response = test_client.post(
        f"/api/v1/images/{image_id}/generations",
        json={
            "mode": "commercial_enhancement",
            "provider": "openai"
        }
    )

    assert generation_response.status_code == 202
    data = generation_response.json()
    assert "id" in data
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_create_generation_invalid_mode_returns_422(test_client):
    response = test_client.post(
        "/api/v1/images/00000000-0000-0000-0000-000000000000/generations",
        json={
            "mode": "invalid_mode",
            "provider": "openai"
        }
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_generation_returns_200(test_client, async_session, mock_image_bytes):
    # Setup: Create project and image first
    project_response = test_client.post(
        "/api/v1/projects",
        json={"name": "Test Project"}
    )
    project_id = project_response.json()["id"]

    image_response = test_client.post(
        f"/api/v1/projects/{project_id}/images",
        files={"file": ("test.jpg", mock_image_bytes, "image/jpeg")}
    )
    image_id = image_response.json()["id"]

    # Request generation
    generation_response = test_client.post(
        f"/api/v1/images/{image_id}/generations",
        json={"mode": "commercial_enhancement", "provider": "openai"}
    )
    generation_id = generation_response.json()["id"]

    # Get generation
    get_response = test_client.get(f"/api/v1/generations/{generation_id}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == generation_id
    assert get_response.json()["mode"] == "commercial_enhancement"

@pytest.mark.asyncio
async def test_list_generations_paginated(test_client, async_session, mock_image_bytes):
    # Setup: Create project and image first
    project_response = test_client.post("/api/v1/projects", json={"name": "Test"})
    project_id = project_response.json()["id"]

    image_response = test_client.post(
        f"/api/v1/projects/{project_id}/images",
        files={"file": ("test.jpg", mock_image_bytes, "image/jpeg")}
    )
    image_id = image_response.json()["id"]

    # Create multiple generations
    for _ in range(3):
        test_client.post(
            f"/api/v1/images/{image_id}/generations",
            json={"mode": "commercial_enhancement", "provider": "openai"}
        )

    # List generations
    list_response = test_client.get(f"/api/v1/images/{image_id}/generations?page=1&page_size=2")

    assert list_response.status_code == 200
    data = list_response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
