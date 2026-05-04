from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.infrastructure.persistence.database import Base

class ProjectModel(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    images = relationship("ImageAssetModel", back_populates="project", cascade="all, delete-orphan")

class ImageAssetModel(Base):
    __tablename__ = "image_assets"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(20), nullable=False)  # "original" | "generated"
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(50), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    storage_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = relationship("ProjectModel", back_populates="images")
    scene_inventory = relationship("SceneInventoryModel", back_populates="image", uselist=False, cascade="all, delete-orphan")
    source_variants = relationship("ImageVariantModel", foreign_keys="ImageVariantModel.source_image_id", back_populates="source_image")

class SceneInventoryModel(Base):
    __tablename__ = "scene_inventories"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    image_id = Column(UUID(as_uuid=True), ForeignKey("image_assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    inventory_data = Column(JSONB, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    provider = Column(String(50), nullable=True)
    model = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    image = relationship("ImageAssetModel", back_populates="scene_inventory")

class GenerationRequestModel(Base):
    __tablename__ = "generation_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    source_image_id = Column(UUID(as_uuid=True), ForeignKey("image_assets.id", ondelete="CASCADE"), nullable=False)
    mode = Column(String(30), nullable=False)
    preset = Column(String(50), nullable=True)
    instructions = Column(Text, nullable=True)
    provider = Column(String(50), nullable=False, default="openai")
    model = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    prompt_final = Column(Text, nullable=True)
    negative_prompt = Column(Text, nullable=True)
    provider_params = Column(JSONB, nullable=True)
    output_image_id = Column(UUID(as_uuid=True), ForeignKey("image_assets.id", ondelete="SET NULL", use_alter=True), nullable=True)
    output_variant_id = Column(UUID(as_uuid=True), ForeignKey("image_variants.id", ondelete="SET NULL", use_alter=True, name="fk_generation_request_output_variant"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    source_image = relationship("ImageAssetModel", foreign_keys=[source_image_id])
    output_variant = relationship("ImageVariantModel", foreign_keys=[output_variant_id], back_populates="generation_request", post_update=True)

class ImageVariantModel(Base):
    __tablename__ = "image_variants"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    source_image_id = Column(UUID(as_uuid=True), ForeignKey("image_assets.id", ondelete="CASCADE"), nullable=False)
    generation_request_id = Column(UUID(as_uuid=True), ForeignKey("generation_requests.id", ondelete="CASCADE"), nullable=False)
    image_asset_id = Column(UUID(as_uuid=True), ForeignKey("image_assets.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    label = Column(String(255), nullable=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    source_image = relationship("ImageAssetModel", foreign_keys=[source_image_id], back_populates="source_variants")
    generation_request = relationship("GenerationRequestModel", foreign_keys=[generation_request_id], back_populates="output_variant")
    image_asset = relationship("ImageAssetModel", foreign_keys=[image_asset_id])
    evaluation = relationship("EvaluationModel", back_populates="variant", uselist=False, cascade="all, delete-orphan")

class EvaluationModel(Base):
    __tablename__ = "evaluations"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("image_variants.id", ondelete="CASCADE"), unique=True, nullable=False)
    geometry = Column(Integer, nullable=False)
    architecture = Column(Integer, nullable=False)
    perspective = Column(Integer, nullable=False)
    photorealism = Column(Integer, nullable=False)
    commercial_quality = Column(Integer, nullable=False)
    instruction_obedience = Column(Integer, nullable=False)
    style_differentiation = Column(Integer, nullable=False)
    localized_edit_accuracy = Column(Integer, nullable=False)
    human_retouch_needed = Column(Integer, nullable=False)
    construction_company_fit = Column(Integer, nullable=False)
    verdict = Column(String(30), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    variant = relationship("ImageVariantModel", back_populates="evaluation")
