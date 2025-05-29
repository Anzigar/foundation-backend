from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from news.schemas import (
    NewsArticleCreate, 
    NewsArticleResponse, 
    NewsArticleUpdate, 
    NewsArticleListItem,
    NewsCategoryResponse,
    NewsCategoryCreate
)
from shared.utils import generate_slug

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
    # Base query with joins to get categories
    query = """
    SELECT 
        n.id, n.title, n.slug, n.excerpt, n.image_url, n.author_id, 
        n.published_at, n.created_at, n.updated_at, n.published, n.featured,
        c.id as category_id, c.name as category_name, c.slug as category_slug
    FROM news_articles n
    LEFT JOIN news_article_categories nac ON n.id = nac.article_id
    LEFT JOIN news_categories c ON nac.category_id = c.id
    WHERE n.published = 1
    """
    
    params = []
    
    # Apply filters
    if category_id:
        query += " AND c.id = %s"
        params.append(category_id)
    
    if featured is not None:
        query += " AND n.featured = %s"
        params.append(featured)
    
    if search:
        query += " AND (n.title LIKE %s OR n.content LIKE %s)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    # Apply cursor pagination
    if cursor:
        if order.lower() == "desc":
            query += " AND n.id < %s"
        else:
            query += " AND n.id > %s"
        params.append(cursor)
    
    # Order the results
    if order.lower() == "desc":
        query += " ORDER BY n.id DESC"
    else:
        query += " ORDER BY n.id ASC"
    
    # Get one more item to check if there are more results
    query += f" LIMIT {limit + 1}"
    
    # Execute the query with parameters
    news_items = await fetch_all(query, tuple(params) if params else None)
    
    # Format the results
    formatted_news = format_news_with_categories(news_items)
    
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

@router.get("/{slug}", response_model=NewsArticleResponse)
async def get_news_article(slug: str):
    """Get a single news article by slug using raw SQL."""
    query = """
    SELECT 
        n.id, n.title, n.slug, n.content, n.excerpt, n.image_url, n.author_id, 
        n.published_at, n.created_at, n.updated_at, n.published, n.featured,
        c.id as category_id, c.name as category_name, c.slug as category_slug
    FROM news_articles n
    LEFT JOIN news_article_categories nac ON n.id = nac.article_id
    LEFT JOIN news_categories c ON nac.category_id = c.id
    WHERE n.slug = %s AND n.published = 1
    """
    
    news_items = await fetch_all(query, (slug,))
    
    if not news_items:
        raise HTTPException(status_code=404, detail="News article not found")
    
    # Format the result
    formatted_news = format_news_with_categories(news_items)
    
    return formatted_news[0]

@router.post("/", response_model=NewsArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_news_article(article: NewsArticleCreate):
    """Create a new news article using raw SQL."""
    # Generate slug if not provided
    if not article.slug:
        article.slug = generate_slug(article.title)
    
    # Insert the news article
    query = """
    INSERT INTO news_articles 
    (title, slug, content, excerpt, image_url, author_id, published, featured)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    # Replace with actual author ID from authentication
    author_id = 1
    
    await execute_query(
        query, 
        (
            article.title, 
            article.slug, 
            article.content, 
            article.excerpt, 
            article.image_url, 
            author_id,
            article.published, 
            article.featured
        )
    )
    
    # Get the inserted article ID
    article_id = await fetch_one("SELECT LAST_INSERT_ID() as id")
    article_id = article_id["id"]
    
    # Add categories if provided
    if article.category_ids:
        values = []
        params = []
        
        for category_id in article.category_ids:
            values.append("(%s, %s)")
            params.extend([article_id, category_id])
        
        if values:
            category_query = f"""
            INSERT INTO news_article_categories (article_id, category_id)
            VALUES {', '.join(values)}
            """
            
            await execute_query(category_query, tuple(params))
    
    # Clear cache
    await clear_cache(pattern="news:list*")
    
    # Get the newly created article
    return await get_news_article(article.slug)

@router.put("/{article_id}", response_model=NewsArticleResponse)
async def update_news_article(article_id: int, article_update: NewsArticleUpdate):
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
    
    if article_update.published is not None:
        update_fields.append("published = %s")
        params.append(article_update.published)
    
    if article_update.featured is not None:
        update_fields.append("featured = %s")
        params.append(article_update.featured)
    
    # Update the article if there are fields to update
    if update_fields:
        update_query = f"""
        UPDATE news_articles 
        SET {', '.join(update_fields)}
        WHERE id = %s
        """
        
        params.append(article_id)
        await execute_query(update_query, tuple(params))
    
    # Update categories if provided
    if article_update.category_ids is not None:
        # First delete existing categories
        await execute_query(
            "DELETE FROM news_article_categories WHERE article_id = %s", 
            (article_id,)
        )
        
        # Then add new categories
        if article_update.category_ids:
            values = []
            params = []
            
            for category_id in article_update.category_ids:
                values.append("(%s, %s)")
                params.extend([article_id, category_id])
            
            if values:
                category_query = f"""
                INSERT INTO news_article_categories (article_id, category_id)
                VALUES {', '.join(values)}
                """
                
                await execute_query(category_query, tuple(params))
    
    # Clear cache
    article_slug = await fetch_one(
        "SELECT slug FROM news_articles WHERE id = %s", 
        (article_id,)
    )
    await clear_cache(pattern=f"news:detail:{article_slug['slug']}")
    await clear_cache(pattern="news:list*")
    
    # Get the updated article
    return await get_news_article(article_slug["slug"])

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news_article(article_id: int):
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
    await clear_cache(pattern=f"news:detail:{article['slug']}")
    await clear_cache(pattern="news:list*")
    
    return JSONResponse(content={}, status_code=status.HTTP_204_NO_CONTENT)

# Add routes for categories
@router.get("/categories/", response_model=List[NewsCategoryResponse])
async def get_news_categories():
    """Get all news categories."""
    categories = await fetch_all("SELECT id, name, slug FROM news_categories ORDER BY name")
    return categories

@router.post("/categories/", response_model=NewsCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_news_category(category: NewsCategoryCreate):
    """Create a new news category."""
    await execute_query(
        "INSERT INTO news_categories (name, slug) VALUES (%s, %s)",
        (category.name, category.slug)
    )
    
    category_id = await fetch_one("SELECT LAST_INSERT_ID() as id")
    
    return {
        "id": category_id["id"],
        "name": category.name,
        "slug": category.slug
    }