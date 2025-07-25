"""Account management tools for SkyFi."""
import logging
from typing import Dict, Any, List
from mcp.types import Tool, TextContent
import json

logger = logging.getLogger(__name__)


async def register_account_tools() -> List[Tool]:
    """Register account management tools."""
    return [
        Tool(
            name="skyfi_update_account_budget",
            description="Attempt to update the SkyFi account budget (experimental - may not be supported by API)",
            inputSchema={
                "type": "object",
                "properties": {
                    "budget_amount": {
                        "type": "number",
                        "description": "New budget amount in USD",
                        "minimum": 0,
                        "maximum": 10000
                    }
                },
                "required": ["budget_amount"]
            }
        )
    ]


async def call_account_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle account tool calls."""
    if name == "skyfi_update_account_budget":
        return await update_account_budget(arguments)
    else:
        return [TextContent(
            type="text",
            text=f"Unknown account tool: {name}"
        )]


async def update_account_budget(arguments: Dict[str, Any]) -> List[TextContent]:
    """Attempt to update the SkyFi account budget."""
    budget_amount = arguments["budget_amount"]
    
    from .client import SkyFiClient
    
    try:
        async with SkyFiClient() as client:
            # First, let's try a few potential endpoints
            # These are educated guesses based on common API patterns
            
            attempts = []
            
            # Attempt 1: Try PATCH on user endpoint
            try:
                response = await client.client.patch(
                    "/auth/user",
                    json={"budgetAmount": budget_amount}
                )
                if response.status_code == 200:
                    return [TextContent(
                        type="text",
                        text=f"✅ Successfully updated SkyFi account budget to ${budget_amount:.2f}"
                    )]
                attempts.append(f"PATCH /auth/user: {response.status_code}")
            except Exception as e:
                attempts.append(f"PATCH /auth/user: {str(e)}")
            
            # Attempt 2: Try PUT on user settings
            try:
                response = await client.client.put(
                    "/user/settings",
                    json={"budgetAmount": budget_amount}
                )
                if response.status_code == 200:
                    return [TextContent(
                        type="text",
                        text=f"✅ Successfully updated SkyFi account budget to ${budget_amount:.2f}"
                    )]
                attempts.append(f"PUT /user/settings: {response.status_code}")
            except Exception as e:
                attempts.append(f"PUT /user/settings: {str(e)}")
            
            # Attempt 3: Try POST to a budget endpoint
            try:
                response = await client.client.post(
                    "/user/budget",
                    json={"amount": budget_amount}
                )
                if response.status_code in [200, 201]:
                    return [TextContent(
                        type="text",
                        text=f"✅ Successfully updated SkyFi account budget to ${budget_amount:.2f}"
                    )]
                attempts.append(f"POST /user/budget: {response.status_code}")
            except Exception as e:
                attempts.append(f"POST /user/budget: {str(e)}")
            
            # If we get here, none of the attempts worked
            return [TextContent(
                type="text",
                text=f"""❌ Unable to update SkyFi account budget

The SkyFi API doesn't appear to have a public endpoint for updating account budgets.

**Attempted endpoints:**
{chr(10).join(f"• {attempt}" for attempt in attempts)}

**What you can do instead:**
1. Log into https://app.skyfi.com
2. Go to your account settings
3. Update your budget there
4. Or contact support@skyfi.com to request this feature

**Note**: The MCP server's local budget limits (${client.config.cost_limit:.2f}) are still in effect and will prevent overspending regardless of your account budget.
"""
            )]
            
    except Exception as e:
        logger.error(f"Error in update_account_budget: {e}")
        return [TextContent(
            type="text",
            text=f"❌ Error updating account budget: {str(e)}"
        )]