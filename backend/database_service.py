"""
Database service for managing user data with Supabase
"""
from supabase_config import supabase_client
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.supabase = supabase_client

    async def create_user_profile(self, user_id: str, email: str, **kwargs) -> Dict[str, Any]:
        """Create a new user profile"""
        try:
            profile_data = {
                "id": user_id,
                "email": email,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                **kwargs
            }
            
            result = self.supabase.table("user_profiles").insert(profile_data).execute()
            logger.info(f"Created user profile for {user_id}")
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error creating user profile: {str(e)}")
            raise

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        try:
            result = self.supabase.table("user_profiles").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None

    async def update_user_profile(self, user_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update user profile"""
        try:
            update_data = {
                "updated_at": datetime.utcnow().isoformat(),
                **kwargs
            }
            
            result = self.supabase.table("user_profiles").update(update_data).eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return None

    # Note: File management is now handled by Supabase Storage
    # The processed_files table is no longer needed since Supabase Storage
    # provides file storage, metadata, and user-specific organization

    async def create_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Create user preferences"""
        try:
            prefs_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "preferences": preferences,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("user_preferences").insert(prefs_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating user preferences: {str(e)}")
            raise

    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences"""
        try:
            result = self.supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return None

    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user preferences"""
        try:
            result = self.supabase.table("user_preferences").update({
                "preferences": preferences,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
            return None

    # Note: User stats are now calculated from Supabase Storage files
    # in the server.py endpoints, eliminating the need for a separate table

# Global database service instance
db_service = DatabaseService()
