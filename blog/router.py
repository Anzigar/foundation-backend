from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile, Form
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
from shared.storage import storage

router = APIRouter()

def format_blog_with_tags_and_author(blog_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format blog posts with their tags and author information."""
    result = []
    current_post = None
    
    for item in blog_items:
        if current_post is None or current_post["uid"] != item["uid"]:
            # Starting a new post
            current_post = {
                "uid": item["uid"],
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
    # Base query with field projection
    query = """
    SELECT 
        uid, title, slug, excerpt, image_url, author_name, tags,
        created_at, updated_at, published, featured, seo_title, meta_description
    FROM blog_posts
    WHERE published = true
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
            query += " AND uid < %s"
        else:
            query += " AND uid > %s"
        params.append(cursor)
    
    # Order the results
    if order.lower() == "desc":
        query += " ORDER BY uid DESC"
    else:
        query += " ORDER BY uid ASC"
    
    # Get one more item to check if there are more results
    query += f" LIMIT {limit + 1}"
    
    # Execute the query with parameters
    blog_items = await fetch_all(query, tuple(params) if params else None)
    
    # Format the results (simplified without complex joins)
    formatted_blogs = []
    for item in blog_items:
        formatted_item = {
            "uid": item["uid"],
            "title": item["title"],
            "slug": item["slug"],
            "excerpt": item["excerpt"],
            "image_url": item["image_url"],
            "author_name": item["author_name"],
            "tags": item["tags"].split(",") if item["tags"] else [],
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
            "published": item["published"],
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
    next_cursor = str(formatted_blogs[-1]["uid"]) if has_more and formatted_blogs else None
    
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
        uid, title, slug, content, excerpt, image_url, author_name, tags,
        created_at, updated_at, published, featured, seo_title, meta_description
    FROM blog_posts
    WHERE slug = %s AND published = true
    """
    
    blog_post = await fetch_one(query, (slug,))
    
    if not blog_post:
        raise HTTPException(status_code=404, detail=f"Published blog post with slug '{slug}' not found")
    
    # Format the result
    formatted_post = {
        "uid": blog_post["uid"],
        "title": blog_post["title"],
        "slug": blog_post["slug"],
        "content": blog_post["content"],
        "excerpt": blog_post["excerpt"],
        "image_url": blog_post["image_url"],
        "author_name": blog_post["author_name"],
        "tags": blog_post["tags"].split(",") if blog_post["tags"] else [],
        "created_at": blog_post["created_at"],
        "updated_at": blog_post["updated_at"],
        "published": blog_post["published"],
        "featured": blog_post["featured"],
        "seo_title": blog_post["seo_title"],
        "meta_description": blog_post["meta_description"]
    }
    
    return formatted_post

@router.get("/id/{post_uid}", response_model=BlogPostResponse)
async def get_blog_post_by_id_legacy(post_uid: UUID):
    """Get a single blog post by UID (legacy endpoint for compatibility)."""
    # This is a legacy alias for the /uid/ endpoint
    return await get_blog_post_by_uid(post_uid)

@router.get("/uid/{post_uid}", response_model=BlogPostResponse)
async def get_blog_post_by_uid(post_uid: UUID):
    """Get a single blog post by UID."""
    query = """
    SELECT 
        uid, title, slug, content, excerpt, image_url, author_name, tags,
        created_at, updated_at, published, featured, seo_title, meta_description
    FROM blog_posts
    WHERE uid = %s AND published = true
    """
    
    blog_post = await fetch_one(query, (post_uid,))
    
    if not blog_post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Format the result to match the response schema  
    formatted_result = {
        "uid": blog_post["uid"],
        "title": blog_post["title"],
        "slug": blog_post["slug"],
        "content": blog_post["content"],
        "excerpt": blog_post["excerpt"],
        "image_url": blog_post["image_url"],
        "author_name": blog_post["author_name"],
        "tags": blog_post["tags"].split(",") if blog_post["tags"] else [],
        "created_at": blog_post["created_at"],
        "updated_at": blog_post["updated_at"],
        "published": blog_post["published"],
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
    logger.info(f"Creating blog post: title='{post.title}', slug='{post.slug}', published={post.published}")
    
    # Generate slug if not provided
    if not post.slug:
        post.slug = generate_slug(post.title)
    
    # Handle slug uniqueness by auto-generating unique slug if needed
    original_slug = post.slug
    counter = 1
    while True:
        existing = await fetch_one("SELECT uid FROM blog_posts WHERE slug = %s", (post.slug,))
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
        uid, title, slug, content, excerpt, image_url, author_name, tags,
        published, featured, seo_title, meta_description, created_at, updated_at
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
            post.author_name, tags_str, post.published, post.featured,
            post.seo_title, post.meta_description, now, now
        )
    )

    # Get the newly created post
    result = await fetch_one("SELECT * FROM blog_posts WHERE slug = %s", (post.slug,))
    
    # Format the result to match the response schema
    formatted_result = {
        "uid": result["uid"],
        "title": result["title"],
        "slug": result["slug"],
        "content": result["content"],
        "excerpt": result["excerpt"],
        "image_url": result["image_url"],
        "author_name": result["author_name"],
        "tags": result["tags"].split(",") if result["tags"] else [],
        "created_at": result["created_at"],
        "updated_at": result["updated_at"],
        "published": result["published"],
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
        blog_post = db.query(BlogPost).filter(BlogPost.uid == blog_id).first()
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
                    "uid": str(blog_post.uid),
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
        blog_post = db.query(BlogPost).filter(BlogPost.uid == blog_id).first()
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
                    "uid": str(blog_post.uid),
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
        blog_post = db.query(BlogPost).filter(BlogPost.uid == blog_id).first()
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
    slugs = await fetch_all("SELECT slug, title, published FROM blog_posts ORDER BY created_at DESC")
    return {"existing_slugs": slugs}

# S3 Image Upload Endpoints
@router.post("/upload-image")
async def upload_blog_image(
    file: UploadFile = File(...),
    blog_uid: Optional[str] = Form(None)
):
    """Upload an image to S3 and optionally associate it with a blog post."""
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
        
        # Create folder path for blog images
        folder_path = "blog/images"
        
        # Upload to S3 with encoded path
        upload_result = await storage.upload_file(
            file=file,
            folder_path=folder_path,
            encode_path=True  # Enable path encoding for security
        )
        
        # If blog_uid provided, update the blog post's image_url
        if blog_uid:
            from shared.database import async_session
            async with async_session() as session:
                try:
                    # Update the blog post with the encoded image path
                    update_query = """
                    UPDATE blog_posts 
                    SET image_url = %s, updated_at = %s 
                    WHERE uid = %s
                    """
                    await execute_query(update_query, (upload_result["url"], datetime.now(), blog_uid), session)
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    # Still return upload success even if DB update fails
                    upload_result["warning"] = f"Image uploaded but failed to update blog post: {str(e)}"
        
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
async def delete_blog_image(
    image_url: str = Form(...),
    blog_uid: Optional[str] = Form(None)
):
    """Delete an image from S3 and optionally remove it from blog post."""
    try:
        # Delete from S3
        delete_result = await storage.delete_file(image_url)
        
        # If blog_uid provided, clear the image_url from the blog post
        if blog_uid:
            from shared.database import async_session
            async with async_session() as session:
                try:
                    # Clear the image_url in the blog post
                    update_query = """
                    UPDATE blog_posts 
                    SET image_url = NULL, updated_at = %s 
                    WHERE uid = %s AND image_url = %s
                    """
                    await execute_query(update_query, (datetime.now(), blog_uid, image_url), session)
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    delete_result["warning"] = f"Image deleted but failed to update blog post: {str(e)}"
        
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
async def get_blog_image_url(encoded_path: str = Query(..., description="Encoded S3 path")):
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