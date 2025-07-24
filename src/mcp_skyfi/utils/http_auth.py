"""HTTP authentication utilities."""
import hashlib
import json
from typing import Dict, Optional

import redis.asyncio as redis


async def verify_api_key(
    api_key: str,
    redis_client: redis.Redis
) -> Optional[Dict[str, Any]]:
    """Verify API key and return user info."""
    # For production, this would check against a database
    # For now, we'll use a simple Redis lookup
    
    # Hash the API key for storage
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    user_key = f"apikey:{key_hash}"
    
    user_data = await redis_client.get(user_key)
    if user_data:
        return json.loads(user_data)
    
    # For demo purposes, accept the SkyFi API key format
    if api_key.startswith("lucas@skyfi.com:"):
        # Create a user record
        user = {
            "id": "lucas",
            "email": "lucas@skyfi.com",
            "api_key_hash": key_hash,
            "limits": {
                "total": 40.0,
                "daily": 40.0,
                "per_order": 20.0
            }
        }
        
        # Store in Redis
        await redis_client.set(user_key, json.dumps(user))
        return user
    
    return None


async def create_api_key(
    redis_client: redis.Redis,
    user_id: str,
    email: str
) -> str:
    """Create a new API key for a user."""
    import secrets
    
    # Generate API key
    api_key = f"{email}:{secrets.token_hex(32)}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Store user data
    user = {
        "id": user_id,
        "email": email,
        "api_key_hash": key_hash,
        "limits": {
            "total": 40.0,
            "daily": 40.0,
            "per_order": 20.0
        }
    }
    
    user_key = f"apikey:{key_hash}"
    await redis_client.set(user_key, json.dumps(user))
    
    return api_key