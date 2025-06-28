from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class BlogPostCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    author_name: str = "Admin"
    tags: List[str] = []
    is_published: bool = False
    featured: bool = False
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    author_name: Optional[str] = None
    tags: Optional[List[str]] = None
    is_published: Optional[bool] = None
    featured: Optional[bool] = None
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None

class BlogPostResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    author_name: str
    tags: List[str] = []
    is_published: bool
    featured: bool
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class BlogPostListItem(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    author_name: str
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
    is_published: bool
    featured: bool
