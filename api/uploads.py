from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends, Path, Query
from fastapi.responses import JSONResponse

from shared.storage import storage

router = APIRouter()

@router.post("/image", status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    folder: str = Form("images"),
    filename: str = Form(None)
):
    """
    Upload an image to S3 storage.
    
    Args:
        file: The image file to upload
        folder: The subfolder to store the image in (default: "images")
        filename: Optional custom filename
        
    Returns:
        JSON response with the URL of the uploaded image
    """
    # Validate file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image (JPEG, PNG, GIF, etc.)"
        )
    
    # Upload to S3
    success, message, url = await storage.upload_file(
        file=file,
        folder=folder,
        custom_filename=filename
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image: {message}"
        )
    
    return {
        "url": url,
        "message": "Image uploaded successfully"
    }

@router.delete("/image", status_code=200)
async def delete_image(url: str):
    """
    Delete an image from S3 storage.
    
    Args:
        url: The full URL of the image to delete
        
    Returns:
        JSON response with deletion status
    """
    success, message = storage.delete_file(url)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete image: {message}"
        )
    
    return {
        "message": "Image deleted successfully"
    }

# Specialized endpoints for different content types
@router.post("/blog-image", status_code=201)
async def upload_blog_image(file: UploadFile = File(...), filename: str = Form(None)):
    """Upload an image specifically for blog posts."""
    return await upload_image(file, "blog-images", filename)

@router.post("/news-image", status_code=201)
async def upload_news_image(file: UploadFile = File(...), filename: str = Form(None)):
    """Upload an image specifically for news articles."""
    return await upload_image(file, "news-images", filename)

@router.post("/event-image", status_code=201)
async def upload_event_image(file: UploadFile = File(...), filename: str = Form(None)):
    """Upload an image specifically for events."""
    return await upload_image(file, "event-images", filename)

@router.get("/media", status_code=200)
async def list_media_files(
    folder: str = Query("images", description="Folder to list files from"),
    max_items: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")
):
    """
    List files in a folder in S3 storage.
    
    Args:
        folder: The folder to list files from
        max_items: Maximum number of items to return
        
    Returns:
        JSON response with the list of files
    """
    success, message, files = storage.list_files(prefix=folder, max_items=max_items)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list media: {message}"
        )
    
    return {
        "items": files,
        "count": len(files),
        "folder": folder
    }

@router.get("/media/{key:path}", status_code=200)
async def get_media_url(
    key: str = Path(..., description="File key/path in S3"),
    expires_in: int = Query(3600, ge=60, le=86400, description="URL expiration time in seconds")
):
    """
    Generate a pre-signed URL for a file in S3 storage.
    
    Args:
        key: The key/path of the file in S3
        expires_in: URL expiration time in seconds
        
    Returns:
        JSON response with the pre-signed URL
    """
    success, message, url = storage.get_file_url(key=key, expires_in=expires_in)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate URL: {message}"
        )
    
    return {
        "url": url,
        "expires_in": expires_in,
        "key": key
    }

@router.get("/browse/{folder:path}", status_code=200)
async def browse_media(
    folder: str = Path(..., description="Folder path to browse"),  # Changed to ... (required)
    max_items: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")
):
    """
    Browse media files in a specific folder.
    Returns more structured data for building a media browser UI.
    
    Args:
        folder: The folder path to browse
        max_items: Maximum number of items to return
    
    Returns:
        JSON response with categorized media files
    """
    success, message, files = storage.list_files(prefix=folder, max_items=max_items)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to browse media: {message}"
        )
    
    # Categorize files by type
    images = []
    documents = []
    videos = []
    other = []
    
    for file in files:
        key = file['key'].lower()
        if key.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')):
            images.append(file)
        elif key.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt')):
            documents.append(file)
        elif key.endswith(('.mp4', '.webm', '.mov', '.avi')):
            videos.append(file)
        else:
            other.append(file)
    
    return {
        "folder": folder,
        "total_count": len(files),
        "images": {
            "count": len(images),
            "items": images
        },
        "documents": {
            "count": len(documents),
            "items": documents
        },
        "videos": {
            "count": len(videos),
            "items": videos
        },
        "other": {
            "count": len(other),
            "items": other
        }
    }
