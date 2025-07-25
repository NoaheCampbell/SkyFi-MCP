"""Budget management tools for SkyFi with user confirmation."""
import logging
import os
from typing import Dict, Any, List
from mcp.types import Tool, TextContent
from datetime import datetime, timedelta
import json
from pathlib import Path

from .config import SkyFiConfig

logger = logging.getLogger(__name__)

# Store pending budget changes
PENDING_CHANGES: Dict[str, Dict[str, Any]] = {}


async def register_budget_tools() -> List[Tool]:
    """Register budget management tools."""
    return [
        Tool(
            name="skyfi_request_budget_change",
            description="Request a change to the SkyFi spending budget (requires user confirmation)",
            inputSchema={
                "type": "object",
                "properties": {
                    "new_budget": {
                        "type": "number",
                        "description": "New budget amount in USD",
                        "minimum": 0,
                        "maximum": 10000
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for the budget change request"
                    },
                    "budget_type": {
                        "type": "string",
                        "enum": ["cost_limit", "max_order_cost", "daily_limit"],
                        "description": "Which budget limit to modify"
                    }
                },
                "required": ["new_budget", "reason", "budget_type"]
            }
        ),
        Tool(
            name="skyfi_confirm_budget_change",
            description="Confirm a pending budget change with a confirmation code",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirmation_code": {
                        "type": "string",
                        "description": "The confirmation code provided by the request"
                    }
                },
                "required": ["confirmation_code"]
            }
        ),
        Tool(
            name="skyfi_view_current_budget",
            description="View current SkyFi budget limits and spending",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


async def call_budget_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle budget tool calls."""
    if name == "skyfi_request_budget_change":
        return await request_budget_change(arguments)
    elif name == "skyfi_confirm_budget_change":
        return await confirm_budget_change(arguments)
    elif name == "skyfi_view_current_budget":
        return await view_current_budget()
    else:
        return [TextContent(
            type="text",
            text=f"Unknown budget tool: {name}"
        )]


async def request_budget_change(arguments: Dict[str, Any]) -> List[TextContent]:
    """Request a budget change that requires user confirmation."""
    new_budget = arguments["new_budget"]
    reason = arguments["reason"]
    budget_type = arguments["budget_type"]
    
    # Get current config
    config = SkyFiConfig.from_env()
    
    # Get current value
    current_value = getattr(config, budget_type)
    
    # Generate confirmation code
    import random
    import string
    confirmation_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Store pending change
    PENDING_CHANGES[confirmation_code] = {
        "budget_type": budget_type,
        "current_value": current_value,
        "new_value": new_budget,
        "reason": reason,
        "requested_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(minutes=5)
    }
    
    # Create response
    budget_type_display = {
        "cost_limit": "Total Cost Limit",
        "max_order_cost": "Maximum Cost per Order",
        "daily_limit": "Daily Spending Limit"
    }
    
    return [TextContent(
        type="text",
        text=f"""
🔔 **Budget Change Request**

**Type**: {budget_type_display.get(budget_type, budget_type)}
**Current Value**: ${current_value:.2f}
**Requested Value**: ${new_budget:.2f}
**Change**: ${new_budget - current_value:+.2f} ({((new_budget - current_value) / current_value * 100):+.1f}%)
**Reason**: {reason}

⚠️ **User Confirmation Required**

To approve this budget change, the user must confirm by running:
`skyfi_confirm_budget_change` with confirmation code: **{confirmation_code}**

This request will expire in 5 minutes.

**Important**: Increasing budget limits will allow the system to spend more money on satellite imagery. Only approve if you understand the financial implications.
"""
    )]


async def confirm_budget_change(arguments: Dict[str, Any]) -> List[TextContent]:
    """Confirm a pending budget change."""
    confirmation_code = arguments["confirmation_code"]
    
    if confirmation_code not in PENDING_CHANGES:
        return [TextContent(
            type="text",
            text="❌ Invalid confirmation code. No pending budget change found with this code."
        )]
    
    change = PENDING_CHANGES[confirmation_code]
    
    # Check if expired
    if datetime.now() > change["expires_at"]:
        del PENDING_CHANGES[confirmation_code]
        return [TextContent(
            type="text",
            text="❌ This budget change request has expired. Please create a new request."
        )]
    
    # Apply the change
    budget_type = change["budget_type"]
    new_value = change["new_value"]
    
    # Update environment variable
    env_var_map = {
        "cost_limit": "SKYFI_COST_LIMIT",
        "max_order_cost": "SKYFI_MAX_ORDER_COST",
        "daily_limit": "SKYFI_DAILY_LIMIT"
    }
    
    env_var = env_var_map.get(budget_type)
    if env_var:
        os.environ[env_var] = str(new_value)
    
    # Clean up
    del PENDING_CHANGES[confirmation_code]
    
    # Log the change
    logger.warning(f"Budget changed: {budget_type} from ${change['current_value']} to ${new_value}")
    
    return [TextContent(
        type="text",
        text=f"""
✅ **Budget Change Confirmed**

**{budget_type}** has been updated:
- Previous: ${change['current_value']:.2f}
- New: ${new_value:.2f}

The new budget limit is now active. The system will use this limit for all future operations.

**Note**: This change is temporary and will reset when the server restarts. To make it permanent, update your configuration file or environment variables.
"""
    )]


async def view_current_budget() -> List[TextContent]:
    """View current budget configuration and spending."""
    config = SkyFiConfig.from_env()
    
    # Try to get spending info from cost tracker
    spending_info = ""
    try:
        # This would connect to the actual cost tracker if available
        # For now, just show the limits
        pass
    except:
        pass
    
    return [TextContent(
        type="text",
        text=f"""
💰 **Current SkyFi Budget Configuration**

**Spending Limits:**
- Total Cost Limit: ${config.cost_limit:.2f}
- Max Cost per Order: ${config.max_order_cost:.2f}
- Daily Spending Limit: ${config.daily_limit:.2f}

**Safety Features:**
- Force Lowest Cost: {'Yes' if config.force_lowest_cost else 'No'}
- Require Confirmation: {'Yes' if config.require_confirmation else 'No'}
- Require Human Approval: {'Yes' if config.require_human_approval else 'No'}
- Ordering Enabled: {'Yes' if config.enable_ordering else 'No'}

{spending_info}

To request a budget change, use the `skyfi_request_budget_change` tool.
"""
    )]