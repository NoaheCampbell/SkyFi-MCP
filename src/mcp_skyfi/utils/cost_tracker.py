"""Cost tracking and enforcement for SkyFi orders."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import logging

logger = logging.getLogger(__name__)


class CostTracker:
    """Track and enforce spending limits for SkyFi orders."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize cost tracker."""
        if data_dir is None:
            # Use user's home directory for persistent storage
            data_dir = Path.home() / ".mcp-skyfi"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.cost_file = self.data_dir / "cost_tracking.json"
        self.orders = self._load_orders()
    
    def _load_orders(self) -> Dict:
        """Load order history from file."""
        if self.cost_file.exists():
            try:
                with open(self.cost_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cost tracking file: {e}")
        
        return {
            "total_spent": 0.0,
            "orders": [],
            "created_at": datetime.now().isoformat()
        }
    
    def _save_orders(self):
        """Save order history to file."""
        try:
            with open(self.cost_file, 'w') as f:
                json.dump(self.orders, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cost tracking file: {e}")
    
    def get_total_spent(self) -> float:
        """Get total amount spent."""
        return self.orders["total_spent"]
    
    def get_remaining_budget(self, limit: float) -> float:
        """Get remaining budget."""
        return max(0, limit - self.get_total_spent())
    
    def can_afford(self, cost: float, limit: float) -> bool:
        """Check if order is within budget."""
        return self.get_total_spent() + cost <= limit
    
    def record_order(self, archive_id: str, cost: float, details: Dict):
        """Record a completed order."""
        order = {
            "archive_id": archive_id,
            "cost": cost,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        
        self.orders["orders"].append(order)
        self.orders["total_spent"] += cost
        self._save_orders()
        
        logger.info(f"Recorded order: {archive_id} for ${cost:.2f}")
        logger.info(f"Total spent: ${self.get_total_spent():.2f}")
    
    def get_order_history(self) -> List[Dict]:
        """Get order history."""
        return self.orders["orders"]
    
    def reset_tracking(self):
        """Reset cost tracking (admin function)."""
        self.orders = {
            "total_spent": 0.0,
            "orders": [],
            "created_at": datetime.now().isoformat(),
            "reset_at": datetime.now().isoformat()
        }
        self._save_orders()
        logger.warning("Cost tracking has been reset")