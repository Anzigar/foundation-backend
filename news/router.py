from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
import uuid

from news.schemas import (
    NewsArticleCreate, 
    NewsArticleResponse, 
    NewsArticleUpdate
)
from shared.utils import generate_slug
from shared.helpers import fetch_all, fetch_one, execute_query

router = APIRouter()

def format_news_with_categories(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format news items with their categories."""
    result = []
    current_news = None
    
    for item in news_items:
        if current_news is None or current_news["id"] != item["id"]:
            # New news article
            current_news = {
                "id": item["id"],
                "title": item["title"],
                "slug": item["slug"],
                "excerpt": item["excerpt"],
                "image_url": item["image_url"],
                "author_id": item["author_id"],
                "published_at": item["published_at"],
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
                "published": bool(item["published"]),
                "featured": bool(item["featured"]),
                "content": item["content"],
                "categories": []
            }
            result.append(current_news)
        
        # Add category if it exists
        if item.get("category_id"):
            current_news["categories"].append({
                "id": item["category_id"],
                "name": item["category_name"],
                "slug": item["category_slug"]
            })
            
    return result

@router.get("/", response_model=Dict[str, Any])
async def get_news_articles(
    cursor: Optional[str] = Query(None, description="Pagination cursor (ID of the last item)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    order: str = Query("desc", description="Sort order (asc or desc)"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    featured: Optional[bool] = Query(None, description="Filter by featured status"),
    search: Optional[str] = Query(None, description="Search in title or content")
):
    """
    Get paginated news articles with cursor-based pagination using raw SQL.
    Implements:
    - Cursor-based pagination
    - Field projection (selecting only needed fields)
    - Response caching
    """
    # Base query - simplified to match our actual schema
    query = """
    SELECT 
        id, title, slug, excerpt, image_url, source, 
        created_at, updated_at, published, featured, tags
    FROM news_articles
    WHERE published = true
    """
    
    params = []
    
    # Apply filters
    if category_id:
        # For now, we'll ignore category_id since we don't have a categories table
        # but we could filter by the category string field if needed
        pass
    
    if featured is not None:
        query += " AND featured = %s"
        params.append(featured)
    
    if search:
        query += " AND (title ILIKE %s OR excerpt ILIKE %s)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    # Apply cursor pagination
    if cursor:
        if order.lower() == "desc":
            query += " AND id < %s"
        else:
            query += " AND id > %s"
        params.append(cursor)
    
    # Order the results
    if order.lower() == "desc":
        query += " ORDER BY id DESC"
    else:
        query += " ORDER BY id ASC"
    
    # Get one more item to check if there are more results
    query += f" LIMIT {limit + 1}"
    
    # Execute the query with parameters
    news_items = await fetch_all(query, tuple(params) if params else None)
    
    # Format the results (simplified without categories)
    formatted_news = []
    for item in news_items:
        formatted_item = {
            "id": item["id"],
            "title": item["title"], 
            "slug": item["slug"],
            "excerpt": item["excerpt"],
            "image_url": item["image_url"],
            "source": item["source"],
            "tags": item["tags"],
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
            "published": item["published"],
            "featured": item["featured"]
        }
        formatted_news.append(formatted_item)
    
    # Check if there are more results
    has_more = len(formatted_news) > limit
    if has_more:
        formatted_news = formatted_news[:limit]
    
    # Get the next cursor
    next_cursor = str(formatted_news[-1]["id"]) if has_more and formatted_news else None
    
    return {
        "items": formatted_news,
        "next_cursor": next_cursor,
        "has_more": has_more
    }

@router.get("/id/{article_id}", response_model=NewsArticleResponse)
async def get_news_article_by_id(article_id: str):
    """Get a single news article by ID using raw SQL."""
    query = """
    SELECT 
        id, title, slug, content, excerpt, image_url, source,
        created_at, updated_at, published, featured, tags
    FROM news_articles
    WHERE id = %s AND published = true
    """
    
    article = await fetch_one(query, (article_id,))
    
    if not article:
        raise HTTPException(status_code=404, detail="News article not found")
    
    return article

@router.get("/{slug}", response_model=NewsArticleResponse)
async def get_news_article(slug: str):
    """Get a single news article by slug using raw SQL."""
    query = """
    SELECT 
        id, title, slug, content, excerpt, image_url, source,
        created_at, updated_at, published, featured, tags
    FROM news_articles
    WHERE slug = %s AND published = true
    """
    
    article = await fetch_one(query, (slug,))
    
    if not article:
        raise HTTPException(status_code=404, detail="News article not found")
    
    return article

@router.post("/", response_model=NewsArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_news_article(article: NewsArticleCreate):
    """Create a new news article using raw SQL."""
    # Generate slug if not provided
    if not article.slug:
        article.slug = generate_slug(article.title)
    
    # Insert the news article (let database auto-generate ID)
    query = """
    INSERT INTO news_articles 
    (title, slug, content, excerpt, image_url, source, published, featured, tags, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    now = datetime.now()
    
    await execute_query(
        query, 
        (
            article.title, 
            article.slug, 
            article.content, 
            article.excerpt, 
            article.image_url, 
            article.source,
            article.published, 
            article.featured,
            article.tags,
            now,
            now
        )
    )
    
    # Get the newly created article
    result = await fetch_one("SELECT * FROM news_articles WHERE slug = %s", (article.slug,))
    return result

@router.put("/{article_id}", response_model=NewsArticleResponse)
async def update_news_article(article_id: str, article_update: NewsArticleUpdate):
    """Update an existing news article using raw SQL."""
    # First check if the article exists
    existing = await fetch_one("SELECT slug FROM news_articles WHERE id = %s", (article_id,))
    
    if not existing:
        raise HTTPException(status_code=404, detail="News article not found")
    
    # Build the update query dynamically based on provided fields
    update_fields = []
    params = []
    
    if article_update.title is not None:
        update_fields.append("title = %s")
        params.append(article_update.title)
        # Also update slug if title is provided
        slug = generate_slug(article_update.title)
        update_fields.append("slug = %s")
        params.append(slug)
    
    if article_update.content is not None:
        update_fields.append("content = %s")
        params.append(article_update.content)
    
    if article_update.excerpt is not None:
        update_fields.append("excerpt = %s")
        params.append(article_update.excerpt)
    
    if article_update.image_url is not None:
        update_fields.append("image_url = %s")
        params.append(article_update.image_url)
    
    if article_update.is_published is not None:
        update_fields.append("published = %s")
        params.append(article_update.is_published)
    
    if article_update.featured is not None:
        update_fields.append("featured = %s")
        params.append(article_update.featured)
    
    # Update the article if there are fields to update
    if update_fields:
        update_query = f"""
        UPDATE news_articles 
        SET {', '.join(update_fields)}, updated_at = %s
        WHERE id = %s
        """
        
        from datetime import datetime
        params.append(datetime.now())
        params.append(article_id)
        await execute_query(update_query, tuple(params))
    
    # Get the updated article by ID
    result = await fetch_one("SELECT * FROM news_articles WHERE id = %s", (article_id,))
    return result

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news_article(article_id: str):
    """Delete a news article using raw SQL."""
    # Get the slug before deletion to clear cache
    article = await fetch_one(
        "SELECT slug FROM news_articles WHERE id = %s", 
        (article_id,)
    )
    
    if not article:
        raise HTTPException(status_code=404, detail="News article not found")
    
    # Delete the article (categories will be deleted via ON DELETE CASCADE)
    await execute_query("DELETE FROM news_articles WHERE id = %s", (article_id,))
    
    # Clear cache
    # await clear_cache(pattern=f"news:detail:{article['slug']}")
    # await clear_cache(pattern="news:list*")
    
    return JSONResponse(content={}, status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/{article_id}/toggle-publish")
async def toggle_news_article_publish(article_id: str):
    """Toggle the published status of a news article."""
    # First check if the article exists
    existing = await fetch_one("SELECT id, published FROM news_articles WHERE id = %s", (article_id,))
    
    if not existing:
        raise HTTPException(status_code=404, detail="News article not found")
    
    # Toggle the published status
    new_published_status = not existing["published"]
    
    # Update the article
    await execute_query(
        "UPDATE news_articles SET published = %s, updated_at = %s WHERE id = %s",
        (new_published_status, datetime.now(), article_id)
    )
    
    # Get the updated article
    result = await fetch_one("SELECT * FROM news_articles WHERE id = %s", (article_id,))
    return result