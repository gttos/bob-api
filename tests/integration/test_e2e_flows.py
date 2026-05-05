import pytest
import io
from PIL import Image
from uuid import uuid4

def create_test_image():
    # Helper to create a valid JPEG in memory
    img_byte_arr = io.BytesIO()
    img = Image.new('RGB', (100, 100), color='red')
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

@pytest.mark.asyncio
async def test_full_flow_create_project_upload_image(test_client):
    # 1. Create Project
    response = test_client.post("/api/v1/projects", json={"name": "My Project"})
    assert response.status_code == 201
    project_id = response.json()["id"]

    # 2. Upload Image
    img_bytes = create_test_image()
    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    response = test_client.post(f"/api/v1/projects/{project_id}/images", files=files)
    assert response.status_code == 201
    image_id = response.json()["id"]
    url = response.json()["url"]
    assert "thumbnail_url" in response.json()
    assert url.startswith("/media/")

@pytest.mark.asyncio
async def test_full_flow_generation_request(test_client):
    response = test_client.post("/api/v1/projects", json={"name": "Proj Gen"})
    project_id = response.json()["id"]

    img_bytes = create_test_image()
    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    response = test_client.post(f"/api/v1/projects/{project_id}/images", files=files)
    image_id = response.json()["id"]

    # 3. Request Generation
    response = test_client.post(
        f"/api/v1/images/{image_id}/generations",
        json={"mode": "commercial_enhancement", "provider": "openai"}
    )
    assert response.status_code == 202
    assert response.json()["status"] == "pending"
    gen_id = response.json()["id"]

    # 4. Get Generation Status
    response = test_client.get(f"/api/v1/generations/{gen_id}")
    assert response.status_code == 200
    assert "status" in response.json()

@pytest.mark.asyncio
async def test_full_flow_comparison_after_generation(test_client, async_session):
    from app.infrastructure.persistence.models import ProjectModel, ImageAssetModel, GenerationRequestModel, ImageVariantModel
    project_id = uuid4()
    image_id = uuid4()
    gen_id = uuid4()
    var_image_id = uuid4()
    variant_id = uuid4()

    async_session.add(ProjectModel(id=project_id, name="Test Compare"))
    async_session.add(ImageAssetModel(id=image_id, project_id=project_id, type="original", filename="a.jpg", mime_type="image/jpeg", storage_path="a.jpg"))
    async_session.add(ImageAssetModel(id=var_image_id, project_id=project_id, type="generated", filename="b.jpg", mime_type="image/jpeg", storage_path="b.jpg"))
    async_session.add(GenerationRequestModel(id=gen_id, source_image_id=image_id, mode="commercial_enhancement", provider="openai", output_image_id=var_image_id, output_variant_id=variant_id))
    async_session.add(ImageVariantModel(id=variant_id, source_image_id=image_id, generation_request_id=gen_id, image_asset_id=var_image_id, version_number=1, provider="openai"))
    await async_session.commit()

    response = test_client.get(f"/api/v1/images/{image_id}/comparison")
    assert response.status_code == 200
    data = response.json()
    assert "url" in data["original"]
    assert "storage_path" not in data["original"]
    assert len(data["variants"]) == 1
    assert "url" in data["variants"][0]
    assert "storage_path" not in data["variants"][0]

@pytest.mark.asyncio
async def test_full_flow_evaluation(test_client, async_session):
    from app.infrastructure.persistence.models import ProjectModel, ImageAssetModel, GenerationRequestModel, ImageVariantModel
    project_id = uuid4()
    image_id = uuid4()
    gen_id = uuid4()
    var_image_id = uuid4()
    variant_id = uuid4()

    async_session.add(ProjectModel(id=project_id, name="Test Eval"))
    async_session.add(ImageAssetModel(id=image_id, project_id=project_id, type="original", filename="a.jpg", mime_type="image/jpeg", storage_path="a.jpg"))
    async_session.add(ImageAssetModel(id=var_image_id, project_id=project_id, type="generated", filename="b.jpg", mime_type="image/jpeg", storage_path="b.jpg"))
    async_session.add(GenerationRequestModel(id=gen_id, source_image_id=image_id, mode="commercial_enhancement", provider="openai", output_image_id=var_image_id, output_variant_id=variant_id))
    async_session.add(ImageVariantModel(id=variant_id, source_image_id=image_id, generation_request_id=gen_id, image_asset_id=var_image_id, version_number=1, provider="openai"))
    await async_session.commit()

    eval_payload = {
        "geometry": 5, "architecture": 4, "perspective": 3, "photorealism": 5,
        "commercial_quality": 4, "instruction_obedience": 5, "style_differentiation": 4,
        "localized_edit_accuracy": 5, "human_retouch_needed": 1, "construction_company_fit": 5,
        "verdict": "approved"
    }

    response = test_client.post(f"/api/v1/image-variants/{variant_id}/evaluation", json=eval_payload)
    assert response.status_code == 201
    eval_id = response.json()["id"]

    response = test_client.get(f"/api/v1/image-variants/{variant_id}/evaluation")
    assert response.status_code == 200

    response = test_client.patch(f"/api/v1/evaluations/{eval_id}", json={"geometry": 3})
    assert response.status_code == 200
    assert response.json()["geometry"] == 3

@pytest.mark.asyncio
async def test_rate_limiting_returns_429(monkeypatch, test_client):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_GENERATIONS_PER_DAY", "2")
    import app.config.settings as settings_module
    settings_module.settings.RATE_LIMIT_ENABLED = True
    settings_module.settings.RATE_LIMIT_GENERATIONS_PER_DAY = 2

    # We need to recreate the RateLimitMiddleware with the new settings
    # For testing, we can use a mocked Redis client or rely on a local Redis if available.
    # To keep it completely hermetic and since we don't have fakeredis installed,
    # we'll mock the internal redis client of the middleware
    class MockRedis:
        def __init__(self):
            self.store = {}
        async def incr(self, key):
            self.store[key] = self.store.get(key, 0) + 1
            return self.store[key]
        async def expire(self, key, time):
            pass
        async def ttl(self, key):
            return 3600

    # Apply mock to the middleware instance inside the app
    for middleware in test_client.app.user_middleware:
        if middleware.cls.__name__ == "RateLimitMiddleware":
            # The actual instance might be inside middleware.kwargs or we just mock redis directly
            break

    # Mocking redis.from_url globally
    import redis.asyncio as redis
    def mock_from_url(*args, **kwargs):
        return MockRedis()
    monkeypatch.setattr(redis, "from_url", mock_from_url)

    # With lazy initialization `_get_redis` we only need to patch it
    from app.api.middleware.rate_limit import RateLimitMiddleware
    mock_redis_instance = MockRedis()

    original_get_redis = RateLimitMiddleware._get_redis
    RateLimitMiddleware._get_redis = lambda self: mock_redis_instance

    try:
        response = test_client.post("/api/v1/projects", json={"name": "Rate Limit"})
        project_id = response.json()["id"]

        img_bytes = create_test_image()
        files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
        response = test_client.post(f"/api/v1/projects/{project_id}/images", files=files)
        image_id = response.json()["id"]

        for _ in range(2):
            res = test_client.post(f"/api/v1/images/{image_id}/generations", json={"mode": "commercial_enhancement", "provider": "openai"})
            assert res.status_code == 202

        res = test_client.post(f"/api/v1/images/{image_id}/generations", json={"mode": "commercial_enhancement", "provider": "openai"})
        assert res.status_code == 429
    finally:
        # Restore globally overridden setting so other tests don't break
        RateLimitMiddleware._get_redis = original_get_redis
        settings_module.settings.RATE_LIMIT_ENABLED = False

def test_path_traversal_blocked(test_client):
    response = test_client.get("/media/../../../etc/passwd")
    assert response.status_code != 200
