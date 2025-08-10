"""
Enhanced image upload utilities for content management.
Ensures all images are properly uploaded to S3 and managed through the media system.
"""

from typing import Optional, Tuple, Dict, Any
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from shared.storage import storage
from shared.media_models import Media


async def upload_content_image(
    file: UploadFile,
    folder: str = "content",
    content_type: str = "general",
    db: Optional[Session] = None
) -> Tuple[str, Optional[int]]:
    """
    Upload an image for content (blog, news, events, projects) to S3.
    
    Args:
        file: The uploaded file
        folder: S3 folder to store the image (e.g., 'blog', 'news', 'events', 'projects')
        content_type: Type of content this image belongs to
        db: Database session for storing media record
    
    Returns:
        Tuple of (image_url, media_id)
    """
    # Validate that it's an image
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Upload to S3
    success, message, url = await storage.upload_file(
        file=file,
        folder=f"{folder}/images",
        custom_filename=None  # Let it generate a unique filename
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {message}")
    
    # Store in media database if session provided
    media_id = None
    if db:
        try:
            # Extract filename from S3 key
            filename = url.split("/")[-1]
            file_key = f"{folder}/images/{filename}"
            
            # Create media record
            media = Media(
                name=file.filename,
                file_key=file_key,
                url=url,
                thumbnail_url=url,  # For images, the URL serves as thumbnail
                file_type="image",
                file_size=0,  # Could be enhanced to get actual file size
                mime_type=file.content_type,
                tags=[content_type, folder],
                folder=f"{folder}/images"
            )
            db.add(media)
            db.commit()
            db.refresh(media)
            media_id = media.id
        except Exception as e:
            # Don't fail the upload if database record fails
            print(f"Warning: Could not create media record: {e}")
    
    return url, media_id


async def replace_image_url(
    old_url: Optional[str],
    new_file: Optional[UploadFile],
    folder: str,
    content_type: str,
    db: Optional[Session] = None
) -> Optional[str]:
    """
    Replace an existing image URL with a new uploaded image.
    Deletes the old image from S3 if it exists.
    
    Args:
        old_url: Current image URL to replace
        new_file: New image file to upload
        folder: S3 folder for the new image
        content_type: Type of content
        db: Database session
    
    Returns:
        New image URL or None if no new file provided
    """
    # Delete old image if it exists and is from our S3 bucket
    if old_url and storage.bucket_name in old_url:
        try:
            storage.delete_file(old_url)
            # Also remove from database
            if db:
                media = db.query(Media).filter(Media.url == old_url).first()
                if media:
                    db.delete(media)
                    db.commit()
        except Exception as e:
            print(f"Warning: Could not delete old image: {e}")
    
    # Upload new image if provided
    if new_file:
        new_url, _ = await upload_content_image(new_file, folder, content_type, db)
        return new_url
    
    return None


def get_s3_image_url(url: Optional[str]) -> Optional[str]:
    """
    Ensure the image URL is a proper S3 URL.
    If it's a relative path or local URL, this function could be enhanced
    to handle migration of existing images to S3.
    
    Args:
        url: Current image URL
    
    Returns:
        S3 URL or None
    """
    if not url:
        return None
    
    # If already an S3 URL, return as is
    if url.startswith("https://") and storage.bucket_name in url:
        return url
    
    # If it's a relative path or local URL, you might want to:
    # 1. Log a warning that this image needs migration
    # 2. Return the URL as-is for now
    # 3. Or implement automatic migration logic
    
    return url


def validate_image_file(file: UploadFile) -> bool:
    """
    Validate that the uploaded file is a supported image format.
    
    Args:
        file: The uploaded file
    
    Returns:
        True if valid image, False otherwise
    """
    if not file.content_type:
        return False
    
    supported_types = [
        "image/jpeg",
        "image/jpg", 
        "image/png",
        "image/gif",
        "image/webp"
    ]
    
    return file.content_type.lower() in supported_types
