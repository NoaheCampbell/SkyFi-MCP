"""Tool to compare local MCP budget vs SkyFi account budget."""
import logging
from typing import Dict, Any, List
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


async def register_budget_comparison_tool() -> List[Tool]:
    """Register budget comparison tool."""
    return [
        Tool(
            name="skyfi_compare_budgets",
            description="Compare local MCP budget limits with actual SkyFi account budget",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


async def compare_budgets() -> List[TextContent]:
    """Compare local and account budgets."""
    from .client import SkyFiClient
    from .config import SkyFiConfig
    
    config = SkyFiConfig.from_env()
    
    try:
        async with SkyFiClient() as client:
            # Get user info with account budget
            user_info = await client.get_user()
            account_budget = user_info.get("budgetAmount", 0)
            current_usage = user_info.get("currentBudgetUsage", 0)
            
            # Create comparison report
            report = "📊 **Budget Comparison Report**\n"
            report += "=" * 50 + "\n\n"
            
            report += "**🏦 SkyFi Account Budget** (actual account limits):\n"
            report += f"  • Budget Amount: ${account_budget:.2f}\n"
            report += f"  • Current Usage: ${current_usage:.2f}\n"
            report += f"  • Remaining: ${account_budget - current_usage:.2f}\n\n"
            
            report += "**🛡️ Local MCP Limits** (safety guardrails):\n"
            report += f"  • Total Cost Limit: ${config.cost_limit:.2f}\n"
            report += f"  • Max Per Order: ${config.max_order_cost:.2f}\n"
            report += f"  • Daily Limit: ${config.daily_limit:.2f}\n\n"
            
            # Determine effective limits
            report += "**✅ Effective Limits** (most restrictive):\n"
            effective_total = min(config.cost_limit, account_budget) if account_budget > 0 else config.cost_limit
            report += f"  • Total Budget: ${effective_total:.2f}\n"
            
            if account_budget == 0:
                report += "\n⚠️ **Warning**: Your SkyFi account budget is $0.00\n"
                report += "   This means you cannot place any orders through SkyFi.\n"
                report += "   To fix this:\n"
                report += "   1. Try: skyfi_update_account_budget (experimental)\n"
                report += "   2. Or visit: https://app.skyfi.com to set your budget\n"
            elif account_budget < config.cost_limit:
                report += "\n💡 **Note**: Your SkyFi account budget is lower than local limits.\n"
                report += "   The account budget will be the effective limit.\n"
            else:
                report += "\n💡 **Note**: Your local MCP limits are more restrictive.\n"
                report += "   This provides extra safety against overspending.\n"
            
            return [TextContent(type="text", text=report)]
            
    except Exception as e:
        logger.error(f"Error comparing budgets: {e}")
        return [TextContent(
            type="text",
            text=f"❌ Error comparing budgets: {str(e)}"
        )]