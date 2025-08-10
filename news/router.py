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
        if current_news is None or current_news["uid"] != item["uid"]:
            # New news article
            current_news = {
                "uid": item["uid"],
                "title": item["title"],
                "slug": item["slug"],
                "excerpt": item["excerpt"],
                "image_url": item["image_url"],
                "published_at": item["published_at"],
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
                "published": bool(item["published"]),
                "is_published": bool(item["is_published"]),
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
    cursor: Optional[str] = Query(None, description="Pagination cursor (UID of the last item)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    order: str = Query("desc", description="Sort order (asc or desc)"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    featured: Optional[bool] = Query(None, description="Filter by featured status"),
    search: Optional[str] = Query(None, description="Search in title or content")
):
    """
    Get paginated news articles with cursor-based pagination using raw SQL.
    Implements:
    - Cursor-based pagination using UID
    - Field projection (selecting only needed fields)
    - Response caching
    """
    # Base query using correct column names from database schema
    query = """
    SELECT 
        uid, title, slug, excerpt, image_url, source, tags,
        created_at, updated_at, published, is_published, featured
    FROM news_articles
    WHERE is_published = true
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
    
    # Apply cursor pagination using UID
    if cursor:
        # For UUID cursor pagination, we need to use created_at for ordering
        if order.lower() == "desc":
            query += " AND created_at < (SELECT created_at FROM news_articles WHERE uid = %s)"
        else:
            query += " AND created_at > (SELECT created_at FROM news_articles WHERE uid = %s)"
        params.append(cursor)
    
    # Order the results by created_at (since UID is not sequential)
    if order.lower() == "desc":
        query += " ORDER BY created_at DESC"
    else:
        query += " ORDER BY created_at ASC"
    
    # Get one more item to check if there are more results
    query += f" LIMIT {limit + 1}"
    
    # Execute the query with parameters
    news_items = await fetch_all(query, tuple(params) if params else None)
    
    # Format the results
    formatted_news = []
    for item in news_items:
        formatted_item = {
            "uid": item["uid"],
            "title": item["title"], 
            "slug": item["slug"],
            "excerpt": item["excerpt"],
            "image_url": item["image_url"],
            "source": item["source"],
            "tags": item["tags"],
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
            "published": item["published"],
            "is_published": item["is_published"],
            "featured": item["featured"]
        }
        formatted_news.append(formatted_item)
    
    # Check if there are more results
    has_more = len(formatted_news) > limit
    if has_more:
        formatted_news = formatted_news[:limit]
    
    # Get the next cursor (UID of the last item)
    next_cursor = str(formatted_news[-1]["uid"]) if has_more and formatted_news else None
    
    return {
        "items": formatted_news,
        "next_cursor": next_cursor,
        "has_more": has_more
    }

@router.get("/id/{article_id}", response_model=NewsArticleResponse)
async def get_news_article_by_id(article_id: str):
    """Get a single news article by UID using raw SQL."""
    query = """
    SELECT 
        uid, title, slug, content, excerpt, image_url, source, tags,
        published, is_published, featured, allow_comments,
        seo_title, meta_description, og_image_url, contact_info,
        author_name, category, venue, location, registration_link,
        ticket_price, event_start_date, event_end_date,
        published_at, created_at, updated_at, category_ids, related_news_ids
    FROM news_articles
    WHERE uid = %s AND is_published = true
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
        uid, title, slug, content, excerpt, image_url, source, tags,
        published, is_published, featured, allow_comments,
        seo_title, meta_description, og_image_url, contact_info,
        author_name, category, venue, location, registration_link,
        ticket_price, event_start_date, event_end_date,
        published_at, created_at, updated_at, category_ids, related_news_ids
    FROM news_articles
    WHERE slug = %s AND is_published = true
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
    
    # Insert the news article with all fields from the database schema
    query = """
    INSERT INTO news_articles 
    (uid, title, slug, content, excerpt, image_url, source, tags,
     published, is_published, featured, allow_comments,
     seo_title, meta_description, og_image_url, contact_info,
     author_name, category, venue, location, registration_link,
     ticket_price, event_start_date, event_end_date,
     published_at, created_at, updated_at, category_ids, related_news_ids)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    now = datetime.now()
    article_uid = uuid.uuid4()
    
    await execute_query(
        query, 
        (
            article_uid,
            article.title, 
            article.slug, 
            article.content, 
            article.excerpt, 
            article.image_url, 
            article.source,
            article.tags,
            article.published,
            article.is_published,
            article.featured,
            article.allow_comments,
            article.seo_title,
            article.meta_description,
            article.og_image_url,
            article.contact_info,
            article.author_name,
            article.category,
            article.venue,
            article.location,
            article.registration_link,
            article.ticket_price,
            article.event_start_date,
            article.event_end_date,
            now,  # published_at
            now,  # created_at
            now,  # updated_at
            article.category_ids,
            article.related_news_ids
        )
    )
    
    # Get the newly created article
    result = await fetch_one("SELECT * FROM news_articles WHERE slug = %s", (article.slug,))
    return result

def build_update_fields_and_params(article_update: NewsArticleUpdate):
    """Build update fields and parameters for news article update."""
    update_fields = []
    params = []
    
    # Simple field mappings
    field_mappings = {
        'content': article_update.content,
        'excerpt': article_update.excerpt,
        'image_url': article_update.image_url,
        'source': article_update.source,
        'tags': article_update.tags,
        'published': article_update.published,
        'is_published': article_update.is_published,
        'featured': article_update.featured,
        'allow_comments': article_update.allow_comments,
        'seo_title': article_update.seo_title,
        'meta_description': article_update.meta_description,
        'og_image_url': article_update.og_image_url,
        'contact_info': article_update.contact_info,
        'author_name': article_update.author_name,
        'category': article_update.category,
        'venue': article_update.venue,
        'location': article_update.location,
        'registration_link': article_update.registration_link,
        'ticket_price': article_update.ticket_price,
        'event_start_date': article_update.event_start_date,
        'event_end_date': article_update.event_end_date,
        'category_ids': article_update.category_ids,
        'related_news_ids': article_update.related_news_ids
    }
    
    # Add fields that have values
    for field_name, field_value in field_mappings.items():
        if field_value is not None:
            update_fields.append(f"{field_name} = %s")
            params.append(field_value)
    
    # Handle title separately (also updates slug)
    if article_update.title is not None:
        update_fields.append("title = %s")
        params.append(article_update.title)
        # Also update slug if title is provided
        slug = generate_slug(article_update.title)
        update_fields.append("slug = %s")
        params.append(slug)
    
    return update_fields, params

@router.put("/{article_id}", response_model=NewsArticleResponse)
async def update_news_article(article_id: str, article_update: NewsArticleUpdate):
    """Update an existing news article using raw SQL."""
    # First check if the article exists
    existing = await fetch_one("SELECT slug FROM news_articles WHERE uid = %s", (article_id,))
    
    if not existing:
        raise HTTPException(status_code=404, detail="News article not found")
    
    # Build the update query dynamically based on provided fields
    update_fields, params = build_update_fields_and_params(article_update)
    
    # Update the article if there are fields to update
    if update_fields:
        update_query = f"""
        UPDATE news_articles 
        SET {', '.join(update_fields)}, updated_at = %s
        WHERE uid = %s
        """
        
        params.append(datetime.now())
        params.append(article_id)
        await execute_query(update_query, tuple(params))
    
    # Get the updated article by UID
    result = await fetch_one("SELECT * FROM news_articles WHERE uid = %s", (article_id,))
    return result

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news_article(article_id: str):
    """Delete a news article using raw SQL."""
    # Get the slug before deletion to clear cache
    article = await fetch_one(
        "SELECT slug FROM news_articles WHERE uid = %s", 
        (article_id,)
    )
    
    if not article:
        raise HTTPException(status_code=404, detail="News article not found")
    
    # Delete the article (categories will be deleted via ON DELETE CASCADE)
    await execute_query("DELETE FROM news_articles WHERE uid = %s", (article_id,))
    
    # Clear cache
    # await clear_cache(pattern=f"news:detail:{article['slug']}")
    # await clear_cache(pattern="news:list*")
    
    return JSONResponse(content={}, status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/{article_id}/toggle-publish")
async def toggle_news_article_publish(article_id: str):
    """Toggle the published status of a news article."""
    # First check if the article exists
    existing = await fetch_one("SELECT uid, is_published FROM news_articles WHERE uid = %s", (article_id,))
    
    if not existing:
        raise HTTPException(status_code=404, detail="News article not found")
    
    # Toggle the published status
    new_published_status = not existing["is_published"]
    
    # Update the article
    await execute_query(
        "UPDATE news_articles SET is_published = %s, updated_at = %s WHERE uid = %s",
        (new_published_status, datetime.now(), article_id)
    )
    
    # Get the updated article
    result = await fetch_one("SELECT * FROM news_articles WHERE uid = %s", (article_id,))
    return result