from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, field_serializer

class NewsArticleCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    source: str = "Admin"
    published: bool = False
    featured: bool = False
    tags: Optional[str] = None
    slug: Optional[str] = None

class NewsArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    published: Optional[bool] = None
    featured: Optional[bool] = None
    tags: Optional[str] = None

class NewsArticleResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    published: bool
    featured: bool
    tags: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)

class NewsArticleListItem(BaseModel):
    id: UUID
    title: str
    slug: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    published: bool
    featured: bool
    created_at: datetime
    
    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)
