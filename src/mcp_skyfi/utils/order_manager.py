"""Order management with approval system."""
import json
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

import logging

logger = logging.getLogger(__name__)


class OrderManager:
    """Manages order approvals and confirmations."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize order manager."""
        if data_dir is None:
            data_dir = Path.home() / ".mcp-skyfi"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.pending_orders_file = self.data_dir / "pending_orders.json"
        self.pending_orders = self._load_pending_orders()
    
    def _load_pending_orders(self) -> Dict:
        """Load pending orders from file."""
        if self.pending_orders_file.exists():
            try:
                with open(self.pending_orders_file, 'r') as f:
                    data = json.load(f)
                    # Clean up expired orders
                    self._cleanup_expired_orders(data)
                    return data
            except Exception as e:
                logger.error(f"Failed to load pending orders: {e}")
        
        return {"orders": {}}
    
    def _save_pending_orders(self):
        """Save pending orders to file."""
        try:
            with open(self.pending_orders_file, 'w') as f:
                json.dump(self.pending_orders, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save pending orders: {e}")
    
    def _cleanup_expired_orders(self, data: Dict):
        """Remove expired pending orders."""
        current_time = time.time()
        expired = []
        
        for token, order in data.get("orders", {}).items():
            if current_time > order.get("expires_at", 0):
                expired.append(token)
        
        for token in expired:
            del data["orders"][token]
            logger.info(f"Cleaned up expired order: {token}")
    
    def create_pending_order(
        self, 
        order_details: Dict, 
        estimated_cost: float,
        expiry_minutes: int = 5
    ) -> str:
        """Create a pending order that requires confirmation."""
        # Generate secure token
        token = secrets.token_urlsafe(16)
        
        # Create pending order
        pending_order = {
            "token": token,
            "details": order_details,
            "estimated_cost": estimated_cost,
            "created_at": datetime.now().isoformat(),
            "expires_at": time.time() + (expiry_minutes * 60),
            "status": "pending_confirmation"
        }
        
        self.pending_orders["orders"][token] = pending_order
        self._save_pending_orders()
        
        logger.info(f"Created pending order {token} for ${estimated_cost:.2f}")
        return token
    
    def get_pending_order(self, token: str) -> Optional[Dict]:
        """Get a pending order by token."""
        self._cleanup_expired_orders(self.pending_orders)
        return self.pending_orders["orders"].get(token)
    
    def confirm_order(self, token: str, confirmation_code: str) -> Tuple[bool, str]:
        """Confirm a pending order with the confirmation code."""
        order = self.get_pending_order(token)
        
        if not order:
            return False, "Order not found or expired"
        
        # For now, simple confirmation - could be enhanced
        expected_code = f"CONFIRM-{token[:6]}"
        
        if confirmation_code != expected_code:
            return False, "Invalid confirmation code"
        
        # Mark as confirmed
        order["status"] = "confirmed"
        order["confirmed_at"] = datetime.now().isoformat()
        self._save_pending_orders()
        
        return True, "Order confirmed"
    
    def cancel_order(self, token: str) -> bool:
        """Cancel a pending order."""
        if token in self.pending_orders["orders"]:
            del self.pending_orders["orders"][token]
            self._save_pending_orders()
            logger.info(f"Cancelled order {token}")
            return True
        return False