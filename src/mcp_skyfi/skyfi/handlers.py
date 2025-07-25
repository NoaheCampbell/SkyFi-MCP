"""Handlers for SkyFi tool calls."""
import json
import logging
from typing import Any, Dict, List

from mcp.types import TextContent

from .client import SkyFiClient
from ..utils.order_manager import OrderManager

logger = logging.getLogger(__name__)


async def handle_skyfi_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle SkyFi tool calls."""
    try:
        async with SkyFiClient() as client:
            if name == "skyfi_get_user":
                result = await client.get_user()
                return [TextContent(
                    type="text",
                    text=f"User Information:\n{json.dumps(result, indent=2)}"
                )]
            
            elif name == "skyfi_search_archives":
                result = await client.search_archives(
                    aoi=arguments["aoi"],
                    from_date=arguments["fromDate"],
                    to_date=arguments["toDate"],
                    open_data=arguments.get("openData", True),
                    product_types=arguments.get("productTypes"),
                    resolution=arguments.get("resolution"),
                )
                
                # Format results for readability
                if "results" in result:
                    text = f"Found {len(result['results'])} satellite images:\n\n"
                    for idx, img in enumerate(result['results'][:10], 1):  # Show first 10
                        text += f"{idx}. Archive ID: {img.get('archiveId', 'N/A')}\n"
                        text += f"   Date: {img.get('captureDate', 'N/A')}\n"
                        text += f"   Satellite: {img.get('satellite', 'N/A')}\n"
                        text += f"   Resolution: {img.get('resolution', 'N/A')}m\n"
                        text += f"   Cloud Cover: {img.get('cloudCover', 'N/A')}%\n"
                        text += f"   Price: ${img.get('price', 'N/A')}\n\n"
                    
                    if len(result['results']) > 10:
                        text += f"... and {len(result['results']) - 10} more results"
                else:
                    text = json.dumps(result, indent=2)
                
                return [TextContent(type="text", text=text)]
            
            elif name == "skyfi_order_archive":
                # Check if ordering is enabled
                if not client.config.enable_ordering:
                    return [TextContent(
                        type="text",
                        text=(
                            "❌ Ordering is disabled for safety!\n\n"
                            "Satellite image ordering costs real money and is disabled by default.\n"
                            "To enable ordering, set SKYFI_ENABLE_ORDERING=true in your environment.\n\n"
                            "Current safety settings:\n"
                            f"- Cost limit: ${client.config.cost_limit:.2f}\n"
                            f"- Force lowest cost: {client.config.force_lowest_cost}\n"
                            f"- Total spent so far: ${client.cost_tracker.get_total_spent():.2f}\n\n"
                            "⚠️  WARNING: Only enable ordering if you understand the costs!"
                        )
                    )]
                
                # First, try to find the image cost from previous search
                archive_id = arguments["archiveId"]
                estimated_cost = arguments.get("estimated_cost")
                
                # Add warning about cost controls
                warning = ""
                if client.config.force_lowest_cost:
                    warning = "\n⚠️  Cost controls active: Using lowest quality settings\n"
                
                if estimated_cost:
                    warning += f"\n💰 Estimated cost: ${estimated_cost:.2f}"
                    warning += f"\n💰 Cost limit: ${client.config.cost_limit:.2f}\n"
                    warning += f"\n💰 Total spent: ${client.cost_tracker.get_total_spent():.2f}"
                    warning += f"\n💰 Remaining budget: ${client.cost_tracker.get_remaining_budget(client.config.cost_limit):.2f}\n"
                
                try:
                    result = await client.order_archive(
                        aoi=arguments["aoi"],
                        archive_id=archive_id,
                        delivery_driver=arguments["deliveryDriver"],
                        delivery_params=arguments["deliveryParams"],
                        estimated_cost=estimated_cost,
                    )
                    return [TextContent(
                        type="text",
                        text=f"{warning}\nOrder placed successfully:\n{json.dumps(result, indent=2)}"
                    )]
                except ValueError as e:
                    # Cost limit exceeded
                    return [TextContent(
                        type="text",
                        text=f"❌ Order blocked: {str(e)}"
                    )]
            
            elif name == "skyfi_get_pricing":
                # Get pricing options for tasking
                aoi = arguments.get("aoi")
                show_all = arguments.get("show_all", True)  # Default to showing all prices
                
                try:
                    result = await client.get_pricing_options(aoi)
                    
                    # Parse the pricing response
                    price_info = "💰 SkyFi Satellite Tasking Price List\n"
                    price_info += f"{'=' * 40}\n\n"
                    
                    if aoi:
                        price_info += f"📍 Pricing for specific area\n\n"
                    else:
                        price_info += "📋 General pricing catalog\n\n"
                    
                    # Show budget status
                    total_spent = client.cost_tracker.get_total_spent()
                    remaining = client.cost_tracker.get_remaining_budget(client.config.cost_limit)
                    
                    price_info += "📊 Budget Reference:\n"
                    price_info += f"- Current spending: ${total_spent:.2f}\n"
                    price_info += f"- Budget remaining: ${remaining:.2f}\n"
                    price_info += f"- Budget limit: ${client.config.cost_limit:.2f}\n\n"
                    
                    # Format the pricing data - show ALL options
                    price_info += "🛰️ ALL AVAILABLE PRICING OPTIONS:\n"
                    price_info += "(Showing all prices regardless of budget)\n\n"
                    
                    # First, let's see the raw structure to handle it properly
                    if isinstance(result, dict):
                        # Count total options
                        total_options = 0
                        
                        # Try different possible response structures
                        if "providers" in result:
                            # Structure: {"providers": {...}}
                            providers_data = result["providers"]
                        elif "pricing" in result:
                            # Structure: {"pricing": {...}}
                            providers_data = result["pricing"]
                        else:
                            # Direct provider data
                            providers_data = result
                        
                        # Format each provider's options
                        for key, value in providers_data.items():
                            if isinstance(value, dict):
                                price_info += f"\n📸 Provider: {key.upper()}\n"
                                price_info += "-" * 30 + "\n"
                                
                                # Handle nested options
                                for option_name, option_data in value.items():
                                    if isinstance(option_data, dict):
                                        # Extract price
                                        price = None
                                        if "price" in option_data:
                                            price = option_data["price"]
                                        elif "cost" in option_data:
                                            price = option_data["cost"]
                                        elif "amount" in option_data:
                                            price = option_data["amount"]
                                        
                                        if price is not None:
                                            total_options += 1
                                            price_float = float(price)
                                            price_info += f"  • {option_name}: ${price_float:,.2f}"
                                            
                                            # Add indicators
                                            if price_float == 0:
                                                price_info += " 🆓 (FREE)"
                                            elif price_float <= remaining:
                                                price_info += " ✅ (within budget)"
                                            else:
                                                price_info += " ❌ (exceeds budget)"
                                            
                                            if price_float > 100:
                                                price_info += " 💸 (premium)"
                                            
                                            # Add other details if available
                                            if "resolution" in option_data:
                                                price_info += f" - {option_data['resolution']}"
                                            if "delivery_time" in option_data:
                                                price_info += f" - {option_data['delivery_time']}"
                                            
                                            price_info += "\n"
                                    elif isinstance(option_data, (int, float)):
                                        # Direct price value
                                        total_options += 1
                                        price_float = float(option_data)
                                        price_info += f"  • {option_name}: ${price_float:,.2f}"
                                        
                                        if price_float == 0:
                                            price_info += " 🆓 (FREE)"
                                        elif price_float <= remaining:
                                            price_info += " ✅"
                                        else:
                                            price_info += " ❌"
                                        
                                        price_info += "\n"
                        
                        if total_options == 0:
                            # If we couldn't parse it, show raw data
                            price_info += "\nRaw pricing data (unable to parse standard format):\n"
                            price_info += json.dumps(result, indent=2)[:2000]  # Limit output
                            if len(json.dumps(result)) > 2000:
                                price_info += "\n... (truncated)"
                        else:
                            price_info += f"\n📊 Total options available: {total_options}"
                    else:
                        # Non-dict response
                        price_info += "Unexpected response format:\n"
                        price_info += str(result)[:1000]
                    
                    price_info += "\n\n⚠️ IMPORTANT REMINDERS:\n"
                    price_info += "• These are viewing prices only - NO orders can be placed\n"
                    price_info += "• Ordering capability has been completely REMOVED for safety\n"
                    price_info += "• Prices shown are for reference only\n"
                    
                    return [TextContent(type="text", text=price_info)]
                    
                except Exception as e:
                    logger.error(f"Error getting pricing: {e}")
                    return [TextContent(
                        type="text",
                        text=f"Error getting pricing: {str(e)}\n\nTry without an AOI for general pricing."
                    )]
            
            elif name == "skyfi_prepare_order":
                # Check if ordering is enabled at all
                if not client.config.enable_ordering:
                    return [TextContent(
                        type="text",
                        text=(
                            "❌ Ordering is disabled!\n\n"
                            "To enable ordering with guardrails:\n"
                            "1. Set SKYFI_ENABLE_ORDERING=true\n"
                            "2. Keep SKYFI_REQUIRE_CONFIRMATION=true (default)\n"
                            "3. Keep SKYFI_REQUIRE_HUMAN_APPROVAL=true (default)\n\n"
                            "This will enable ordering with multiple safety checks."
                        )
                    )]
                
                aoi = arguments["aoi"]
                archive_id = arguments["archiveId"]
                estimated_cost = float(arguments["estimated_cost"])
                
                # Create order manager
                order_manager = OrderManager()
                
                # Perform all safety checks
                checks_passed = True
                warnings = []
                
                # Check 1: Single order cost limit
                if estimated_cost > client.config.max_order_cost:
                    checks_passed = False
                    warnings.append(
                        f"❌ Order exceeds max single order limit "
                        f"(${estimated_cost:.2f} > ${client.config.max_order_cost:.2f})"
                    )
                
                # Check 2: Daily spending limit
                total_spent = client.cost_tracker.get_total_spent()
                if total_spent + estimated_cost > client.config.daily_limit:
                    checks_passed = False
                    warnings.append(
                        f"❌ Order would exceed daily limit "
                        f"(${total_spent:.2f} + ${estimated_cost:.2f} > ${client.config.daily_limit:.2f})"
                    )
                
                # Check 3: Total budget limit
                if total_spent + estimated_cost > client.config.cost_limit:
                    checks_passed = False
                    warnings.append(
                        f"❌ Order would exceed total budget "
                        f"(${total_spent:.2f} + ${estimated_cost:.2f} > ${client.config.cost_limit:.2f})"
                    )
                
                if not checks_passed:
                    return [TextContent(
                        type="text",
                        text=(
                            "🚫 Order Cannot Proceed - Failed Safety Checks:\n\n" +
                            "\n".join(warnings) +
                            "\n\nPlease select a cheaper option or increase limits."
                        )
                    )]
                
                # Create pending order
                order_details = {
                    "aoi": aoi,
                    "archiveId": archive_id,
                    "deliveryDriver": "S3",  # Default, could be parameterized
                    "deliveryParams": {}  # Would need to be filled in
                }
                
                token = order_manager.create_pending_order(
                    order_details=order_details,
                    estimated_cost=estimated_cost,
                    expiry_minutes=5
                )
                
                confirmation_code = f"CONFIRM-{token[:6]}"
                
                response = f"📋 Order Preview\n"
                response += f"{'=' * 40}\n\n"
                response += f"Archive ID: {archive_id}\n"
                response += f"Estimated Cost: ${estimated_cost:.2f}\n"
                response += f"Budget Status:\n"
                response += f"  - Current spending: ${total_spent:.2f}\n"
                response += f"  - After this order: ${total_spent + estimated_cost:.2f}\n"
                response += f"  - Daily limit: ${client.config.daily_limit:.2f}\n\n"
                
                if client.config.require_human_approval:
                    response += "⚠️  HUMAN APPROVAL REQUIRED\n\n"
                    response += "To complete this order:\n"
                    response += f"1. Review the order details above\n"
                    response += f"2. Copy this token: {token}\n"
                    response += f"3. Copy this code: {confirmation_code}\n"
                    response += f"4. Use skyfi_confirm_order with both values\n\n"
                    response += "⏱️  This order expires in 5 minutes\n"
                    response += "❗ Only confirm if you want to spend real money!"
                else:
                    response += "Order created and ready for confirmation.\n"
                
                return [TextContent(type="text", text=response)]
            
            elif name == "skyfi_confirm_order":
                # Validate ordering is enabled
                if not client.config.enable_ordering:
                    return [TextContent(
                        type="text",
                        text="❌ Ordering is disabled. Cannot confirm orders."
                    )]
                
                token = arguments["token"]
                confirmation_code = arguments["confirmation_code"]
                
                # Create order manager
                order_manager = OrderManager()
                
                # Validate the order
                order = order_manager.get_pending_order(token)
                if not order:
                    return [TextContent(
                        type="text",
                        text="❌ Order not found or expired. Orders expire after 5 minutes."
                    )]
                
                # Confirm the order
                success, message = order_manager.confirm_order(token, confirmation_code)
                
                if not success:
                    return [TextContent(
                        type="text",
                        text=f"❌ {message}"
                    )]
                
                # If confirmed, proceed with the actual order
                try:
                    result = await client.order_archive(
                        aoi=order["details"]["aoi"],
                        archive_id=order["details"]["archiveId"],
                        delivery_driver=order["details"]["deliveryDriver"],
                        delivery_params=order["details"]["deliveryParams"],
                        estimated_cost=order["estimated_cost"]
                    )
                    
                    return [TextContent(
                        type="text",
                        text=(
                            f"✅ Order Placed Successfully!\n\n"
                            f"Cost: ${order['estimated_cost']:.2f}\n"
                            f"Order details:\n{json.dumps(result, indent=2)}"
                        )
                    )]
                except Exception as e:
                    return [TextContent(
                        type="text",
                        text=f"❌ Order failed: {str(e)}"
                    )]
            
            elif name.startswith("skyfi_request_budget_") or name.startswith("skyfi_confirm_budget_") or name == "skyfi_view_current_budget":
                # Handle budget tools
                from .budget_tools import call_budget_tool
                return await call_budget_tool(name, arguments)
            
            elif name == "skyfi_spending_report":
                total_spent = client.cost_tracker.get_total_spent()
                remaining = client.cost_tracker.get_remaining_budget(client.config.cost_limit)
                orders = client.cost_tracker.get_order_history()
                
                report = f"💰 SkyFi Spending Report\n"
                report += f"{'=' * 40}\n\n"
                report += f"Total Spent: ${total_spent:.2f}\n"
                report += f"Budget Limit: ${client.config.cost_limit:.2f}\n"
                report += f"Remaining: ${remaining:.2f}\n"
                report += f"Orders Made: {len(orders)}\n\n"
                
                report += "Safety Settings:\n"
                report += f"- Ordering Enabled: {client.config.enable_ordering}\n"
                report += f"- Force Lowest Cost: {client.config.force_lowest_cost}\n\n"
                
                if orders:
                    report += "Recent Orders:\n"
                    for order in orders[-5:]:  # Last 5 orders
                        report += f"- {order['timestamp']}: ${order['cost']:.2f} ({order['archive_id']})\n"
                
                return [TextContent(type="text", text=report)]
            
            else:
                raise ValueError(f"Unknown SkyFi tool: {name}")
    
    except Exception as e:
        logger.error(f"Error handling SkyFi tool {name}: {e}")
        error_msg = f"Error executing {name}: {str(e)}"
        
        # Add helpful error messages
        if "401" in str(e) or "authentication" in str(e).lower():
            error_msg += "\n\nTroubleshooting:\n"
            error_msg += "- Check that SKYFI_API_KEY is set correctly\n"
            error_msg += "- Verify your API key at app.skyfi.com\n"
            error_msg += "- Ensure you have a Pro account"
        
        return [TextContent(type="text", text=error_msg)]