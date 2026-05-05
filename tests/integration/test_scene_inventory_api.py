import pytest
from uuid import uuid4

@pytest.mark.asyncio
async def test_request_analysis_returns_202(test_client, async_session):
    # Create project and image directly or via API
    # Here we can just use the DB to insert an image
    from app.infrastructure.persistence.models import ProjectModel, ImageAssetModel
    project_id = uuid4()
    image_id = uuid4()

    project = ProjectModel(id=project_id, name="Test")
    image = ImageAssetModel(id=image_id, project_id=project_id, type="original", filename="a.jpg", mime_type="image/jpeg", storage_path="a.jpg")

    async_session.add(project)
    async_session.add(image)
    await async_session.commit()

    response = test_client.post(f"/api/v1/images/{image_id}/scene-inventory")

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "pending"
    assert data["image_id"] == str(image_id)

@pytest.mark.asyncio
async def test_get_inventory_returns_404_when_not_exists(test_client):
    response = test_client.get(f"/api/v1/images/{uuid4()}/scene-inventory")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_inventory_returns_200_when_exists(test_client, async_session):
    from app.infrastructure.persistence.models import ProjectModel, ImageAssetModel, SceneInventoryModel
    project_id = uuid4()
    image_id = uuid4()

    project = ProjectModel(id=project_id, name="Test")
    image = ImageAssetModel(id=image_id, project_id=project_id, type="original", filename="a.jpg", mime_type="image/jpeg", storage_path="a.jpg")
    inv = SceneInventoryModel(image_id=image_id, status="completed", inventory_data={"scene_type": "living_room"})

    async_session.add(project)
    async_session.add(image)
    async_session.add(inv)
    await async_session.commit()

    response = test_client.get(f"/api/v1/images/{image_id}/scene-inventory")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["inventory_data"] == {"scene_type": "living_room"}
