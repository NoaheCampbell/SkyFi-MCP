"""Configuration for SkyFi service."""
import os
from typing import Optional

from pydantic import BaseModel, Field
from ..auth import auth_manager


class SkyFiConfig(BaseModel):
    """Configuration for SkyFi API."""
    
    api_key: str = Field(..., description="SkyFi API key")
    api_url: str = Field(
        default="https://app.skyfi.com/platform-api",
        description="SkyFi API base URL"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    cost_limit: float = Field(default=40.0, description="Maximum cost limit per order in USD")
    force_lowest_cost: bool = Field(
        default=True,
        description="Always select lowest cost options (lowest quality, smallest area)"
    )
    enable_ordering: bool = Field(
        default=False,
        description="Enable satellite image ordering (DANGEROUS - costs real money!)"
    )
    require_confirmation: bool = Field(
        default=True,
        description="Require explicit confirmation for all orders"
    )
    max_order_cost: float = Field(
        default=20.0,
        description="Maximum cost per single order"
    )
    daily_limit: float = Field(
        default=40.0,
        description="Maximum spending per day"
    )
    require_human_approval: bool = Field(
        default=True,
        description="Require human approval via confirmation code"
    )
    
    @classmethod
    def from_env(cls, require_api_key: bool = True) -> "SkyFiConfig":
        """Create configuration from environment variables."""
        # Try auth manager first
        api_key = auth_manager.get_api_key()
        
        # Fall back to environment variable
        if not api_key:
            api_key = os.getenv("SKYFI_API_KEY", "")
        
        if require_api_key and not api_key:
            # Don't raise immediately - allow runtime configuration
            api_key = "PENDING_RUNTIME_CONFIG"
        
        return cls(
            api_key=api_key,
            api_url=os.getenv("SKYFI_API_URL", cls.model_fields["api_url"].default),
            timeout=int(os.getenv("SKYFI_TIMEOUT", "30")),
            cost_limit=float(os.getenv("SKYFI_COST_LIMIT", "40.0")),
            force_lowest_cost=os.getenv("SKYFI_FORCE_LOWEST_COST", "true").lower() == "true",
            enable_ordering=os.getenv("SKYFI_ENABLE_ORDERING", "false").lower() == "true",
            require_confirmation=os.getenv("SKYFI_REQUIRE_CONFIRMATION", "true").lower() == "true",
            max_order_cost=float(os.getenv("SKYFI_MAX_ORDER_COST", "20.0")),
            daily_limit=float(os.getenv("SKYFI_DAILY_LIMIT", "40.0")),
            require_human_approval=os.getenv("SKYFI_REQUIRE_HUMAN_APPROVAL", "true").lower() == "true"
        )