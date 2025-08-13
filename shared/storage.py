import os
import uuid
from typing import Optional, BinaryIO, Dict, Any, Tuple, List
import logging
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile

from config import settings
from shared.utils import encode_s3_path, decode_s3_path, generate_secure_filename

logger = logging.getLogger(__name__)

class S3Storage:
    """S3 storage utility for managing file uploads to AWS S3."""
    
    def __init__(self):
        """Initialize S3 client using environment variables."""
        self.aws_access_key = settings.AWS_ACCESS_KEY_ID
        self.aws_secret_key = settings.AWS_SECRET_ACCESS_KEY
        self.region_name = settings.AWS_REGION
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        self.s3_client = self._get_s3_client()
        
    def _get_s3_client(self):
        """Create and return an S3 client."""
        try:
            return boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region_name
            )
        except Exception as e:
            logger.error(f"Failed to create S3 client: {str(e)}")
            return None
    
    async def upload_file(
        self, 
        file: UploadFile, 
        folder: str = "uploads",
        custom_filename: Optional[str] = None,
        encode_path: bool = True
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Upload a file to S3 bucket.
        
        Args:
            file: The file to upload
            folder: The folder within the bucket to store the file
            custom_filename: Optional custom filename, if not provided a secure filename will be generated
            encode_path: Whether to return encoded path for security (default: True)
            
        Returns:
            Tuple of (success status, message, url/encoded_path if successful)
        """
        if not self.s3_client:
            return False, "S3 client not initialized", None
            
        try:
            # Generate secure filename if not provided
            if custom_filename:
                filename = custom_filename
            else:
                filename = generate_secure_filename(file.filename, folder.replace("/", "_"))
            
            # Construct S3 path
            s3_path = f"{folder}/{filename}"
            
            # Read file content
            file_content = await file.read()
            
            # Upload to S3
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_path,
                Body=file_content,
                ContentType=file.content_type
            )
            
            if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
                # Generate URL for the uploaded file
                file_url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{s3_path}"
                
                # Return encoded path if requested, otherwise return full URL
                if encode_path:
                    encoded_path = encode_s3_path(file_url)
                    return True, "File uploaded successfully", encoded_path
                else:
                    return True, "File uploaded successfully", file_url
            else:
                return False, "Failed to upload file", None
                
        except ClientError as e:
            logger.error(f"S3 client error: {str(e)}")
            return False, f"S3 client error: {str(e)}", None
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return False, f"Error uploading file: {str(e)}", None
        finally:
            # Reset file position for potential reuse
            await file.seek(0)
    
    def get_actual_url(self, encoded_path_or_url: str) -> str:
        """
        Get the actual S3 URL from an encoded path or return the URL if it's already decoded.
        
        Args:
            encoded_path_or_url: Encoded path or full S3 URL
            
        Returns:
            Full S3 URL
        """
        # If it's already a full URL, return as is
        if encoded_path_or_url.startswith('http'):
            return encoded_path_or_url
        
        # Otherwise, decode the path
        return decode_s3_path(encoded_path_or_url, self.bucket_name, self.region_name)
    
    def delete_file(self, encoded_path_or_url: str) -> Tuple[bool, str]:
        """
        Delete a file from S3 bucket.
        
        Args:
            encoded_path_or_url: Encoded path or full URL of the file to delete
            
        Returns:
            Tuple of (success status, message)
        """
        if not self.s3_client:
            return False, "S3 client not initialized"
            
        try:
            # Get the actual URL if it's encoded
            file_url = self.get_actual_url(encoded_path_or_url)
            
            # Extract key from URL
            path_parts = file_url.split(f"{self.bucket_name}.s3.{self.region_name}.amazonaws.com/")[1]
            
            # Delete from S3
            response = self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=path_parts
            )
            
            if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 204:
                return True, "File deleted successfully"
            else:
                return False, "Failed to delete file"
                
        except ClientError as e:
            logger.error(f"S3 client error: {str(e)}")
            return False, f"S3 client error: {str(e)}"
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False, f"Error deleting file: {str(e)}"
    
    def get_file_url(self, key: str, expires_in: int = 3600) -> Tuple[bool, str, Optional[str]]:
        """
        Generate a pre-signed URL for a file in S3.
        
        Args:
            key: The key (path) of the file in S3
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Tuple of (success status, message, url if successful)
        """
        if not self.s3_client:
            return False, "S3 client not initialized", None
            
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expires_in
            )
            return True, "URL generated successfully", url
        except Exception as e:
            logger.error(f"Error generating pre-signed URL: {str(e)}")
            return False, f"Error generating pre-signed URL: {str(e)}", None
    
    async def download_file(self, key: str, local_path: str) -> Tuple[bool, str]:
        """
        Download a file from S3 to a local path.
        
        Args:
            key: The key (path) of the file in S3
            local_path: The local path to save the file to
            
        Returns:
            Tuple of (success status, message)
        """
        if not self.s3_client:
            return False, "S3 client not initialized"
            
        try:
            with open(local_path, 'wb') as f:
                self.s3_client.download_fileobj(
                    Bucket=self.bucket_name,
                    Key=key,
                    Fileobj=f
                )
            return True, "File downloaded successfully"
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return False, f"Error downloading file: {str(e)}"
    
    def list_files(self, prefix: str = "", max_items: int = 1000) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """
        List files in a folder/prefix in the S3 bucket.
        
        Args:
            prefix: The prefix/folder to list files from
            max_items: Maximum number of items to return
            
        Returns:
            Tuple of (success status, message, list of file data if successful)
        """
        if not self.s3_client:
            return False, "S3 client not initialized", None
            
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_items
            )
            
            if 'Contents' not in response:
                return True, "No files found", []
                
            files = []
            for item in response['Contents']:
                files.append({
                    'key': item['Key'],
                    'size': item['Size'],
                    'last_modified': item['LastModified'],
                    'url': f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{item['Key']}"
                })
                
            return True, f"Found {len(files)} files", files
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return False, f"Error listing files: {str(e)}", None

# Create a singleton instance
storage = S3Storage()
