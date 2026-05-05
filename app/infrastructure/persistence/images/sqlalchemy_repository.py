from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repository_ports import ImageRepository
from app.domain.images.entities import ImageAsset
from app.infrastructure.persistence.models import ImageAssetModel


class SQLAlchemyImageRepository(ImageRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, image: ImageAsset) -> ImageAsset:
        model = await self._session.get(ImageAssetModel, image.id)
        if model is None:
            model = self._to_model(image)
            self._session.add(model)
        else:
            model.project_id = image.project_id
            model.type = image.type
            model.filename = image.filename
            model.mime_type = image.mime_type
            model.width = image.width
            model.height = image.height
            model.storage_path = image.storage_path
            model.thumbnail_path = image.thumbnail_path
            model.created_at = image.created_at

        await self._session.flush()
        return self._to_entity(model)

    async def get_by_id(self, image_id: UUID) -> ImageAsset | None:
        model = await self._session.get(ImageAssetModel, image_id)
        if model is None:
            return None
        return self._to_entity(model)

    async def list_by_project(self, project_id: UUID, offset: int = 0, limit: int = 20) -> list[ImageAsset]:
        result = await self._session.execute(
            select(ImageAssetModel)
            .where(ImageAssetModel.project_id == project_id)
            .order_by(ImageAssetModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars()]

    async def count_by_project(self, project_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(ImageAssetModel.id))
            .where(ImageAssetModel.project_id == project_id)
        )
        return result.scalar_one()

    async def delete(self, image_id: UUID) -> None:
        model = await self._session.get(ImageAssetModel, image_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()

    def _to_entity(self, model: ImageAssetModel) -> ImageAsset:
        return ImageAsset(
            id=model.id,
            project_id=model.project_id,
            type=model.type,
            filename=model.filename,
            mime_type=model.mime_type,
            width=model.width,
            height=model.height,
            storage_path=model.storage_path,
            thumbnail_path=model.thumbnail_path,
            created_at=model.created_at,
        )

    def _to_model(self, entity: ImageAsset) -> ImageAssetModel:
        return ImageAssetModel(
            id=entity.id,
            project_id=entity.project_id,
            type=entity.type,
            filename=entity.filename,
            mime_type=entity.mime_type,
            width=entity.width,
            height=entity.height,
            storage_path=entity.storage_path,
            thumbnail_path=entity.thumbnail_path,
            created_at=entity.created_at,
        )
