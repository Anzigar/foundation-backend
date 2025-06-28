from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from fastapi.responses import JSONResponse
import os

from shared.storage import storage

router = APIRouter()

@router.post("/upload", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Form("uploads"),
    filename: str = Form(None)
):
    """Upload a file to S3 storage and return media browser compatible response."""
    success, message, url = await storage.upload_file(
        file=file,
        folder=folder,
        custom_filename=filename
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {message}")
    
    # Extract filename from URL or use original filename
    key = url.split('/')[-2] + '/' + url.split('/')[-1] if '/' in url else file.filename
    
    return {
        "id": 42,  # In real implementation, save to Media table and return actual ID
        "public_url": url,
        "key": key,
        "name": filename or file.filename,
        "url": url
    }

@router.get("/browse", status_code=200)
async def browse_media(
    folder: str = Query("", description="Folder path to browse"),
    max_items: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")
):
    """Browse media files in organized folders."""
    # Get files from storage
    success, message, files = storage.list_files(prefix=folder, max_items=max_items)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to browse media: {message}")
    
    # Organize files by type
    images = []
    videos = []
    documents = []
    
    for file in files:
        key_lower = file['key'].lower()
        item = {
            "key": file['key'],
            "name": os.path.basename(file['key']),
            "url": file['url'],
            "thumbnail": file['url'] if key_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) else None,
            "tags": ["featured"] if "featured" in file['key'] else []
        }
        
        if key_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')):
            images.append(item)
        elif key_lower.endswith(('.mp4', '.webm', '.mov', '.avi')):
            videos.append(item)
        elif key_lower.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt')):
            documents.append(item)
    
    return {
        "folders": [
            {"name": "Blog Images", "path": "/blog-images"},
            {"name": "Event Photos", "path": "/event-photos"},
            {"name": "Project Images", "path": "/project-images"}
        ],
        "images": {"items": images},
        "videos": {"items": videos},
        "documents": {"items": documents}
    }

@router.delete("/file")
async def delete_file(url: str):
    """Delete a file from S3 storage."""
    success, message = storage.delete_file(url)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {message}")
    
    return {"message": "File deleted successfully"}

# Legacy endpoints for backward compatibility
@router.post("/image", status_code=201)
async def upload_image(file: UploadFile = File(...), folder: str = Form("images")):
    """Legacy image upload endpoint."""
    return await upload_file(file, folder)

@router.post("/blog-image", status_code=201)
async def upload_blog_image(file: UploadFile = File(...)):
    """Upload image for blog."""
    return await upload_file(file, "blog-images")

@router.post("/news-image", status_code=201)
async def upload_news_image(file: UploadFile = File(...)):
    """Upload image for news."""
    return await upload_file(file, "news-images")

@router.post("/project-image", status_code=201)
async def upload_project_image(file: UploadFile = File(...)):
    """Upload image for projects."""
    return await upload_file(file, "project-images")
