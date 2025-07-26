"""Header-based authentication for MCP requests."""
import logging
from typing import Optional, Dict, Any
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Context variable to store the API key for the current request
current_api_key: ContextVar[Optional[str]] = ContextVar('current_api_key', default=None)


class HeaderAuthManager:
    """Manage API keys from request headers."""
    
    @staticmethod
    def extract_api_key_from_context(context: Dict[str, Any]) -> Optional[str]:
        """Extract API key from MCP request context.
        
        MCP passes headers in the request context.
        """
        # Check for headers in context
        headers = context.get('headers', {})
        
        # Look for API key in various header formats
        api_key = (
            headers.get('X-Skyfi-Api-Key') or
            headers.get('x-skyfi-api-key') or
            headers.get('Authorization', '').replace('Bearer ', '') or
            headers.get('authorization', '').replace('Bearer ', '')
        )
        
        if api_key:
            logger.debug("API key found in request headers")
            return api_key
        
        # Check if it's in the MCP metadata
        metadata = context.get('metadata', {})
        api_key = metadata.get('skyfi_api_key')
        
        if api_key:
            logger.debug("API key found in request metadata")
            return api_key
        
        return None
    
    @staticmethod
    def set_context_api_key(api_key: str) -> None:
        """Set the API key for the current context."""
        current_api_key.set(api_key)
    
    @staticmethod
    def get_context_api_key() -> Optional[str]:
        """Get the API key from the current context."""
        return current_api_key.get()
    
    @staticmethod
    def clear_context() -> None:
        """Clear the current context."""
        current_api_key.set(None)


# Global instance
header_auth = HeaderAuthManager()