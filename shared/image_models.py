"""Shared image models for consistent image handling across all content types."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON, CheckConstraint, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from shared.database import Base

class ImageType(enum.Enum):
    """Enum for different image types."""
    FEATURED = "featured"
    GALLERY = "gallery"
    THUMBNAIL = "thumbnail"
    OG_IMAGE = "og_image"
    BANNER = "banner"

class ContentImageType(enum.Enum):
    """Enum for content types that can have images."""
    BLOG = "blog"
    NEWS = "news"
    EVENT = "event"
    PROJECT = "project"

class ContentImage(Base):
    """Shared image model for all content types."""
    __tablename__ = "content_images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    content_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # ID of the content item
    content_type = Column(Enum(ContentImageType), nullable=False, index=True)  # Type of content
    image_type = Column(Enum(ImageType), nullable=False, default=ImageType.GALLERY)
    
    # Image details
    title = Column(String(255))
    description = Column(Text)
    alt_text = Column(String(255))  # For accessibility
    image_url = Column(String(255), CheckConstraint("image_url ~ '^https?://'"), nullable=False)
    thumbnail_url = Column(String(255), CheckConstraint("thumbnail_url ~ '^https?://'"))
    
    # Image metadata
    file_size = Column(String(50))  # e.g., "2.5MB"
    dimensions = Column(String(50))  # e.g., "1920x1080"
    format = Column(String(10))  # e.g., "jpeg", "png", "webp"
    
    # Ordering and display
    order_index = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ContentImage(content_type='{self.content_type.value}', image_type='{self.image_type.value}', title='{self.title}')>"

class ImageTag(Base):
    """Tags for images to enable better organization and search."""
    __tablename__ = "image_tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    color = Column(String(7))  # Hex color code
    created_at = Column(DateTime, default=func.now())

class ContentImageTag(Base):
    """Many-to-many relationship between images and tags."""
    __tablename__ = "content_image_tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id = Column(UUID(as_uuid=True), ForeignKey("content_images.id"), nullable=False)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("image_tags.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    image = relationship("ContentImage")
    tag = relationship("ImageTag")
