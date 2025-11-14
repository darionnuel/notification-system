"""Client for interacting with User Service."""
import httpx
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.async_circuit_breaker import AsyncCircuitBreaker


class UserServiceClient:
    """Client for fetching user data from User Service."""
    
    def __init__(self):
        """Initialize user service client."""
        self.base_url = settings.user_service_url
        self.timeout = settings.user_service_timeout
        self.circuit_breaker = AsyncCircuitBreaker(
            name="UserService",
            failure_threshold=3,
            timeout=30
        )
    
    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """
        Fetch user details from User Service by ID.
        
        Args:
            user_id: User identifier
            
        Returns:
            User data dictionary with fields:
                - id: User ID
                - email: User's email address
                - name: User's full name
                - first_name: User's first name
                - last_name: User's last name
                - preferences: User notification preferences
                  - email_enabled: bool
                  - push_enabled: bool
                  - language: str (e.g., "en", "es")
            
        Raises:
            Exception: If user not found or service unavailable
        """
        url = f"{self.base_url}/api/v1/users/{user_id}"
        
        async def fetch():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                if not data.get("success"):
                    raise Exception(f"User Service error: {data.get('message')}")
                
                return data["data"]
        
        try:
            return await self.circuit_breaker.call(fetch)
        except Exception as e:
            raise Exception(f"Failed to fetch user {user_id}: {str(e)}")
    
    async def check_email_preference(self, user_id: str) -> bool:
        """
        Check if user has email notifications enabled.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if email notifications are enabled, False otherwise
        """
        try:
            user = await self.get_user_by_id(user_id)
            preferences = user.get("preferences", {})
            return preferences.get("email_enabled", True)  # Default to True if not specified
        except Exception as e:
            print(f"⚠️ Warning: Could not check email preference for user {user_id}: {e}")
            return True  # Default to allowing emails if preference check fails
    
    def extract_user_email(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract email address from user data.
        
        Args:
            user_data: User data dictionary
            
        Returns:
            User's email address or None
        """
        return user_data.get("email")
    
    def extract_user_name(self, user_data: Dict[str, Any]) -> str:
        """
        Extract user's full name from user data.
        
        Args:
            user_data: User data dictionary
            
        Returns:
            User's full name (or concatenated first/last name)
        """
        # Try to get full name first
        name = user_data.get("name")
        if name:
            return name
        
        # Otherwise, concatenate first and last name
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")
        
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        
        return "User"  # Default fallback
    
    def extract_user_language(self, user_data: Dict[str, Any]) -> str:
        """
        Extract user's preferred language from user data.
        
        Args:
            user_data: User data dictionary
            
        Returns:
            Language code (e.g., "en", "es", "fr")
        """
        preferences = user_data.get("preferences", {})
        return preferences.get("language", "en")  # Default to English


# Global instance
user_client = UserServiceClient()
