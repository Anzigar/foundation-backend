from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel, field_serializer, model_validator

# Project Image Schemas
class ProjectImageBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_primary: bool = False
    order_index: int = 0

class ProjectImageCreate(BaseModel):
    """
    Schema for creating project images.
    Accepts both 'url' and 'image_url' field names for compatibility.
    Frontend can send either field name - they will be normalized to 'image_url'.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    url: Optional[str] = None  # Alternative field name for compatibility
    is_primary: bool = False
    order_index: int = 0
    
    @model_validator(mode='before')
    @classmethod
    def validate_url_fields(cls, data: Any) -> Any:
        """Handle both 'url' and 'image_url' field names"""
        if isinstance(data, dict):
            # If url is provided but image_url is missing or None, use url as image_url
            if 'url' in data and (data.get('image_url') is None or 'image_url' not in data):
                data['image_url'] = data['url']
        return data

class ProjectImageUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_primary: Optional[bool] = None
    order_index: Optional[int] = None

class ProjectImageResponse(ProjectImageBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    
    @field_serializer('id', 'project_id')
    def serialize_uuid(self, value: UUID) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)

class ProjectCreate(BaseModel):
    title: str
    slug: Optional[str] = None
    description: str
    project_image: Optional[str] = None
    project_image_preview: Optional[str] = None
    image_title: Optional[str] = None
    image_description: Optional[str] = None
    source_link: Optional[str] = None
    live_link: Optional[str] = None
    technologies: List[str] = []
    is_ongoing: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    featured: bool = False
    public: bool = True
    images: Optional[List[ProjectImageCreate]] = []

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    project_image: Optional[str] = None
    project_image_preview: Optional[str] = None
    image_title: Optional[str] = None
    image_description: Optional[str] = None
    source_link: Optional[str] = None
    live_link: Optional[str] = None
    technologies: Optional[List[str]] = None
    is_ongoing: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    featured: Optional[bool] = None
    public: Optional[bool] = None

class ProjectResponse(ProjectCreate):
    id: UUID
    slug: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    images: List[ProjectImageResponse] = []
    
    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)

class ProjectListItem(BaseModel):
    id: UUID
    title: str
    slug: str
    description: str
    project_image: Optional[str] = None
    featured: bool
    is_ongoing: bool
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    primary_image: Optional[ProjectImageResponse] = None
    
    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)
