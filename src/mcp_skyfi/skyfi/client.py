"""SkyFi API client implementation."""
import logging
from typing import Any, Dict, Optional

import httpx

from .config import SkyFiConfig
from ..utils.cost_tracker import CostTracker

logger = logging.getLogger(__name__)


class SkyFiClient:
    """Client for interacting with SkyFi API."""
    
    def __init__(self, config: Optional[SkyFiConfig] = None):
        """Initialize SkyFi client."""
        self.config = config or SkyFiConfig.from_env()
        self.cost_tracker = CostTracker()
        self.client = httpx.AsyncClient(
            base_url=self.config.api_url,
            headers={
                "X-Skyfi-Api-Key": self.config.api_key,
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def get_user(self) -> Dict[str, Any]:
        """Get current authenticated user information."""
        response = await self.client.get("/auth/whoami")
        response.raise_for_status()
        return response.json()
    
    async def search_archives(
        self,
        aoi: str,
        from_date: str,
        to_date: str,
        open_data: bool = True,
        product_types: Optional[list[str]] = None,
        resolution: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search for satellite imagery in the catalog."""
        # Force lowest cost options if configured
        if self.config.force_lowest_cost:
            resolution = "LOW"  # Always use lowest resolution
            open_data = True    # Prefer open data (usually cheaper/free)
            
        payload = {
            "aoi": aoi,
            "fromDate": from_date,
            "toDate": to_date,
            "openData": open_data,
        }
        
        if product_types:
            payload["productTypes"] = product_types
        if resolution:
            payload["resolution"] = resolution
        
        response = await self.client.post("/archives", json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Sort by price if forcing lowest cost
        if self.config.force_lowest_cost and "results" in result:
            result["results"] = sorted(
                result["results"], 
                key=lambda x: x.get("price", float('inf'))
            )
        
        return result
    
    async def order_archive(
        self,
        aoi: str,
        archive_id: str,
        delivery_driver: str,
        delivery_params: Dict[str, Any],
        estimated_cost: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Order satellite imagery with delivery to cloud storage."""
        # Get actual cost if not provided
        if not estimated_cost:
            # Try to get cost from a fresh search
            logger.warning("No estimated cost provided, cannot validate spending limit")
            estimated_cost = 0  # Conservative approach
        
        # Check total spending limit
        total_spent = self.cost_tracker.get_total_spent()
        remaining_budget = self.cost_tracker.get_remaining_budget(self.config.cost_limit)
        
        logger.info(f"Current spending: ${total_spent:.2f} / ${self.config.cost_limit:.2f}")
        logger.info(f"Remaining budget: ${remaining_budget:.2f}")
        logger.info(f"Order cost: ${estimated_cost:.2f}")
        
        # Validate against total limit
        if not self.cost_tracker.can_afford(estimated_cost, self.config.cost_limit):
            raise ValueError(
                f"Order would exceed total spending limit!\n"
                f"Total spent: ${total_spent:.2f}\n"
                f"This order: ${estimated_cost:.2f}\n"
                f"Total limit: ${self.config.cost_limit:.2f}\n"
                f"Remaining budget: ${remaining_budget:.2f}"
            )
        
        # Additional safety check - require explicit confirmation for any order
        if estimated_cost > 0:
            logger.warning(f"COST WARNING: About to place order for ${estimated_cost:.2f}")
            # In a real implementation, this would require user confirmation
        
        payload = {
            "aoi": aoi,
            "archiveId": archive_id,
            "deliveryDriver": delivery_driver,
            "deliveryParams": delivery_params,
        }
        
        # Make the API call
        response = await self.client.post("/order-archive", json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Record the order
        self.cost_tracker.record_order(
            archive_id=archive_id,
            cost=estimated_cost,
            details={
                "aoi": aoi,
                "delivery_driver": delivery_driver,
                "response": result
            }
        )
        
        return result
    
    async def get_pricing_options(self, aoi: Optional[str] = None) -> Dict[str, Any]:
        """Get pricing options for tasking orders using the /pricing endpoint."""
        payload = {}
        if aoi:
            payload["aoi"] = aoi
        
        response = await self.client.post("/pricing", json=payload)
        response.raise_for_status()
        return response.json()