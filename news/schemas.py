from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl

class NewsCategoryBase(BaseModel):
    name: str
    slug: str

class NewsCategoryCreate(NewsCategoryBase):
    pass

class NewsCategoryResponse(NewsCategoryBase):
    id: int

class NewsArticleBase(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    contact_info: Optional[str] = None
    tags: Optional[str] = None
    published: bool = False
    featured: bool = False
    allow_comments: bool = True
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None

class NewsArticleCreate(NewsArticleBase):
    slug: Optional[str] = None  # Will be generated if not provided
    category_ids: List[int] = []
    related_news_ids: Optional[List[int]] = None

class NewsArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    contact_info: Optional[str] = None
    tags: Optional[str] = None
    published: Optional[bool] = None
    featured: Optional[bool] = None
    allow_comments: Optional[bool] = None
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None
    category_ids: Optional[List[int]] = None
    related_news_ids: Optional[List[int]] = None

class NewsArticleResponse(NewsArticleBase):
    id: int
    slug: str
    author_id: int
    published_at: datetime
    created_at: datetime
    updated_at: datetime
    view_count: int
    share_count: int
    comment_count: int
    categories: List["NewsCategoryResponse"] = []
    related_news: Optional[List[Dict[str, Any]]] = None

class NewsArticleListItem(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: Optional[str]
    image_url: Optional[str]
    author_id: int
    published_at: datetime
    published: bool
    featured: bool
    categories: List[NewsCategoryResponse] = []
