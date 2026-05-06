from uuid import UUID

from app.application.ports.repository_ports import GenerationRepository, ImageRepository
from app.application.ports.storage_port import StoragePort
from app.domain.shared.exceptions import ResourceNotFoundError

class GetComparisonUseCase:
    def __init__(self, image_repo: ImageRepository, generation_repo: GenerationRepository, storage: StoragePort):
        self.image_repo = image_repo
        self.generation_repo = generation_repo
        self.storage = storage

    async def execute(self, image_id: UUID) -> dict:
        original_image = await self.image_repo.get_by_id(image_id)
        if not original_image:
             raise ResourceNotFoundError(f"Image {image_id} not found")

        variants = await self.generation_repo.list_by_image(image_id, offset=0, limit=100) # Gets GenerationRequests

        # Actually we need ImageVariants for comparison, they are generated variants of a specific image.
        # But wait, GenerationRepository has list_by_image which returns requests, we can then fetch output_variants.
        # Alternatively, we can just fetch all valid requests and construct the response.

        variants_response = []
        for req in sorted(variants, key=lambda x: x.created_at):
             if req.output_variant_id:
                  variant = await self.generation_repo.get_variant_by_id(req.output_variant_id)
                  variant_image = await self.image_repo.get_by_id(req.output_image_id) if req.output_image_id else None

                  if variant and variant_image:
                       variants_response.append({
                           "id": str(variant.id),
                           "version_number": variant.version_number,
                           "provider": variant.provider,
                           "model": variant.model,
                           "url": self.storage.get_url(variant_image.storage_path),
                           "generation_metadata": {
                               "mode": req.mode,
                               "preset": req.preset,
                               "provider": req.provider
                           }
                       })

        # Ensure ordered by version_number ASC
        variants_response.sort(key=lambda x: x["version_number"])

        return {
            "original": {
                "id": str(original_image.id),
                "url": self.storage.get_url(original_image.storage_path)
            },
            "variants": variants_response
        }
