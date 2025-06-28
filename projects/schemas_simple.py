from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    title: str
    description: str
    projectImage: Optional[str] = None
    projectImagePreview: Optional[str] = None
    imageTitle: Optional[str] = None
    imageDescription: Optional[str] = None
    githubLink: Optional[str] = None
    demoLink: Optional[str] = None
    technologies: List[str] = []
    isOngoing: bool = True
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    featured: bool = False
    public: bool = True

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    projectImage: Optional[str] = None
    projectImagePreview: Optional[str] = None
    imageTitle: Optional[str] = None
    imageDescription: Optional[str] = None
    githubLink: Optional[str] = None
    demoLink: Optional[str] = None
    technologies: Optional[List[str]] = None
    isOngoing: Optional[bool] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    featured: Optional[bool] = None
    public: Optional[bool] = None

class ProjectResponse(ProjectCreate):
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime
