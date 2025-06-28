from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class NewsArticleCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    author_name: str = "Admin"
    is_published: bool = False
    featured: bool = False
    category: Optional[str] = None
    slug: Optional[str] = None

class NewsArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    author_name: Optional[str] = None
    is_published: Optional[bool] = None
    featured: Optional[bool] = None
    category: Optional[str] = None

class NewsArticleResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    author_name: str
    is_published: bool
    featured: bool
    category: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class NewsArticleListItem(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    author_name: str
    category: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_published: bool
    featured: bool
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    published: bool = False
    featured: bool = False
    created_at: datetime
    author_id: int
