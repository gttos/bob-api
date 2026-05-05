from uuid import UUID
from fastapi import APIRouter, Depends, Query, UploadFile, File, Response
from fastapi.responses import StreamingResponse
import io

from app.api.schemas.images import ImageResponse
from app.api.schemas.shared import PaginatedResponse
from app.application.ports.storage_port import StoragePort
from app.application.images.upload_image import UploadImageUseCase, UploadImageCommand
from app.application.images.get_image import GetImageUseCase
from app.application.images.list_images import ListImagesUseCase
from app.application.images.delete_image import DeleteImageUseCase
from app.api.dependencies import (
    get_storage,
    get_upload_image_uc,
    get_get_image_uc,
    get_list_images_uc,
    get_delete_image_uc
)

# Router for project-scoped image endpoints (POST /projects/{id}/images, GET /projects/{id}/images)
project_images_router = APIRouter(prefix="/projects/{project_id}/images", tags=["Images"])

# Router for standalone image endpoints (GET /images/{id}, DELETE /images/{id})
images_router = APIRouter(prefix="/images", tags=["Images"])


@project_images_router.post("", response_model=ImageResponse, status_code=201)
async def upload_image(
    project_id: UUID,
    file: UploadFile = File(...),
    use_case: UploadImageUseCase = Depends(get_upload_image_uc),
    storage: StoragePort = Depends(get_storage)
):
    file_bytes = await file.read()

    command = UploadImageCommand(
        project_id=project_id,
        filename=file.filename or "image.jpg",
        content_type=file.content_type or "image/jpeg",
        file_data=file_bytes
    )

    image_asset = await use_case.execute(command)
    return ImageResponse.from_entity(image_asset, storage)


@project_images_router.get("", response_model=PaginatedResponse[ImageResponse])
async def list_images(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_case: ListImagesUseCase = Depends(get_list_images_uc),
    storage: StoragePort = Depends(get_storage)
):
    result = await use_case.execute(project_id=project_id, page=page, page_size=page_size)
    items = [ImageResponse.from_entity(image, storage) for image in result.items]

    return PaginatedResponse(
        items=items,
        total=result.total,
        page=page,
        page_size=page_size
    )


@images_router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: UUID,
    use_case: GetImageUseCase = Depends(get_get_image_uc),
    storage: StoragePort = Depends(get_storage)
):
    image_asset = await use_case.execute(image_id)
    return ImageResponse.from_entity(image_asset, storage)


@images_router.delete("/{image_id}", status_code=204)
async def delete_image(
    image_id: UUID,
    use_case: DeleteImageUseCase = Depends(get_delete_image_uc)
):
    await use_case.execute(image_id)
    return Response(status_code=204)


@images_router.get("/{image_id}/download")
async def download_image(
    image_id: UUID,
    use_case: GetImageUseCase = Depends(get_get_image_uc),
    storage: StoragePort = Depends(get_storage)
):
    image_asset = await use_case.execute(image_id)

    # Get bytes from storage
    file_bytes = await storage.download(image_asset.storage_path)

    # Create an iterator over the bytes for StreamingResponse
    def iterfile():
        yield file_bytes

    return StreamingResponse(
        iterfile(),
        media_type=image_asset.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{image_asset.filename}"'
        }
    )
