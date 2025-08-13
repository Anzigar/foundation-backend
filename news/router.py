from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile, Form
from fastapi.responses import JSONResponse
import uuid

from news.schemas import (
    NewsArticleCreate, 
    NewsArticleResponse, 
    NewsArticleUpdate
)
from shared.utils import generate_slug
from shared.helpers import fetch_all, fetch_one, execute_query
from shared.storage import storage

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
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
                "published": bool(item["published"]),
                "featured": bool(item["featured"]),
                "content": item.get("content"),
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
        uid, title, slug, excerpt, image_url, tags,
        created_at, updated_at, published, featured
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
        uid, title, slug, content, excerpt, image_url, tags,
        published, featured, 
        seo_title, meta_description, og_image_url,
        author_name, created_at, updated_at, category_ids
    FROM news_articles
    WHERE uid = %s AND published = true
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
        uid, title, slug, content, excerpt, image_url, tags,
        published, featured,
        seo_title, meta_description, og_image_url,
        author_name, created_at, updated_at, category_ids
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
    
    # Insert the news article with all fields from the database schema
    query = """
    INSERT INTO news_articles 
    (uid, title, slug, content, excerpt, image_url, tags,
     published, featured, seo_title, meta_description, og_image_url,
     author_name, created_at, updated_at, category_ids)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            article.tags,
            article.published,
            article.featured,
            article.seo_title,
            article.meta_description,
            article.og_image_url,
            article.author_name,
            now,  # created_at
            now,  # updated_at
            article.category_ids
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
        'tags': article_update.tags,
        'published': article_update.published,
        'featured': article_update.featured,
        'seo_title': article_update.seo_title,
        'meta_description': article_update.meta_description,
        'og_image_url': article_update.og_image_url,
        'author_name': article_update.author_name,
        'category_ids': article_update.category_ids
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
    existing = await fetch_one("SELECT uid, published FROM news_articles WHERE uid = %s", (article_id,))
    
    if not existing:
        raise HTTPException(status_code=404, detail="News article not found")
    
    # Toggle the published status
    new_published_status = not existing["published"]
    
    # Update the article
    await execute_query(
        "UPDATE news_articles SET published = %s, updated_at = %s WHERE uid = %s",
        (new_published_status, datetime.now(), article_id)
    )
    
    # Get the updated article
    result = await fetch_one("SELECT * FROM news_articles WHERE uid = %s", (article_id,))
    return result

# S3 Image Upload Endpoints
@router.post("/upload-image")
async def upload_news_image(
    file: UploadFile = File(...),
    news_uid: Optional[str] = Form(None)
):
    """Upload an image to S3 and optionally associate it with a news article."""
    try:
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not allowed. Supported types: {', '.join(allowed_types)}"
            )
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        contents = await file.read()
        if len(contents) > max_size:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 10MB limit"
            )
        
        # Reset file pointer for upload
        await file.seek(0)
        
        # Create folder path for news images
        folder_path = "news/images"
        
        # Upload to S3 with encoded path
        upload_result = await storage.upload_file(
            file=file,
            folder_path=folder_path,
            encode_path=True  # Enable path encoding for security
        )
        
        # If news_uid provided, update the news article's image_url
        if news_uid:
            from shared.database import async_session
            async with async_session() as session:
                try:
                    # Update the news article with the encoded image path
                    update_query = """
                    UPDATE news_articles 
                    SET image_url = %s, updated_at = %s 
                    WHERE uid = %s
                    """
                    await execute_query(update_query, (upload_result["url"], datetime.now(), news_uid), session)
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    # Still return upload success even if DB update fails
                    upload_result["warning"] = f"Image uploaded but failed to update news article: {str(e)}"
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": upload_result,
                "message": "Image uploaded successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@router.delete("/delete-image")
async def delete_news_image(
    image_url: str = Form(...),
    news_uid: Optional[str] = Form(None)
):
    """Delete an image from S3 and optionally remove it from news article."""
    try:
        # Delete from S3
        delete_result = await storage.delete_file(image_url)
        
        # If news_uid provided, clear the image_url from the news article
        if news_uid:
            from shared.database import async_session
            async with async_session() as session:
                try:
                    # Clear the image_url in the news article
                    update_query = """
                    UPDATE news_articles 
                    SET image_url = NULL, updated_at = %s 
                    WHERE uid = %s AND image_url = %s
                    """
                    await execute_query(update_query, (datetime.now(), news_uid, image_url), session)
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    delete_result["warning"] = f"Image deleted but failed to update news article: {str(e)}"
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": delete_result,
                "message": "Image deleted successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Delete failed: {str(e)}"
        )

@router.get("/get-image-url")
async def get_news_image_url(encoded_path: str = Query(..., description="Encoded S3 path")):
    """Get the actual S3 URL from an encoded path."""
    try:
        actual_url = storage.get_actual_url(encoded_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "encoded_path": encoded_path,
                    "actual_url": actual_url
                },
                "message": "URL retrieved successfully"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to decode URL: {str(e)}"
        )