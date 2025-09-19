"""
Authentication middleware for FastAPI backend using Supabase
"""
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase_config import supabase_client
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

security = HTTPBearer()

class AuthMiddleware:
    def __init__(self):
        self.supabase = supabase_client

    async def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """
        Verify JWT token and return user information
        """
        try:
            # Verify the JWT token with Supabase
            response = self.supabase.auth.get_user(credentials.credentials)
            
            if not response.user:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            user = response.user
            logger.info(f"User authenticated: {user.id}")
            
            return {
                "user_id": user.id,
                "email": user.email,
                "user_metadata": user.user_metadata,
                "app_metadata": user.app_metadata,
                "token": credentials.credentials
            }
            
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid or expired token")

    async def get_current_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Get current user from request headers (optional authentication)
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        try:
            response = self.supabase.auth.get_user(token)
            if response.user:
                return {
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata,
                    "app_metadata": response.user.app_metadata,
                    "token": token
                }
        except Exception as e:
            logger.warning(f"Optional auth failed: {str(e)}")
        
        return None

# Global auth middleware instance
auth_middleware = AuthMiddleware()

# Dependency functions for FastAPI
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Required authentication dependency"""
    return await auth_middleware.verify_token(credentials)

async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Optional authentication dependency"""
    return await auth_middleware.get_current_user(request)
