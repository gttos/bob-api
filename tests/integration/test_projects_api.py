import pytest
from uuid import uuid4
from sqlalchemy.orm import configure_mappers

# This is necessary because of the use_alter issue with Circular references in SQLAlchemy Models
from app.infrastructure.persistence.models import ProjectModel
try:
    configure_mappers()
except Exception:
    pass

@pytest.mark.asyncio
async def test_create_project_returns_201(test_client):
    response = test_client.post("/api/v1/projects", json={
        "name": "Test Project",
        "description": "A test"
    })
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Project"
    assert data["description"] == "A test"
    assert "created_at" in data
    assert "updated_at" in data

@pytest.mark.asyncio
async def test_create_project_without_name_returns_422(test_client):
    response = test_client.post("/api/v1/projects", json={
        "description": "no name"
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_project_returns_200(test_client):
    create_resp = test_client.post("/api/v1/projects", json={
        "name": "To be retrieved",
        "description": "A test"
    })
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    response = test_client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "To be retrieved"

@pytest.mark.asyncio
async def test_get_nonexistent_project_returns_404(test_client):
    random_id = str(uuid4())
    response = test_client.get(f"/api/v1/projects/{random_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_list_projects_returns_paginated(test_client):
    for i in range(3):
        test_client.post("/api/v1/projects", json={
            "name": f"Project {i}",
        })

    response = test_client.get("/api/v1/projects?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    # NOTE: Test total could be >= 3 depending on previous tests if they share the db,
    # but our fixtures typically isolate it or run it all in one run.
    assert data["total"] >= 3
    assert data["page"] == 1
    assert data["page_size"] == 2

@pytest.mark.asyncio
async def test_update_project_partial(test_client):
    create_resp = test_client.post("/api/v1/projects", json={
        "name": "To be updated",
        "description": "Desc"
    })
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    response = test_client.patch(f"/api/v1/projects/{project_id}", json={
        "name": "Updated"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["description"] == "Desc"

@pytest.mark.asyncio
async def test_delete_project_returns_204(test_client):
    create_resp = test_client.post("/api/v1/projects", json={
        "name": "To be deleted"
    })
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    response = test_client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204

    get_resp = test_client.get(f"/api/v1/projects/{project_id}")
    assert get_resp.status_code == 404
