"""HTTP-compatible spending tracker using Redis."""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import redis.asyncio as redis


class HTTPSpendingTracker:
    """Track spending for HTTP server using Redis."""
    
    def __init__(self, redis_client: redis.Redis, user_id: str):
        """Initialize spending tracker for a specific user."""
        self.redis = redis_client
        self.user_id = user_id
        self.spending_key = f"spending:{user_id}:total"
        self.daily_key = f"spending:{user_id}:daily:{datetime.now().date()}"
        self.history_key = f"spending:{user_id}:history"
    
    async def get_total_spent(self) -> float:
        """Get total amount spent by user."""
        value = await self.redis.get(self.spending_key)
        return float(value) if value else 0.0
    
    async def get_daily_spent(self) -> float:
        """Get amount spent today."""
        value = await self.redis.get(self.daily_key)
        return float(value) if value else 0.0
    
    async def get_remaining_budget(self, limit: float) -> float:
        """Get remaining budget."""
        total = await self.get_total_spent()
        return max(0, limit - total)
    
    async def can_afford(self, cost: float, limit: float) -> bool:
        """Check if user can afford an order."""
        total = await self.get_total_spent()
        return total + cost <= limit
    
    async def add_spending(self, amount: float, order_details: Optional[Dict] = None):
        """Record a spending transaction."""
        # Update total spending
        await self.redis.incrbyfloat(self.spending_key, amount)
        
        # Update daily spending
        await self.redis.incrbyfloat(self.daily_key, amount)
        await self.redis.expire(self.daily_key, 86400)  # Expire after 24 hours
        
        # Add to history
        history_entry = {
            "amount": amount,
            "timestamp": datetime.now().isoformat(),
            "details": order_details or {}
        }
        await self.redis.lpush(self.history_key, json.dumps(history_entry))
        
        # Keep only last 100 entries
        await self.redis.ltrim(self.history_key, 0, 99)
    
    async def get_spending_history(self, limit: int = 10) -> List[Dict]:
        """Get recent spending history."""
        history = await self.redis.lrange(self.history_key, 0, limit - 1)
        return [json.loads(entry) for entry in history]
    
    async def reset_daily_spending(self):
        """Reset daily spending (for testing)."""
        await self.redis.delete(self.daily_key)