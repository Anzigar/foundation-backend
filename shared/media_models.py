from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.sql import func

from shared.database import Base

class Media(Base):
    """Media model for managing uploaded files."""
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    file_key = Column(String(255), nullable=False, unique=True)  # S3 key
    url = Column(String(255), nullable=False)  # Public URL
    thumbnail_url = Column(String(255))  # Thumbnail URL for images
    file_type = Column(String(50))  # image, video, document
    file_size = Column(Integer)  # File size in bytes
    mime_type = Column(String(100))  # MIME type
    tags = Column(JSON, default=list)  # Tags for organization
    folder = Column(String(255))  # Folder/category
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
