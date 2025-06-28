from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class MediaUpload(BaseModel):
    name: Optional[str] = None
    folder: str = "uploads"
    tags: List[str] = []

class MediaResponse(BaseModel):
    id: int
    name: str
    url: str
    public_url: str  # Same as url for compatibility
    file_key: str
    file_type: str
    thumbnail_url: Optional[str] = None
    tags: List[str] = []
    created_at: datetime

class MediaBrowserResponse(BaseModel):
    folders: List[Dict[str, str]]
    images: Dict[str, Any]
    videos: Dict[str, Any]
    documents: Dict[str, Any]

class MediaUploadResponse(BaseModel):
    id: int
    public_url: str
    key: str
    name: str
    url: str
