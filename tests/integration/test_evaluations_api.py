import pytest
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_evaluation_returns_201(test_client, async_session):
    from app.infrastructure.persistence.models import ProjectModel, ImageAssetModel, GenerationRequestModel, ImageVariantModel
    project_id = uuid4()
    image_id = uuid4()
    req_id = uuid4()
    variant_id = uuid4()

    async_session.add(ProjectModel(id=project_id, name="Test"))
    async_session.add(ImageAssetModel(id=image_id, project_id=project_id, type="original", filename="a.jpg", mime_type="image/jpeg", storage_path="a.jpg"))
    async_session.add(GenerationRequestModel(id=req_id, source_image_id=image_id, mode="commercial_enhancement", provider="openai"))
    async_session.add(ImageVariantModel(id=variant_id, source_image_id=image_id, generation_request_id=req_id, image_asset_id=image_id, version_number=1, provider="openai"))
    await async_session.commit()

    payload = {
        "geometry": 5, "architecture": 4, "perspective": 3, "photorealism": 5,
        "commercial_quality": 4, "instruction_obedience": 5, "style_differentiation": 4,
        "localized_edit_accuracy": 5, "human_retouch_needed": 1, "construction_company_fit": 5,
        "verdict": "approved", "notes": "Great"
    }

    response = test_client.post(f"/api/v1/image-variants/{variant_id}/evaluation", json=payload)

    assert response.status_code == 201
    assert response.json()["verdict"] == "approved"

@pytest.mark.asyncio
async def test_create_evaluation_invalid_score_returns_422(test_client):
    payload = {
        "geometry": 6, "architecture": 4, "perspective": 3, "photorealism": 5,
        "commercial_quality": 4, "instruction_obedience": 5, "style_differentiation": 4,
        "localized_edit_accuracy": 5, "human_retouch_needed": 1, "construction_company_fit": 5,
        "verdict": "approved"
    }
    response = test_client.post(f"/api/v1/image-variants/{uuid4()}/evaluation", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_evaluation_returns_200(test_client, async_session):
    from app.infrastructure.persistence.models import ProjectModel, ImageAssetModel, GenerationRequestModel, ImageVariantModel, EvaluationModel
    project_id = uuid4()
    image_id = uuid4()
    req_id = uuid4()
    variant_id = uuid4()
    eval_id = uuid4()

    async_session.add(ProjectModel(id=project_id, name="Test"))
    async_session.add(ImageAssetModel(id=image_id, project_id=project_id, type="original", filename="a.jpg", mime_type="image/jpeg", storage_path="a.jpg"))
    async_session.add(GenerationRequestModel(id=req_id, source_image_id=image_id, mode="commercial_enhancement", provider="openai"))
    async_session.add(ImageVariantModel(id=variant_id, source_image_id=image_id, generation_request_id=req_id, image_asset_id=image_id, version_number=1, provider="openai"))
    async_session.add(EvaluationModel(id=eval_id, variant_id=variant_id, geometry=5, architecture=4, perspective=3, photorealism=5, commercial_quality=4, instruction_obedience=5, style_differentiation=4, localized_edit_accuracy=5, human_retouch_needed=1, construction_company_fit=5, verdict="approved"))
    await async_session.commit()

    response = test_client.get(f"/api/v1/image-variants/{variant_id}/evaluation")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_update_evaluation_partial_returns_200(test_client, async_session):
    from app.infrastructure.persistence.models import ProjectModel, ImageAssetModel, GenerationRequestModel, ImageVariantModel, EvaluationModel
    project_id = uuid4()
    image_id = uuid4()
    req_id = uuid4()
    variant_id = uuid4()
    eval_id = uuid4()

    async_session.add(ProjectModel(id=project_id, name="Test"))
    async_session.add(ImageAssetModel(id=image_id, project_id=project_id, type="original", filename="a.jpg", mime_type="image/jpeg", storage_path="a.jpg"))
    async_session.add(GenerationRequestModel(id=req_id, source_image_id=image_id, mode="commercial_enhancement", provider="openai"))
    async_session.add(ImageVariantModel(id=variant_id, source_image_id=image_id, generation_request_id=req_id, image_asset_id=image_id, version_number=1, provider="openai"))
    async_session.add(EvaluationModel(id=eval_id, variant_id=variant_id, geometry=1, architecture=1, perspective=1, photorealism=1, commercial_quality=1, instruction_obedience=1, style_differentiation=1, localized_edit_accuracy=1, human_retouch_needed=1, construction_company_fit=1, verdict="rejected"))
    await async_session.commit()

    response = test_client.patch(f"/api/v1/evaluations/{eval_id}", json={"geometry": 5, "verdict": "approved"})
    assert response.status_code == 200
    assert response.json()["geometry"] == 5
    assert response.json()["architecture"] == 1
    assert response.json()["verdict"] == "approved"

@pytest.mark.asyncio
async def test_comparison_endpoint_returns_original_and_variants(test_client, async_session):
    from app.infrastructure.persistence.models import ProjectModel, ImageAssetModel, GenerationRequestModel, ImageVariantModel
    project_id = uuid4()
    image_id = uuid4()
    req_id = uuid4()
    variant_id = uuid4()
    var_image_id = uuid4()

    async_session.add(ProjectModel(id=project_id, name="Test"))
    async_session.add(ImageAssetModel(id=image_id, project_id=project_id, type="original", filename="a.jpg", mime_type="image/jpeg", storage_path="a.jpg"))
    async_session.add(ImageAssetModel(id=var_image_id, project_id=project_id, type="generated", filename="b.jpg", mime_type="image/jpeg", storage_path="b.jpg"))
    async_session.add(GenerationRequestModel(id=req_id, source_image_id=image_id, mode="commercial_enhancement", provider="openai", output_image_id=var_image_id, output_variant_id=variant_id))
    async_session.add(ImageVariantModel(id=variant_id, source_image_id=image_id, generation_request_id=req_id, image_asset_id=var_image_id, version_number=1, provider="openai"))
    await async_session.commit()

    response = test_client.get(f"/api/v1/images/{image_id}/comparison")
    assert response.status_code == 200
    data = response.json()
    assert "original" in data
    assert "variants" in data
    assert len(data["variants"]) == 1
    assert data["variants"][0]["generation_metadata"]["mode"] == "commercial_enhancement"
