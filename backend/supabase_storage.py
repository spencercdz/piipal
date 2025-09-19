"""
Supabase Storage service for file management
"""
from supabase_config import supabase_client
from typing import Optional, Dict, Any
import logging
import uuid
from pathlib import Path
import tempfile
import shutil

logger = logging.getLogger(__name__)

class SupabaseStorageService:
    def __init__(self):
        self.supabase = supabase_client
        self.bucket_name = "processed-files"

    async def create_bucket(self) -> bool:
        """Create the storage bucket if it doesn't exist"""
        try:
            # Check if bucket exists
            buckets = self.supabase.storage.list_buckets()
            bucket_exists = any(bucket.name == self.bucket_name for bucket in buckets)
            
            if not bucket_exists:
                # Create bucket
                result = self.supabase.storage.create_bucket(
                    self.bucket_name,
                    options={
                        "public": True,  # Make files publicly accessible
                        "file_size_limit": 50 * 1024 * 1024,  # 50MB limit
                        "allowed_mime_types": [
                            "image/*",
                            "video/*",
                            "application/octet-stream"
                        ]
                    }
                )
                logger.info(f"Created storage bucket: {self.bucket_name}")
                return True
            else:
                logger.info(f"Storage bucket already exists: {self.bucket_name}")
                return True
        except Exception as e:
            logger.error(f"Error creating storage bucket: {str(e)}")
            return False

    async def upload_file(self, file_path: str, user_id: str, file_type: str) -> Optional[Dict[str, Any]]:
        """Upload a file to Supabase Storage"""
        try:
            # Create user-specific folder structure
            folder_path = f"{user_id}/{file_type}"
            
            # Generate unique filename
            file_name = Path(file_path).name
            unique_filename = f"{uuid.uuid4()}_{file_name}"
            
            # Upload file
            with open(file_path, 'rb') as file_data:
                result = self.supabase.storage.from_(self.bucket_name).upload(
                    path=f"{folder_path}/{unique_filename}",
                    file=file_data,
                    file_options={
                        "content-type": self._get_content_type(file_name),
                        "upsert": "true"  # Overwrite if exists
                    }
                )
            
            if result:
                # Get public URL
                public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(
                    f"{folder_path}/{unique_filename}"
                )
                
                logger.info(f"Uploaded file to Supabase Storage: {unique_filename}")
                
                return {
                    "filename": unique_filename,
                    "path": f"{folder_path}/{unique_filename}",
                    "public_url": public_url,
                    "size": Path(file_path).stat().st_size
                }
            else:
                logger.error("Failed to upload file to Supabase Storage")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading file to Supabase Storage: {str(e)}")
            return None

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from Supabase Storage"""
        try:
            result = self.supabase.storage.from_(self.bucket_name).remove([file_path])
            logger.info(f"Deleted file from Supabase Storage: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file from Supabase Storage: {str(e)}")
            return False

    async def list_user_files(self, user_id: str) -> list:
        """List all files for a specific user"""
        try:
            # List files in user's folder
            result = self.supabase.storage.from_(self.bucket_name).list(
                path=user_id,
                options={"limit": 1000}
            )
            
            files = []
            for item in result:
                if item.get('name'):  # Skip folders
                    file_path = f"{user_id}/{item['name']}"
                    public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
                    
                    files.append({
                        "filename": item['name'],
                        "path": file_path,
                        "public_url": public_url,
                        "size": item.get('metadata', {}).get('size', 0),
                        "created_at": item.get('created_at'),
                        "updated_at": item.get('updated_at')
                    })
            
            return files
        except Exception as e:
            logger.error(f"Error listing user files: {str(e)}")
            return []

    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        ext = Path(filename).suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.mp4': 'video/mp4',
            '.avi': 'video/avi',
            '.mov': 'video/quicktime',
            '.webm': 'video/webm',
            '.mkv': 'video/x-matroska',
            '.flv': 'video/x-flv',
            '.wmv': 'video/x-ms-wmv'
        }
        return content_types.get(ext, 'application/octet-stream')

    async def get_public_url(self, file_path: str) -> str:
        """Get public URL for a file"""
        try:
            return self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
        except Exception as e:
            logger.error(f"Error getting public URL: {str(e)}")
            return ""

# Global storage service instance
storage_service = SupabaseStorageService()
