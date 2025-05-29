from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import json  # Add this import at the top

from blog.schemas import (
    BlogPostCreate, 
    BlogPostResponse, 
)
from shared.utils import generate_slug
from shared.database import get_db

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

async def fetch_all(query: str, params: Optional[tuple] = None, db: AsyncSession = None) -> List[Dict[str, Any]]:
    """Execute a query and fetch all results as dicts using SQLAlchemy."""
    if db is None:
        # For standalone function calls, create a session
        from shared.database import async_session
        async with async_session() as session:
            return await _fetch_with_session(query, params, session)
    else:
        # Use provided session
        return await _fetch_with_session(query, params, db)

async def _fetch_with_session(query: str, params: Optional[tuple], session: AsyncSession) -> List[Dict[str, Any]]:
    # Convert ? placeholders to :param1, :param2, etc. for SQLAlchemy
    if params:
        # Replace each ? with a numbered parameter
        param_dict = {}
        for i, param in enumerate(params):
            param_name = f"param{i+1}"
            param_dict[param_name] = param
            
        # Replace one ? at a time with the appropriate :paramN
        modified_query = query
        for i in range(len(params)):
            # Replace only the first ? with :paramN
            modified_query = modified_query.replace('?', f':{param_name}', 1)
            
        result = await session.execute(text(modified_query), param_dict)
    else:
        result = await session.execute(text(query))
    
    return [dict(row) for row in result.mappings()]

async def fetch_one(query: str, params: Optional[tuple] = None, db: AsyncSession = None) -> Optional[Dict[str, Any]]:
    """Execute a SQL query and fetch one result as dict using SQLAlchemy."""
    results = await fetch_all(query, params, db)
    return results[0] if results else None

async def execute_query(query: str, params: Optional[tuple] = None, db: AsyncSession = None) -> int:
    """Execute a SQL query and return the number of affected rows using SQLAlchemy."""
    if db is None:
        # For standalone function calls, create a session
        from shared.database import async_session
        async with async_session() as session:
            return await _execute_with_session(query, params, session)
    else:
        # Use provided session
        return await _execute_with_session(query, params, db)

async def _execute_with_session(query: str, params: Optional[tuple], session: AsyncSession) -> int:
    # Convert ? placeholders to :param1, :param2, etc. for SQLAlchemy
    if params:
        # Create a dictionary of named parameters
        param_dict = {}
        for i, param in enumerate(params):
            param_dict[f"param{i+1}"] = param
            
        # Replace one ? at a time with the appropriate :paramN
        modified_query = query
        for i in range(len(params)):
            param_name = f"param{i+1}"
            # Replace only the first ? with :paramN
            modified_query = modified_query.replace('?', f':{param_name}', 1)
            
        result = await session.execute(text(modified_query), param_dict)
    else:
        result = await session.execute(text(query))
    
    await session.commit()
    return result.rowcount

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
    # Base query with joins to get tags and author - SQLite syntax
    query = """
    SELECT 
        bp.id, bp.title, bp.slug, bp.excerpt, bp.featured_image_url, 
        bp.author_id, u.username as author_username, u.full_name as author_full_name,
        u.bio as author_bio, u.profile_image_url as author_profile_image_url,
        u.social_links as author_social_links,
        bp.published_at, bp.created_at, bp.view_count, bp.comment_count,
        bt.id as tag_id, bt.name as tag_name, bt.slug as tag_slug, bt.description as tag_description
    FROM blog_posts bp
    JOIN users u ON bp.author_id = u.id
    LEFT JOIN blog_post_tags bpt ON bp.id = bpt.post_id
    LEFT JOIN blog_tags bt ON bpt.tag_id = bt.id
    WHERE bp.published = 1
    """
    
    params = []
    
    # Apply filters - SQLite uses ? for parameters
    if tag_id:
        query += " AND bt.id = ?"
        params.append(tag_id)
    
    if search:
        query += " AND (bp.title LIKE ? OR bp.content LIKE ? OR bp.introduction LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    # Apply cursor pagination
    if cursor:
        if order.lower() == "desc":
            query += " AND bp.id < ?"
        else:
            query += " AND bp.id > ?"
        params.append(cursor)
    
    # Order the results
    if order.lower() == "desc":
        query += " ORDER BY bp.id DESC"
    else:
        query += " ORDER BY bp.id ASC"
    
    # Execute the query with parameters
    blog_items = await fetch_all(query, tuple(params) if params else None, db)
    
    # Format the results
    formatted_blogs = format_blog_with_tags_and_author(blog_items)
    
    # Remove duplicates (because of the LEFT JOIN with tags)
    unique_blogs = []
    seen_ids = set()
    for blog in formatted_blogs:
        if blog["id"] not in seen_ids:
            unique_blogs.append(blog)
            seen_ids.add(blog["id"])
    
    # Get one more item to check if there are more results
    has_more = len(unique_blogs) > limit
    if has_more:
        unique_blogs = unique_blogs[:limit]
    
    # Get the next cursor
    next_cursor = str(unique_blogs[-1]["id"]) if has_more and unique_blogs else None
    
    return {
        "items": unique_blogs,
        "next_cursor": next_cursor,
        "has_more": has_more
    }

@router.get("/{slug}", response_model=BlogPostResponse)
async def get_blog_post(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a single blog post by slug with tags, author, and related posts."""
    # Increment view count - SQLite syntax
    await execute_query(
        "UPDATE blog_posts SET view_count = view_count + 1 WHERE slug = ?",
        (slug,),
        db
    )
    
    # Get the blog post, its tags, and author info - SQLite syntax
    query = """
    SELECT 
        bp.id, bp.title, bp.slug, bp.introduction, bp.content, bp.excerpt,
        bp.featured_image_url, bp.cta_text, bp.cta_link, bp.allow_comments,
        bp.seo_title, bp.meta_description, bp.og_image_url, bp.newsletter_form_enabled,
        bp.published, bp.published_at, bp.created_at, bp.updated_at,
        bp.view_count, bp.share_count, bp.comment_count, bp.related_posts,
        bp.author_id, u.username as author_username, u.full_name as author_full_name,
        u.bio as author_bio, u.profile_image_url as author_profile_image_url,
        u.social_links as author_social_links,
        bt.id as tag_id, bt.name as tag_name, bt.slug as tag_slug, bt.description as tag_description
    FROM blog_posts bp
    JOIN users u ON bp.author_id = u.id
    LEFT JOIN blog_post_tags bpt ON bp.id = bpt.post_id
    LEFT JOIN blog_tags bt ON bpt.tag_id = bt.id
    WHERE bp.slug = ? AND bp.published = 1
    """
    
    blog_items = await fetch_all(query, (slug,), db)
    
    if not blog_items:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Format the result
    formatted_blogs = format_blog_with_tags_and_author(blog_items)
    
    return formatted_blogs[0]

@router.post("/", response_model=BlogPostResponse, status_code=status.HTTP_201_CREATED)
async def create_blog_post(post: BlogPostCreate, db: AsyncSession = Depends(get_db)):
    """Create a new blog post."""
    # Generate slug if not provided
    if not post.slug:
        post.slug = generate_slug(post.title)
    
    # Check for slug uniqueness - SQLite syntax
    existing = await fetch_one("SELECT id FROM blog_posts WHERE slug = ?", (post.slug,), db)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Blog post with slug '{post.slug}' already exists"
        )
    
    # Format related posts as JSON
    related_posts = []
    if post.related_post_ids:
        # Create placeholders for SQLite IN clause
        placeholders = ','.join('?' * len(post.related_post_ids))
        related_posts_data = await fetch_all(
            f"SELECT id, title, slug, featured_image_url FROM blog_posts WHERE id IN ({placeholders})",
            tuple(post.related_post_ids)
        )
        related_posts = related_posts_data if related_posts_data else []
    
    # Serialize related_posts to JSON string
    related_posts_json = json.dumps(related_posts)

    query = """
    INSERT INTO blog_posts (
        title, slug, introduction, content, excerpt, featured_image_url,
        cta_text, cta_link, allow_comments, seo_title, meta_description,
        og_image_url, newsletter_form_enabled, published, published_at,
        author_id, related_posts
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    # Define published_at before using it
    published_at = datetime.utcnow() if post.published else None

    # Define author_id (replace with actual authenticated user ID in production)
    author_id = 1  # Temporary placeholder for author ID

    await execute_query(
        query, 
        (
            post.title, post.slug, post.introduction, post.content, post.excerpt,
            post.featured_image_url, post.cta_text, post.cta_link, post.allow_comments,
            post.seo_title, post.meta_description, post.og_image_url,
            post.newsletter_form_enabled, post.published, published_at,
            author_id, related_posts_json
        ),
        db
    )

    # Get the inserted post ID - SQLite syntax
    post_id_row = await fetch_one("SELECT last_insert_rowid() as id", db=db)
    post_id = post_id["id"] if post_id else None

    # Add tags if provided
    if post.tag_ids and post_id:
        values = []
        params = []
        
        for tag_id in post.tag_ids:
            values.append("(?, ?)")
            params.extend([post_id, tag_id])
        
        if values:
            tags_query = f"""
            INSERT INTO blog_post_tags (post_id, tag_id)
            VALUES {', '.join(values)}
            """
            await execute_query(tags_query, tuple(params), db)

    # Get the newly created post
    return await get_blog_post(post.slug, db)
