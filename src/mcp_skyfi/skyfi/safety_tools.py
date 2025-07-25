"""MCP Safety Guardrail tools - NOT account budget management."""
import logging
import os
from typing import Dict, Any, List
from mcp.types import Tool, TextContent
from datetime import datetime, timedelta
import json

from .config import SkyFiConfig

logger = logging.getLogger(__name__)

# Store pending safety limit changes
PENDING_SAFETY_CHANGES: Dict[str, Dict[str, Any]] = {}


async def register_safety_tools() -> List[Tool]:
    """Register MCP safety guardrail tools."""
    return [
        Tool(
            name="skyfi_modify_safety_limits",
            description="Modify MCP safety guardrails that prevent overspending (NOT your SkyFi account budget)",
            inputSchema={
                "type": "object",
                "properties": {
                    "new_limit": {
                        "type": "number",
                        "description": "New safety limit in USD",
                        "minimum": 0,
                        "maximum": 10000
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for changing the safety limit"
                    },
                    "limit_type": {
                        "type": "string",
                        "enum": ["total_safety_limit", "per_order_safety_limit", "daily_safety_limit"],
                        "description": "Which MCP safety limit to modify"
                    }
                },
                "required": ["new_limit", "reason", "limit_type"]
            }
        ),
        Tool(
            name="skyfi_confirm_safety_change",
            description="Confirm a pending MCP safety limit change",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirmation_code": {
                        "type": "string",
                        "description": "The confirmation code provided"
                    }
                },
                "required": ["confirmation_code"]
            }
        ),
        Tool(
            name="skyfi_view_safety_status",
            description="View MCP safety guardrails and how they compare to your SkyFi account",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


async def call_safety_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle safety tool calls."""
    if name == "skyfi_modify_safety_limits":
        return await modify_safety_limits(arguments)
    elif name == "skyfi_confirm_safety_change":
        return await confirm_safety_change(arguments)
    elif name == "skyfi_view_safety_status":
        return await view_safety_status()
    else:
        return [TextContent(
            type="text",
            text=f"Unknown safety tool: {name}"
        )]


async def modify_safety_limits(arguments: Dict[str, Any]) -> List[TextContent]:
    """Request a change to MCP safety limits."""
    new_limit = arguments["new_limit"]
    reason = arguments["reason"]
    limit_type = arguments["limit_type"]
    
    # Get current config
    config = SkyFiConfig.from_env()
    
    # Map friendly names to config fields
    limit_map = {
        "total_safety_limit": "cost_limit",
        "per_order_safety_limit": "max_order_cost",
        "daily_safety_limit": "daily_limit"
    }
    
    config_field = limit_map[limit_type]
    current_value = getattr(config, config_field)
    
    # Generate confirmation code
    import random
    import string
    confirmation_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Store pending change
    PENDING_SAFETY_CHANGES[confirmation_code] = {
        "limit_type": limit_type,
        "config_field": config_field,
        "current_value": current_value,
        "new_value": new_limit,
        "reason": reason,
        "requested_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(minutes=5)
    }
    
    # Create response
    limit_display = {
        "total_safety_limit": "Total Safety Limit (MCP will block orders exceeding this)",
        "per_order_safety_limit": "Per-Order Safety Limit (MCP blocks single orders over this)",
        "daily_safety_limit": "Daily Safety Limit (MCP blocks if daily total exceeds this)"
    }
    
    return [TextContent(
        type="text",
        text=f"""
🛡️ **MCP Safety Limit Change Request**

**What this changes**: {limit_display[limit_type]}
**Current Limit**: ${current_value:.2f}
**Requested Limit**: ${new_limit:.2f}
**Change**: ${new_limit - current_value:+.2f} ({((new_limit - current_value) / current_value * 100):+.1f}%)
**Reason**: {reason}

⚠️ **IMPORTANT**: This only changes the MCP server's safety limits, NOT your SkyFi account budget!

**What this means**:
- If increased: The MCP will allow larger orders (up to the new limit)
- If decreased: The MCP will be more restrictive
- Your SkyFi account budget remains unchanged

To approve this change, use: `skyfi_confirm_safety_change` with code: **{confirmation_code}**

This request expires in 5 minutes.
"""
    )]


async def confirm_safety_change(arguments: Dict[str, Any]) -> List[TextContent]:
    """Confirm a pending safety limit change."""
    confirmation_code = arguments["confirmation_code"]
    
    if confirmation_code not in PENDING_SAFETY_CHANGES:
        return [TextContent(
            type="text",
            text="❌ Invalid confirmation code. No pending safety changes found."
        )]
    
    change = PENDING_SAFETY_CHANGES[confirmation_code]
    
    # Check if expired
    if datetime.now() > change["expires_at"]:
        del PENDING_SAFETY_CHANGES[confirmation_code]
        return [TextContent(
            type="text",
            text="❌ This safety change request has expired. Please create a new request."
        )]
    
    # Apply the change
    config_field = change["config_field"]
    new_value = change["new_value"]
    
    # Update environment variable
    env_var_map = {
        "cost_limit": "SKYFI_COST_LIMIT",
        "max_order_cost": "SKYFI_MAX_ORDER_COST",
        "daily_limit": "SKYFI_DAILY_LIMIT"
    }
    
    env_var = env_var_map.get(config_field)
    if env_var:
        os.environ[env_var] = str(new_value)
    
    # Clean up
    del PENDING_SAFETY_CHANGES[confirmation_code]
    
    # Log the change
    logger.warning(f"MCP safety limit changed: {config_field} from ${change['current_value']} to ${new_value}")
    
    return [TextContent(
        type="text",
        text=f"""
✅ **MCP Safety Limit Updated**

**{change['limit_type']}** has been changed:
- Previous: ${change['current_value']:.2f}
- New: ${new_value:.2f}

The MCP server will now use this limit to prevent overspending.

**Remember**: This does NOT change your SkyFi account budget!
To update your actual SkyFi account budget, visit https://app.skyfi.com
"""
    )]


async def view_safety_status() -> List[TextContent]:
    """View comprehensive safety status."""
    config = SkyFiConfig.from_env()
    
    # Try to get account info
    account_info = "Unable to fetch (API key may be missing)"
    account_budget = 0
    current_usage = 0
    
    try:
        from .client import SkyFiClient
        async with SkyFiClient() as client:
            user_info = await client.get_user()
            account_budget = user_info.get("budgetAmount", 0)
            current_usage = user_info.get("currentBudgetUsage", 0)
            account_info = f"${account_budget:.2f} (${current_usage:.2f} used)"
    except:
        pass
    
    return [TextContent(
        type="text",
        text=f"""
🛡️ **MCP Safety Status Report**

**Purpose**: These are LOCAL safety limits that prevent the MCP from overspending.
They work INDEPENDENTLY from your SkyFi account budget.

**Current MCP Safety Limits:**
- 🚫 Total Safety Limit: ${config.cost_limit:.2f}
  (MCP will reject ANY order that would push total spending over this)
  
- 📦 Per-Order Safety Limit: ${config.max_order_cost:.2f}
  (MCP will reject any SINGLE order over this amount)
  
- 📅 Daily Safety Limit: ${config.daily_limit:.2f}
  (MCP will reject orders if today's total would exceed this)

**Current Safety Features:**
- Force Lowest Cost: {'✅ Yes' if config.force_lowest_cost else '❌ No'}
  (Always selects cheapest options when searching)
  
- Require Confirmation: {'✅ Yes' if config.require_confirmation else '❌ No'}
  (Requires explicit confirmation before ordering)
  
- Require Human Approval: {'✅ Yes' if config.require_human_approval else '❌ No'}
  (Requires confirmation code for all orders)
  
- Ordering Enabled: {'✅ Yes' if config.enable_ordering else '❌ No'}
  (Master switch - if No, ALL ordering is blocked)

**Your SkyFi Account Status:**
Account Budget: {account_info}

**How They Work Together:**
1. MCP checks its safety limits FIRST
2. If MCP approves, the order goes to SkyFi
3. SkyFi then checks against your account budget
4. Both must approve for an order to succeed

To modify MCP safety limits, use: `skyfi_modify_safety_limits`
To update your SkyFi account budget, visit: https://app.skyfi.com
"""
    )]