from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import json  # Add this import at the top

from blog.schemas import (
    BlogPostCreate, 
    BlogPostResponse
)
from blog.models import BlogPost
from shared.utils import generate_slug
from shared.database import get_db
from shared.helpers import fetch_all, fetch_one, execute_query
from shared.deployment_utils import deploy_content, undeploy_content, get_deployment_status, DeploymentError

router = APIRouter()

def format_blog_with_tags_and_author(blog_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format blog posts with their tags and author information."""
    result = []
    current_post = None
    
    for item in blog_items:
        if current_post is None or current_post["id"] != item["id"]:
            # New blog post
            current_post = {
                "id": item["id"],
                "title": item["title"],
                "slug": item["slug"],
                "introduction": item["introduction"],
                "content": item["content"],
                "excerpt": item["excerpt"],
                "featured_image_url": item["featured_image_url"],
                "cta_text": item["cta_text"],
                "cta_link": item["cta_link"],
                "allow_comments": bool(item["allow_comments"]),
                "seo_title": item["seo_title"],
                "meta_description": item["meta_description"],
                "og_image_url": item["og_image_url"],
                "newsletter_form_enabled": bool(item["newsletter_form_enabled"]),
                "published": bool(item["published"]),
                "published_at": item["published_at"],
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
                "view_count": item["view_count"],
                "share_count": item["share_count"],
                "comment_count": item["comment_count"],
                "author": {
                    "id": item["author_id"],
                    "username": item["author_username"],
                    "full_name": item["author_full_name"],
                    "bio": item["author_bio"],
                    "profile_image_url": item["author_profile_image_url"],
                    "social_links": item["author_social_links"]
                },
                "tags": [],
                "related_posts": item["related_posts"] if item["related_posts"] else []
            }
            result.append(current_post)
        
        # Add tag if it exists
        if item.get("tag_id"):
            current_post["tags"].append({
                "id": item["tag_id"],
                "name": item["tag_name"],
                "slug": item["tag_slug"],
                "description": item["tag_description"]
            })
            
    return result

@router.get("/", response_model=Dict[str, Any])
async def get_blog_posts(
    cursor: Optional[str] = Query(None, description="Pagination cursor (ID of the last item)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    order: str = Query("desc", description="Sort order (asc or desc)"),
    tag_id: Optional[int] = Query(None, description="Filter by tag ID"),
    search: Optional[str] = Query(None, description="Search in title or content"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated blog posts with cursor-based pagination using raw SQL.
    Implements:
    - Cursor-based pagination
    - Field projection (selecting only needed fields)
    - Tag filtering
    - Search functionality
    """
    # Base query - simplified to match our actual schema
    query = """
    SELECT 
        id, title, slug, excerpt, image_url, author_name, tags,
        created_at, updated_at, is_published, featured, seo_title, meta_description
    FROM blog_posts
    WHERE is_published = true
    """
    
    params = []
    
    # Apply filters - PostgreSQL uses %s for parameters
    if tag_id:
        # For now, we'll ignore tag_id since we don't have separate tag tables
        # but we could filter by the tags text field if needed
        pass
    
    if search:
        query += " AND (title ILIKE %s OR content ILIKE %s OR excerpt ILIKE %s)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
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
    blog_items = await fetch_all(query, tuple(params) if params else None)
    
    # Format the results (simplified without complex joins)
    formatted_blogs = []
    for item in blog_items:
        formatted_item = {
            "id": item["id"],
            "title": item["title"],
            "slug": item["slug"],
            "excerpt": item["excerpt"],
            "image_url": item["image_url"],
            "author_name": item["author_name"],
            "tags": item["tags"].split(",") if item["tags"] else [],
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
            "is_published": item["is_published"],
            "featured": item["featured"],
            "seo_title": item["seo_title"],
            "meta_description": item["meta_description"]
        }
        formatted_blogs.append(formatted_item)
    
    # Check if there are more results
    has_more = len(formatted_blogs) > limit
    if has_more:
        formatted_blogs = formatted_blogs[:limit]
    
    # Get the next cursor
    next_cursor = str(formatted_blogs[-1]["id"]) if has_more and formatted_blogs else None
    
    return {
        "items": formatted_blogs,
        "next_cursor": next_cursor,
        "has_more": has_more
    }

@router.get("/{slug}", response_model=BlogPostResponse)
async def get_blog_post(slug: str):
    """Get a single blog post by slug."""
    # Get the blog post - simplified to match our actual schema
    query = """
    SELECT 
        id, title, slug, content, excerpt, image_url, author_name, tags,
        created_at, updated_at, is_published, featured, seo_title, meta_description
    FROM blog_posts
    WHERE slug = %s AND is_published = true
    """
    
    blog_post = await fetch_one(query, (slug,))
    
    if not blog_post:
        raise HTTPException(status_code=404, detail=f"Published blog post with slug '{slug}' not found. Try /api/blog/draft/{slug} for drafts.")
    
    # Format the result
    formatted_post = {
        "id": blog_post["id"],
        "title": blog_post["title"],
        "slug": blog_post["slug"],
        "content": blog_post["content"],
        "excerpt": blog_post["excerpt"],
        "image_url": blog_post["image_url"],
        "author_name": blog_post["author_name"],
        "tags": blog_post["tags"].split(",") if blog_post["tags"] else [],
        "created_at": blog_post["created_at"],
        "updated_at": blog_post["updated_at"],
        "is_published": blog_post["is_published"],
        "featured": blog_post["featured"],
        "seo_title": blog_post["seo_title"],
        "meta_description": blog_post["meta_description"]
    }
    
    return formatted_post

@router.get("/id/{post_id}", response_model=BlogPostResponse)
async def get_blog_post_by_id(post_id: UUID):
    """Get a single blog post by ID."""
    query = """
    SELECT 
        id, title, slug, content, excerpt, image_url, author_name, tags,
        created_at, updated_at, is_published, featured, seo_title, meta_description
    FROM blog_posts
    WHERE id = %s AND is_published = true
    """
    
    blog_post = await fetch_one(query, (post_id,))
    
    if not blog_post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Format the result to match the response schema  
    formatted_result = {
        "id": blog_post["id"],
        "title": blog_post["title"],
        "slug": blog_post["slug"],
        "content": blog_post["content"],
        "excerpt": blog_post["excerpt"],
        "image_url": blog_post["image_url"],
        "author_name": blog_post["author_name"],
        "tags": blog_post["tags"].split(",") if blog_post["tags"] else [],
        "created_at": blog_post["created_at"],
        "updated_at": blog_post["updated_at"],
        "is_published": blog_post["is_published"],
        "featured": blog_post["featured"],
        "seo_title": blog_post["seo_title"],
        "meta_description": blog_post["meta_description"]
    }
    
    return formatted_result

@router.post("/", response_model=BlogPostResponse, status_code=status.HTTP_201_CREATED)
async def create_blog_post(post: BlogPostCreate):
    """Create a new blog post."""
    # Add logging to debug frontend issues
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Creating blog post: title='{post.title}', slug='{post.slug}', is_published={post.is_published}")
    
    # Generate slug if not provided
    if not post.slug:
        post.slug = generate_slug(post.title)
    
    # Handle slug uniqueness by auto-generating unique slug if needed
    original_slug = post.slug
    counter = 1
    while True:
        existing = await fetch_one("SELECT id FROM blog_posts WHERE slug = %s", (post.slug,))
        if not existing:
            break
        # If slug exists, append counter
        post.slug = f"{original_slug}-{counter}"
        counter += 1
        
        # Prevent infinite loop - max 100 attempts
        if counter > 100:
            raise HTTPException(
                status_code=400, 
                detail=f"Unable to generate unique slug for '{original_slug}' after 100 attempts"
            )
    
    # Insert the blog post
    query = """
    INSERT INTO blog_posts (
        id, title, slug, content, excerpt, image_url, author_name, tags,
        is_published, featured, seo_title, meta_description, created_at, updated_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    from datetime import datetime
    import uuid
    now = datetime.now()
    post_id = uuid.uuid4()
    
    # Convert tag list to comma-separated string if provided
    tags_str = ",".join(post.tags) if post.tags else ""

    await execute_query(
        query, 
        (
            post_id, post.title, post.slug, post.content, post.excerpt, post.image_url,
            post.author_name, tags_str, post.is_published, post.featured,
            post.seo_title, post.meta_description, now, now
        )
    )

    # Get the newly created post
    result = await fetch_one("SELECT * FROM blog_posts WHERE slug = %s", (post.slug,))
    
    # Format the result to match the response schema
    formatted_result = {
        "id": result["id"],
        "title": result["title"],
        "slug": result["slug"],
        "content": result["content"],
        "excerpt": result["excerpt"],
        "image_url": result["image_url"],
        "author_name": result["author_name"],
        "tags": result["tags"].split(",") if result["tags"] else [],
        "created_at": result["created_at"],
        "updated_at": result["updated_at"],
        "is_published": result["is_published"],
        "featured": result["featured"],
        "seo_title": result["seo_title"],
        "meta_description": result["meta_description"]
    }
    
    return formatted_result

@router.get("/draft/{slug}", response_model=BlogPostResponse)
async def get_blog_post_draft(slug: str):
    """Get a single blog post by slug, including unpublished drafts."""
    query = """
    SELECT 
        id, title, slug, content, excerpt, image_url, author_name, tags,
        created_at, updated_at, is_published, featured, seo_title, meta_description
    FROM blog_posts
    WHERE slug = %s
    """
    
    blog_post = await fetch_one(query, (slug,))
    
    if not blog_post:
        raise HTTPException(status_code=404, detail=f"Blog post with slug '{slug}' not found")
    
    # Format the result to match the response schema
    formatted_result = {
        "id": blog_post["id"],
        "title": blog_post["title"],
        "slug": blog_post["slug"],
        "content": blog_post["content"],
        "excerpt": blog_post["excerpt"],
        "image_url": blog_post["image_url"],
        "author_name": blog_post["author_name"],
        "tags": blog_post["tags"].split(",") if blog_post["tags"] else [],
        "created_at": blog_post["created_at"],
        "updated_at": blog_post["updated_at"],
        "is_published": blog_post["is_published"],
        "featured": blog_post["featured"],
        "seo_title": blog_post["seo_title"],
        "meta_description": blog_post["meta_description"]
    }
    
    return formatted_result

@router.post("/draft", response_model=BlogPostResponse, status_code=status.HTTP_201_CREATED)
async def create_blog_post_draft(post: BlogPostCreate):
    """Create a new blog post draft (unpublished)."""
    # Generate slug if not provided
    if not post.slug:
        post.slug = generate_slug(post.title)
    
    # If it's an offline blog with timestamp, keep the slug as-is
    if post.slug.startswith('offlineBlog_'):
        pass  # Keep the offline slug as-is
    
    # Insert the blog post as a draft (is_published = false)
    query = """
    INSERT INTO blog_posts (
        id, title, slug, content, excerpt, image_url, author_name, tags,
        is_published, featured, seo_title, meta_description, created_at, updated_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    from datetime import datetime
    import uuid
    now = datetime.now()
    post_id = uuid.uuid4()
    
    await execute_query(
        query, 
        (
            post_id,
            post.title, 
            post.slug, 
            post.content, 
            post.excerpt, 
            post.image_url, 
            post.author_name,
            ','.join(post.tags) if post.tags else None,
            False,  # is_published = False for drafts
            post.featured,
            post.seo_title,
            post.meta_description,
            now,
            now
        )
    )
    
    # Get the newly created draft
    result = await fetch_one("SELECT * FROM blog_posts WHERE slug = %s", (post.slug,))
    
    # Format the result to match the response schema
    formatted_result = {
        "id": result["id"],
        "title": result["title"],
        "slug": result["slug"],
        "content": result["content"],
        "excerpt": result["excerpt"],
        "image_url": result["image_url"],
        "author_name": result["author_name"],
        "tags": result["tags"].split(",") if result["tags"] else [],
        "created_at": result["created_at"],
        "updated_at": result["updated_at"],
        "is_published": result["is_published"],
        "featured": result["featured"],
        "seo_title": result["seo_title"],
        "meta_description": result["meta_description"]
    }
    
    return formatted_result

@router.post("/sync-offline", response_model=BlogPostResponse, status_code=status.HTTP_201_CREATED)
async def sync_offline_blog_post(post: BlogPostCreate):
    """Sync an offline blog post to the server."""
    import logging
    import time
    logger = logging.getLogger(__name__)
    
    # Handle offline blog posts specifically
    if post.slug and post.slug.startswith('offlineBlog_'):
        # Generate a new proper slug from the title
        new_slug = generate_slug(post.title) if post.title else f"blog-post-{int(time.time())}"
        logger.info(f"Converting offline blog '{post.slug}' to proper slug '{new_slug}'")
        post.slug = new_slug
    
    # Use the same logic as create_blog_post but with offline handling
    return await create_blog_post(post)


# Deployment endpoints
@router.post("/{blog_id}/deploy")
async def deploy_blog_post(
    blog_id: UUID, 
    force: bool = Query(False, description="Force deployment even if already deployed"),
    db: Session = Depends(get_db)
):
    """Deploy a blog post, making it live and preventing duplicate deployments."""
    try:
        # Fetch the blog post
        blog_post = db.query(BlogPost).filter(BlogPost.id == blog_id).first()
        if not blog_post:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        # Deploy the content
        result = deploy_content(db, blog_post, force=force)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result,
                "blog_post": {
                    "id": str(blog_post.id),
                    "title": blog_post.title,
                    "slug": blog_post.slug,
                    "is_deployed": blog_post.is_deployed,
                    "deployment_count": blog_post.deployment_count
                }
            }
        )
        
    except DeploymentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@router.post("/{blog_id}/undeploy")
async def undeploy_blog_post(
    blog_id: UUID,
    db: Session = Depends(get_db)
):
    """Undeploy a blog post, taking it offline."""
    try:
        # Fetch the blog post
        blog_post = db.query(BlogPost).filter(BlogPost.id == blog_id).first()
        if not blog_post:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        # Undeploy the content
        result = undeploy_content(db, blog_post)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result,
                "blog_post": {
                    "id": str(blog_post.id),
                    "title": blog_post.title,
                    "slug": blog_post.slug,
                    "is_deployed": blog_post.is_deployed
                }
            }
        )
        
    except DeploymentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Undeployment failed: {str(e)}")


@router.get("/{blog_id}/deployment-status")
async def get_blog_deployment_status(
    blog_id: UUID,
    db: Session = Depends(get_db)
):
    """Get deployment status for a blog post."""
    try:
        blog_post = db.query(BlogPost).filter(BlogPost.id == blog_id).first()
        if not blog_post:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        status_info = get_deployment_status(blog_post)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": status_info
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deployment status: {str(e)}")

@router.get("/debug-slugs")
async def debug_existing_slugs():
    """Debug endpoint to see what slugs exist in the database."""
    slugs = await fetch_all("SELECT slug, title, is_published FROM blog_posts ORDER BY created_at DESC")
    return {"existing_slugs": slugs}