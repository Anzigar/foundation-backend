from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, field_serializer

class NewsArticleCreate(BaseModel):
    title: str
    content: Optional[str] = None
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[str] = None  # Database stores as varchar(255)
    published: bool = False
    featured: bool = False
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None
    author_name: Optional[str] = None
    
    # JSON fields
    category_ids: Optional[List] = []
    
    slug: Optional[str] = None

class NewsArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[str] = None
    published: Optional[bool] = None
    featured: Optional[bool] = None
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None
    author_name: Optional[str] = None
    
    # JSON fields
    category_ids: Optional[List] = None

class NewsArticleResponse(BaseModel):
    uid: UUID  # Database uses uid as primary key
    title: str
    slug: str
    content: Optional[str] = None
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[str] = None
    published: bool
    featured: bool
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None
    author_name: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # JSON fields
    category_ids: Optional[List] = []
    
    @field_serializer('uid')
    def serialize_uid(self, value: UUID) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)

class NewsArticleListItem(BaseModel):
    uid: UUID  # Database uses uid as primary key
    title: str
    slug: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[str] = None
    published: bool
    featured: bool
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('uid')
    def serialize_uid(self, value: UUID) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)
