from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# Project Image Schemas
class ProjectImageBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: str
    primary: bool = False
    order_index: int = 0

class ProjectImageCreate(ProjectImageBase):
    pass

class ProjectImageUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    primary: Optional[bool] = None
    order_index: Optional[int] = None

class ProjectImageResponse(ProjectImageBase):
    id: int
    project_id: int
    created_at: datetime

class ProjectCreate(BaseModel):
    title: str
    slug: Optional[str] = None
    description: str
    project_image: Optional[str] = None
    project_image_preview: Optional[str] = None
    image_title: Optional[str] = None
    image_description: Optional[str] = None
    github_link: Optional[str] = None
    demo_link: Optional[str] = None
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
    github_link: Optional[str] = None
    demo_link: Optional[str] = None
    technologies: Optional[List[str]] = None
    is_ongoing: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    featured: Optional[bool] = None
    public: Optional[bool] = None

class ProjectResponse(ProjectCreate):
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime
    images: List[ProjectImageResponse] = []

class ProjectListItem(BaseModel):
    id: int
    title: str
    slug: str
    description: str
    project_image: Optional[str] = None
    featured: bool
    is_ongoing: bool
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    primary_image: Optional[ProjectImageResponse] = None
