"""
Supabase configuration and client setup for backend
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SupabaseConfig:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role key for backend
        
        if not self.url or not self.key:
            raise ValueError("Missing Supabase environment variables. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        
        self.client: Client = create_client(self.url, self.key)
        logger.info("Supabase client initialized successfully")

    def get_client(self) -> Client:
        """Get the Supabase client instance"""
        return self.client

    def test_connection(self) -> bool:
        """Test the Supabase connection"""
        try:
            # Try to query a simple table to test connection
            result = self.client.table("user_profiles").select("id").limit(1).execute()
            logger.info("Supabase connection test successful")
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {str(e)}")
            return False

# Global Supabase instance
supabase_config = SupabaseConfig()
supabase_client = supabase_config.get_client()
