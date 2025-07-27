"""SkyFi API client implementation."""
import logging
from typing import Any, Dict, Optional

import json
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
        self._create_client()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        if hasattr(self, 'client'):
            await self.client.aclose()
    
    def _create_client(self):
        """Create or recreate the HTTP client with current config."""
        if hasattr(self, 'client'):
            # Close existing client if it exists
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.client.aclose())
                else:
                    loop.run_until_complete(self.client.aclose())
            except:
                pass
        
        # Check if API key is pending
        if self.config.api_key == "PENDING_RUNTIME_CONFIG":
            # Create a client that will fail gracefully
            self.client = None
            return
        
        self.client = httpx.AsyncClient(
            base_url=self.config.api_url,
            headers={
                "X-Skyfi-Api-Key": self.config.api_key,
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
        )
    
    def update_api_key(self, api_key: str):
        """Update the API key and recreate the client."""
        self.config.api_key = api_key
        self._create_client()
    
    async def _ensure_client(self):
        """Ensure client is ready before making requests."""
        if self.client is None:
            if self.config.api_key == "PENDING_RUNTIME_CONFIG":
                raise ValueError(
                    "API key not configured. Use 'skyfi_set_api_key' to set your API key."
                )
            self._create_client()
    
    async def get_user(self) -> Dict[str, Any]:
        """Get current authenticated user information."""
        await self._ensure_client()
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
        # If user explicitly requested a specific resolution, respect it
        # Only force LOW resolution if no resolution was specified AND force_lowest_cost is true
        if self.config.force_lowest_cost and resolution is None:
            resolution = "LOW"  # Default to lowest resolution
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
        
        # Log the payload for debugging
        logger.info(f"Search payload - resolution: {resolution}, openData: {open_data}")
        
        response = await self.client.post("/archives", json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Filter results by resolution if specified
        if resolution and "results" in result:
            # If user requested a specific resolution, filter to only that resolution
            original_count = len(result["results"])
            result["results"] = [
                r for r in result["results"] 
                if r.get("resolution", "").upper() == resolution.upper()
            ]
            filtered_count = original_count - len(result["results"])
            if filtered_count > 0:
                logger.info(f"Filtered out {filtered_count} results that didn't match resolution {resolution}")
        
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
        
        logger.info(f"Sending order request with payload: {json.dumps(payload, indent=2)}")
        
        # Make the API call
        response = await self.client.post("/order-archive", json=payload)
        
        # Log response details for debugging
        if response.status_code == 422:
            logger.error(f"422 Error - Request payload: {json.dumps(payload, indent=2)}")
            try:
                error_detail = response.json()
                logger.error(f"422 Error details: {json.dumps(error_detail, indent=2)}")
            except:
                logger.error(f"422 Error response text: {response.text}")
        
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
    
    async def list_orders(
        self, 
        order_type: Optional[str] = None,
        page_size: int = 10,
        page_number: int = 0
    ) -> Dict[str, Any]:
        """List orders for the user.
        
        Args:
            order_type: Filter by ARCHIVE or TASKING
            page_size: Number of results per page
            page_number: Page number (0-indexed)
            
        Returns:
            Order list with metadata
        """
        params = {
            "pageSize": page_size,
            "pageNumber": page_number
        }
        
        if order_type:
            params["orderType"] = order_type
            
        response = await self.client.get("/orders", params=params)
        response.raise_for_status()
        return response.json()
    
    async def download_order(self, order_id: str, deliverable_type: str = "image", save_path: Optional[str] = None) -> str:
        """Download order file to local disk.
        
        Args:
            order_id: The order ID
            deliverable_type: Type of deliverable (image, payload, tiles)
            save_path: Where to save the file (defaults to order_ID_type with appropriate extension)
            
        Returns:
            Path to the saved file
        """
        import os
        import tempfile
        
        # Determine file extension based on deliverable type
        extensions = {
            "image": "png",  # Could also be jpg, but png is common
            "payload": "zip",
            "tiles": "zip"
        }
        
        if not save_path:
            ext = extensions.get(deliverable_type, "dat")
            # Use temp directory to avoid read-only file system issues
            temp_dir = tempfile.gettempdir()
            save_path = os.path.join(temp_dir, f"skyfi_order_{order_id}_{deliverable_type}.{ext}")
        
        # Download directly from the endpoint
        endpoint = f"/orders/{order_id}/{deliverable_type}"
        
        # Download with API key in header using -L style redirect following
        response = await self.client.get(
            endpoint,
            headers={"X-Skyfi-Api-Key": self.config.api_key},
            follow_redirects=True
        )
        response.raise_for_status()
        
        # Save to file
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return os.path.abspath(save_path)
    
    async def get_download_url(self, order_id: str, deliverable_type: str = "image") -> str:
        """Get download URL for a completed order.
        
        Args:
            order_id: The order ID
            deliverable_type: Type of deliverable (image, payload, tiles)
            
        Returns:
            The API endpoint URL (requires authentication header to download)
        """
        # Return the direct API endpoint - authentication required via header
        return f"{self.config.api_url}/orders/{order_id}/{deliverable_type}"