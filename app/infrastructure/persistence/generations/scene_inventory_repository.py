from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repository_ports import SceneInventoryRepository
from app.domain.generations.entities import SceneInventory
from app.infrastructure.persistence.models import SceneInventoryModel

class SQLAlchemySceneInventoryRepository(SceneInventoryRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_model(self, entity: SceneInventory) -> SceneInventoryModel:
        return SceneInventoryModel(
            id=entity.id,
            image_id=entity.image_id,
            inventory_data=entity.inventory_data,
            status=entity.status,
            error_message=entity.error_message,
            provider=entity.provider,
            model=entity.model,
            created_at=entity.created_at,
            completed_at=entity.completed_at
        )

    def _to_entity(self, model: SceneInventoryModel) -> SceneInventory:
        return SceneInventory(
            id=model.id,
            image_id=model.image_id,
            inventory_data=model.inventory_data,
            status=model.status,
            error_message=model.error_message,
            provider=model.provider,
            model=model.model,
            created_at=model.created_at,
            completed_at=model.completed_at
        )

    async def save(self, inventory: SceneInventory) -> SceneInventory:
        model = await self.session.get(SceneInventoryModel, inventory.id)
        if model:
            model.status = inventory.status
            model.inventory_data = inventory.inventory_data
            model.error_message = inventory.error_message
            model.provider = inventory.provider
            model.model = inventory.model
            model.completed_at = inventory.completed_at
        else:
            model = self._to_model(inventory)
            self.session.add(model)

        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_image_id(self, image_id: UUID) -> SceneInventory | None:
        query = select(SceneInventoryModel).where(SceneInventoryModel.image_id == image_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)
