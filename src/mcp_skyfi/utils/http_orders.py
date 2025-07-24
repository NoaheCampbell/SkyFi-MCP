"""HTTP-compatible order manager using Redis."""
import json
import secrets
import time
from typing import Dict, Optional

import redis.asyncio as redis


class HTTPOrderManager:
    """Manage orders for HTTP server using Redis."""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize order manager."""
        self.redis = redis_client
        self.order_prefix = "order:pending"
        self.expiry_seconds = 300  # 5 minutes
    
    async def create_pending_order(
        self,
        user_id: str,
        order_details: Dict,
        estimated_cost: float
    ) -> str:
        """Create a pending order that expires."""
        token = secrets.token_urlsafe(16)
        
        order_data = {
            "user_id": user_id,
            "token": token,
            "details": order_details,
            "estimated_cost": estimated_cost,
            "created_at": time.time(),
            "status": "pending"
        }
        
        # Store in Redis with expiration
        key = f"{self.order_prefix}:{token}"
        await self.redis.setex(
            key,
            self.expiry_seconds,
            json.dumps(order_data)
        )
        
        # Also store user->token mapping for lookup
        user_orders_key = f"user:orders:{user_id}"
        await self.redis.sadd(user_orders_key, token)
        await self.redis.expire(user_orders_key, self.expiry_seconds)
        
        return token
    
    async def get_pending_order(
        self,
        token: str,
        user_id: str
    ) -> Optional[Dict]:
        """Get a pending order if it exists and belongs to user."""
        key = f"{self.order_prefix}:{token}"
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        order = json.loads(data)
        
        # Verify ownership
        if order["user_id"] != user_id:
            return None
        
        return order
    
    async def confirm_order(self, token: str) -> bool:
        """Mark order as confirmed (for audit trail)."""
        key = f"{self.order_prefix}:{token}"
        data = await self.redis.get(key)
        
        if not data:
            return False
        
        order = json.loads(data)
        order["status"] = "confirmed"
        order["confirmed_at"] = time.time()
        
        # Move to confirmed orders
        confirmed_key = f"order:confirmed:{token}"
        await self.redis.set(confirmed_key, json.dumps(order))
        await self.redis.delete(key)
        
        return True
    
    async def get_user_pending_orders(self, user_id: str) -> List[Dict]:
        """Get all pending orders for a user."""
        user_orders_key = f"user:orders:{user_id}"
        tokens = await self.redis.smembers(user_orders_key)
        
        orders = []
        for token in tokens:
            order = await self.get_pending_order(token, user_id)
            if order:
                orders.append(order)
        
        return orders