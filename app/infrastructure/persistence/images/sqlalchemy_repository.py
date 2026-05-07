from uuid import UUID
from datetime import datetime, timezone

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
        if model is None or model.deleted_at is not None:
            return None
        return self._to_entity(model)

    async def list_by_project(self, project_id: UUID, offset: int = 0, limit: int = 20) -> list[ImageAsset]:
        result = await self._session.execute(
            select(ImageAssetModel)
            .where(ImageAssetModel.project_id == project_id)
            .where(ImageAssetModel.deleted_at.is_(None))
            .order_by(ImageAssetModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars()]

    async def count_by_project(self, project_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(ImageAssetModel.id))
            .where(ImageAssetModel.project_id == project_id)
            .where(ImageAssetModel.deleted_at.is_(None))
        )
        return result.scalar_one()

    async def list_by_space(self, space_id: UUID, offset: int = 0, limit: int = 20) -> list[ImageAsset]:
        result = await self._session.execute(
            select(ImageAssetModel)
            .where(ImageAssetModel.space_id == space_id)
            .where(ImageAssetModel.deleted_at.is_(None))
            .order_by(ImageAssetModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars()]

    async def count_by_space(self, space_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(ImageAssetModel.id))
            .where(ImageAssetModel.space_id == space_id)
            .where(ImageAssetModel.deleted_at.is_(None))
        )
        return result.scalar_one()

    async def delete(self, image_id: UUID) -> None:
        model = await self._session.get(ImageAssetModel, image_id)
        if model is not None:
            model.deleted_at = datetime.now(timezone.utc)
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
            space_id=model.space_id,
            parent_image_id=model.parent_image_id,
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
            space_id=entity.space_id,
            parent_image_id=entity.parent_image_id,
            created_at=entity.created_at,
        )
