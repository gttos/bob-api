import pytest
import uuid
from sqlalchemy import inspect

from app.api.main import app
from app.config.settings import settings
from app.domain.shared.exceptions import ResourceNotFoundError, DomainValidationError
from app.infrastructure.persistence.models import ProjectModel

def test_health_endpoint(test_client):
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["env"] == settings.APP_ENV
    assert data["version"] == "1.0.0"

def test_correlation_id_is_returned_in_response_header(test_client):
    response = test_client.get("/api/v1/health")
    correlation_id = response.headers.get("X-Correlation-ID")
    assert correlation_id is not None
    # Validate UUID
    assert uuid.UUID(correlation_id)

def test_correlation_id_from_request_is_echoed(test_client):
    headers = {"X-Correlation-ID": "test-correlation-123"}
    response = test_client.get("/api/v1/health", headers=headers)
    assert response.headers.get("X-Correlation-ID") == "test-correlation-123"

def test_resource_not_found_exception_returns_404(test_client):
    @app.get("/api/v1/test-404")
    def trigger_404():
        raise ResourceNotFoundError("test not found")

    response = test_client.get("/api/v1/test-404")
    assert response.status_code == 404
    assert response.json() == {"detail": "test not found"}

def test_domain_validation_exception_returns_422(test_client):
    @app.get("/api/v1/test-422")
    def trigger_422():
        raise DomainValidationError("invalid input")

    response = test_client.get("/api/v1/test-422")
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid input"}

def test_settings_defaults():
    assert settings.RATE_LIMIT_ENABLED is False
    assert settings.APP_ENV == "development"
    assert settings.MAX_UPLOAD_SIZE_MB == 20
    assert settings.STORAGE_BACKEND == "local"

@pytest.mark.asyncio
async def test_all_tables_created_by_migration(async_engine):
    # Using async_engine fixture which creates all tables in memory SQLite
    def sync_get_tables(conn):
        inspector = inspect(conn)
        return inspector.get_table_names()

    async with async_engine.connect() as conn:
        tables = await conn.run_sync(sync_get_tables)

    expected_tables = {
        "projects",
        "image_assets",
        "scene_inventories",
        "generation_requests",
        "image_variants",
        "evaluations"
    }

    for table in expected_tables:
        assert table in tables, f"Table '{table}' is missing from the database."

def test_projects_table_has_owner_id_column():
    # We can inspect the SQLAlchemy model directly to verify columns
    columns = ProjectModel.__table__.columns
    assert "owner_id" in columns
    assert columns["owner_id"].nullable is True
