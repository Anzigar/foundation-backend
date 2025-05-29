from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl

# Project Image Schemas
class ProjectImageBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: str
    primary: bool = False
    order: int = 0

class ProjectImageCreate(ProjectImageBase):
    pass

class ProjectImageUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    primary: Optional[bool] = None
    order: Optional[int] = None

class ProjectImageResponse(ProjectImageBase):
    id: int
    project_id: int
    created_at: datetime

# Project Schemas
class ProjectBase(BaseModel):
    title: str
    description: str
    timeline: Optional[str] = None
    links: Optional[Dict[str, str]] = Field(default_factory=dict)
    published: bool = False
    featured: bool = False

class ProjectCreate(ProjectBase):
    slug: Optional[str] = None  # Will be generated if not provided
    images: Optional[List[ProjectImageCreate]] = None

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    timeline: Optional[str] = None
    links: Optional[Dict[str, str]] = None
    published: Optional[bool] = None
    featured: Optional[bool] = None

class ProjectListItem(BaseModel):
    id: int
    title: str
    slug: str
    description: str
    timeline: Optional[str] = None
    featured: bool
    created_at: datetime
    primary_image: Optional[ProjectImageResponse] = None

class ProjectResponse(ProjectBase):
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime
    images: List[ProjectImageResponse] = []
