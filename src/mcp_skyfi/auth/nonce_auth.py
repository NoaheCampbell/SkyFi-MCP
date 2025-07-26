"""Nonce-based authentication system for secure API key handling."""
import secrets
import time
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NonceAuthManager:
    """Manage nonce-based authentication sessions."""
    
    def __init__(self, expiry_minutes: int = 5):
        """Initialize the nonce manager.
        
        Args:
            expiry_minutes: How long a nonce is valid for
        """
        self.sessions: Dict[str, Dict] = {}  # nonce -> session data
        self.expiry_minutes = expiry_minutes
        self._cleanup_interval = 60  # Cleanup every minute
        self._last_cleanup = time.time()
    
    def generate_auth_session(self, session_id: str) -> Tuple[str, str]:
        """Generate a new authentication session with nonce.
        
        Args:
            session_id: MCP session identifier
            
        Returns:
            (nonce, auth_url)
        """
        # Generate cryptographically secure nonce
        nonce = secrets.token_urlsafe(32)
        
        # Store session data
        self.sessions[nonce] = {
            'session_id': session_id,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=self.expiry_minutes),
            'status': 'pending',
            'api_key': None
        }
        
        # Cleanup old sessions periodically
        self._cleanup_expired()
        
        # Generate auth URL using configured domain
        import os
        ngrok_domain = os.environ.get('NGROK_DOMAIN', 'skyfi-mcp.ngrok-free.app')
        base_url = f"https://{ngrok_domain}"
        auth_url = f"{base_url}/auth/{nonce}"
        
        logger.info(f"Generated auth session for {session_id} with nonce {nonce[:8]}...")
        
        return nonce, auth_url
    
    def complete_auth(self, nonce: str, api_key: str) -> bool:
        """Complete authentication by associating API key with nonce.
        
        Args:
            nonce: The authentication nonce
            api_key: User's SkyFi API key
            
        Returns:
            True if successful
        """
        if nonce not in self.sessions:
            logger.warning(f"Invalid nonce attempted: {nonce[:8]}...")
            return False
        
        session = self.sessions[nonce]
        
        # Check if expired
        if datetime.utcnow() > session['expires_at']:
            logger.warning(f"Expired nonce attempted: {nonce[:8]}...")
            del self.sessions[nonce]
            return False
        
        # Check if already used
        if session['status'] != 'pending':
            logger.warning(f"Reused nonce attempted: {nonce[:8]}...")
            return False
        
        # Complete authentication
        session['api_key'] = api_key
        session['status'] = 'completed'
        session['authenticated_at'] = datetime.utcnow()
        
        logger.info(f"Completed auth for nonce {nonce[:8]}...")
        
        return True
    
    def get_api_key_for_session(self, session_id: str) -> Optional[str]:
        """Get API key for a session ID.
        
        Args:
            session_id: MCP session identifier
            
        Returns:
            API key if authenticated, None otherwise
        """
        # Find session by session_id
        for nonce, session in self.sessions.items():
            if (session['session_id'] == session_id and 
                session['status'] == 'completed' and
                session['api_key']):
                return session['api_key']
        
        return None
    
    def check_auth_status(self, nonce: str) -> Dict[str, any]:
        """Check the status of an auth session.
        
        Args:
            nonce: The authentication nonce
            
        Returns:
            Status information
        """
        if nonce not in self.sessions:
            return {'status': 'invalid'}
        
        session = self.sessions[nonce]
        
        if datetime.utcnow() > session['expires_at']:
            del self.sessions[nonce]
            return {'status': 'expired'}
        
        return {
            'status': session['status'],
            'created_at': session['created_at'].isoformat(),
            'expires_at': session['expires_at'].isoformat()
        }
    
    def _cleanup_expired(self):
        """Remove expired sessions."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = now
        current_time = datetime.utcnow()
        
        expired = [
            nonce for nonce, session in self.sessions.items()
            if current_time > session['expires_at']
        ]
        
        for nonce in expired:
            del self.sessions[nonce]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired auth sessions")


# Global instance
nonce_auth = NonceAuthManager()