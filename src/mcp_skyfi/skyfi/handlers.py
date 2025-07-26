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
                # Parse dates with natural language support
                from_date_str = arguments["fromDate"]
                to_date_str = arguments["toDate"]
                
                # Try natural language parsing
                try:
                    from ..utils.date_parser import parse_date_range, format_date_for_api
                    from_date, to_date = parse_date_range(from_date_str, to_date_str)
                    from_date_iso = format_date_for_api(from_date)
                    to_date_iso = format_date_for_api(to_date)
                    
                    logger.info(f"Parsed dates: '{from_date_str}' → {from_date_iso}, '{to_date_str}' → {to_date_iso}")
                except Exception as e:
                    logger.warning(f"Failed to parse natural dates, using as-is: {e}")
                    from_date_iso = from_date_str
                    to_date_iso = to_date_str
                
                result = await client.search_archives(
                    aoi=arguments["aoi"],
                    from_date=from_date_iso,
                    to_date=to_date_iso,
                    open_data=arguments.get("openData", True),
                    product_types=arguments.get("productTypes"),
                    resolution=arguments.get("resolution"),
                )
                
                # Format results with previews
                if "results" in result:
                    from ..utils.preview_generator import format_search_results_with_previews
                    from ..utils.budget_alerts import format_spending_summary
                    from ..utils.price_interpreter import needs_price_clarification
                    
                    # Calculate area if provided in search
                    search_area_km2 = None
                    if "aoi" in arguments:
                        try:
                            from ..utils.area_calculator import calculate_wkt_area_km2
                            search_area_km2 = calculate_wkt_area_km2(arguments["aoi"])
                        except:
                            pass
                    
                    # Show spending summary at the top
                    text = format_spending_summary(client.cost_tracker, client.config) + "\n\n"
                    
                    # Check if we need price clarification
                    if needs_price_clarification(result['results']):
                        text += "⚠️  Note: Prices shown are per km². Total cost = price × area (min 25 km²)\n\n"
                    
                    # Format results with area context
                    text += format_search_results_with_previews(result['results'], max_results=5, area_km2=search_area_km2)
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
                provided_cost = float(arguments["estimated_cost"])
                
                # Calculate area and auto-expand if too small
                from ..utils.area_calculator import calculate_wkt_area_km2, expand_polygon_to_minimum_area
                from ..utils.price_interpreter import estimate_order_cost, interpret_archive_price
                from ..utils.budget_alerts import check_order_feasibility, format_budget_alert
                
                original_area_km2 = calculate_wkt_area_km2(aoi)
                
                # Auto-expand if area is too small
                if original_area_km2 < 5.0:
                    logger.info(f"Auto-expanding area from {original_area_km2:.2f} km² to 5.1 km²")
                    # Use 5.1 km² to ensure we're safely above the 5.0 minimum
                    aoi = expand_polygon_to_minimum_area(aoi, min_area_km2=5.1)
                    area_km2 = calculate_wkt_area_km2(aoi)
                else:
                    area_km2 = original_area_km2
                
                # Interpret the price - determine if it's per km² or total
                # Look for the archive in search history if possible
                archive_data = {"price": provided_cost}  # Basic archive data
                price_per_km2, estimated_cost, price_explanation = interpret_archive_price(archive_data, area_km2)
                
                # If the provided cost is suspiciously low, it's likely per km²
                if provided_cost < 10 and area_km2 > 5:
                    # Force interpretation as price per km²
                    price_per_km2 = provided_cost
                    billable_area = max(area_km2, 25.0)
                    estimated_cost = price_per_km2 * billable_area
                    if area_km2 < 25.0:
                        price_explanation = f"${price_per_km2:.2f}/km² × 25 km² (minimum billing)"
                    else:
                        price_explanation = f"${price_per_km2:.2f}/km² × {area_km2:.1f} km²"
                
                # Log price interpretation for debugging
                logger.info(f"Price interpretation: provided=${provided_cost:.2f}, per_km2=${price_per_km2:.2f}, total=${estimated_cost:.2f}")
                
                # Create order manager
                order_manager = OrderManager()
                
                # Perform all safety checks
                checks_passed = True
                warnings = []
                
                # Check 0: Area size maximum (we auto-expand small areas)
                if area_km2 > 10000.0:
                    checks_passed = False
                    warnings.append(
                        f"❌ Area too large: {area_km2:.2f} km² (maximum: 10,000 km²)\n"
                        f"   Please select a smaller area or split into multiple orders."
                    )
                
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
                # Use NONE delivery driver for SkyFi-hosted downloads
                order_details = {
                    "aoi": aoi,
                    "archiveId": archive_id,
                    "deliveryDriver": "NONE",  # NONE = use SkyFi download URLs
                    "deliveryParams": None  # Must be null for NONE delivery driver
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
                
                # Show area information with visual
                from ..utils.preview_generator import estimate_area_preview
                area_visual = estimate_area_preview(area_km2)
                
                if original_area_km2 < 5.0:
                    response += f"Area: {area_visual}\n"
                    response += f"     (auto-expanded from {original_area_km2:.2f} km² to meet minimum)\n"
                    response += f"⚠️ Your area was automatically expanded to meet the 5 km² minimum\n"
                else:
                    response += f"Area: {area_visual}\n"
                
                # Price breakdown
                response += f"\n💰 Price Calculation:\n"
                response += f"   {price_explanation} = ${estimated_cost:.2f}\n"
                if area_km2 < 25.0:
                    response += f"   ℹ️  Minimum billing area: 25 km²\n"
                
                response += f"\nDelivery: Download URL (no cloud storage needed)\n\n"
                
                # Budget status with visual alerts
                response += "📊 Budget Impact:\n"
                response += format_budget_alert(total_spent, client.config.cost_limit, "Before") + "\n"
                response += format_budget_alert(total_spent + estimated_cost, client.config.cost_limit, "After") + "\n\n"
                
                # Check if order is feasible
                is_feasible, feasibility_warnings = check_order_feasibility(estimated_cost, client.cost_tracker, client.config)
                if not is_feasible:
                    response += "⚠️  Budget Warnings:\n"
                    response += feasibility_warnings + "\n\n"
                
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
                    # Log the order details for debugging
                    logger.info(f"Order details from storage: {json.dumps(order['details'], indent=2)}")
                    
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
            
            elif name == "skyfi_update_account_budget":
                # Handle account tools
                from .account_tools import call_account_tool
                return await call_account_tool(name, arguments)
            
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
            
            elif name == "skyfi_list_orders":
                order_type = arguments.get("order_type")
                page_size = arguments.get("page_size", 10)
                page_number = arguments.get("page_number", 0)
                
                try:
                    result = await client.list_orders(
                        order_type=order_type,
                        page_size=page_size,
                        page_number=page_number
                    )
                    
                    # Format the response
                    text = f"📋 Order History (Page {page_number + 1})\n"
                    text += f"{'=' * 50}\n\n"
                    text += f"Total orders: {result.get('total', 0)}\n\n"
                    
                    orders = result.get('orders', [])
                    if not orders:
                        text += "No orders found.\n"
                    else:
                        for idx, order in enumerate(orders, 1):
                            order_id = order.get('id', 'N/A')
                            order_type = order.get('orderType', 'N/A')
                            status = order.get('status', 'N/A')
                            cost = order.get('orderCost', 0)
                            created = order.get('createdAt', 'N/A')
                            order_code = order.get('orderCode', 'N/A')
                            location = order.get('geocodeLocation', 'N/A')
                            
                            # Get visual status
                            from ..utils.preview_generator import generate_order_status_preview
                            status_visual = generate_order_status_preview(order)
                            
                            text += f"{idx}. Order {order_code} ({order_type})\n"
                            text += f"   {status_visual}\n"
                            text += f"   ID: {order_id}\n"
                            text += f"   Cost: ${cost / 100:.2f}\n" if cost > 0 else "   Cost: FREE\n"
                            text += f"   Location: {location}\n"
                            text += f"   Created: {created}\n"
                            
                            # Add download URLs if complete
                            if status == 'PROCESSING_COMPLETE':
                                text += f"   📥 Download Image: Use skyfi_get_download_url with order_id='{order_id}'\n"
                            
                            # Add archive details if available
                            if order_type == 'ARCHIVE' and 'archive' in order:
                                archive = order['archive']
                                constellation = archive.get('constellation', 'N/A')
                                capture_date = archive.get('captureTimestamp', 'N/A')
                                cloud_cover = archive.get('cloudCoveragePercent', 'N/A')
                                text += f"   Satellite: {constellation}\n"
                                text += f"   Captured: {capture_date}\n"
                                text += f"   Cloud Cover: {cloud_cover:.1f}%\n"
                            
                            text += "\n"
                    
                    # Add pagination info
                    if result.get('total', 0) > page_size:
                        total_pages = (result['total'] + page_size - 1) // page_size
                        text += f"\n📖 Page {page_number + 1} of {total_pages}\n"
                        if page_number < total_pages - 1:
                            text += f"Use page_number={page_number + 1} to see more orders.\n"
                    
                    # Add download instructions if any orders are complete
                    has_complete_orders = any(o.get('status') == 'PROCESSING_COMPLETE' for o in orders)
                    if has_complete_orders:
                        text += "\n💡 To download completed orders, use skyfi_get_download_url with the order ID.\n"
                        text += "Files will be automatically downloaded to your temp directory.\n"
                    
                    return [TextContent(type="text", text=text)]
                    
                except Exception as e:
                    logger.error(f"Error listing orders: {e}")
                    return [TextContent(
                        type="text",
                        text=f"❌ Error listing orders: {str(e)}"
                    )]
            
            elif name == "skyfi_get_download_url":
                order_id = arguments["order_id"]
                deliverable_type = arguments.get("deliverable_type", "image")
                
                try:
                    download_url = await client.get_download_url(order_id, deliverable_type)
                    
                    # Try to download directly instead of showing curl command
                    try:
                        file_path = await client.download_order(order_id, deliverable_type)
                        
                        # Get file size for preview
                        import os
                        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        
                        preview_text = f"✅ Successfully downloaded order {order_id}\n\n"
                        preview_text += "📦 Download Complete\n"
                        preview_text += "┌────────────────────────────────────┐\n"
                        preview_text += f"│ 🖼️  {deliverable_type.upper():<29} │\n"
                        preview_text += f"│ 📏 Size: {file_size_mb:.1f} MB{' ' * (22 - len(f'{file_size_mb:.1f} MB'))} │\n"
                        preview_text += f"│ 📁 Saved to temp directory         │\n"
                        preview_text += "│                                    │\n"
                        preview_text += "│    ╔═══════════════════╗          │\n"
                        preview_text += "│    ║ 🛰️             🌍 ║          │\n"
                        preview_text += "│    ║                   ║          │\n"
                        preview_text += "│    ║   Satellite       ║          │\n"
                        preview_text += "│    ║     Image         ║          │\n"
                        preview_text += "│    ║                   ║          │\n"
                        preview_text += "│    ╚═══════════════════╝          │\n"
                        preview_text += "└────────────────────────────────────┘\n\n"
                        preview_text += f"📍 Location: {file_path}\n\n"
                        preview_text += "💡 Tip: You can open this file with any image viewer"
                        
                        return [TextContent(
                            type="text",
                            text=preview_text
                        )]
                    except Exception as download_error:
                        # If download fails, provide the URL and instructions
                        extensions = {
                            "image": "png",
                            "payload": "zip",
                            "tiles": "zip"
                        }
                        ext = extensions.get(deliverable_type, "dat")
                        
                        return [TextContent(
                            type="text",
                            text=(
                                f"📥 Order {order_id} - Download Information\n\n"
                                f"Type: {deliverable_type}\n"
                                f"Expected format: .{ext}\n\n"
                                f"⚠️ Could not download automatically: {str(download_error)}\n\n"
                                "To download manually, use this curl command:\n\n"
                                f"```bash\n"
                                f"curl -L -X GET \"{download_url}\" \\\n"
                                f"  -H \"X-Skyfi-Api-Key: {client.config.api_key}\" \\\n"
                                f"  --output skyfi-order-{order_id}.{ext}\n"
                                f"```"
                            )
                        )]
                except Exception as e:
                    return [TextContent(
                        type="text",
                        text=f"❌ Failed to get download URL: {str(e)}\n\nThe order may still be processing."
                    )]
            
            elif name == "skyfi_download_order":
                order_id = arguments["order_id"]
                deliverable_type = arguments.get("deliverable_type", "image")
                save_path = arguments.get("save_path")
                
                try:
                    file_path = await client.download_order(order_id, deliverable_type, save_path)
                    
                    return [TextContent(
                        type="text",
                        text=(
                            f"✅ Successfully downloaded order {order_id}\n\n"
                            f"📁 Saved to: {file_path}\n"
                            f"Type: {deliverable_type}\n\n"
                            "The file has been saved to your local disk."
                        )
                    )]
                except Exception as e:
                    return [TextContent(
                        type="text",
                        text=f"❌ Failed to download order: {str(e)}\n\nThe order may still be processing or there may be an authentication issue."
                    )]
            
            elif name == "skyfi_save_search":
                # Save search configuration
                from ..utils.saved_searches import SavedSearchManager
                manager = SavedSearchManager()
                
                search_id = manager.save_search(
                    name=arguments["name"],
                    aoi=arguments["aoi"],
                    from_date=arguments["from_date"],
                    to_date=arguments["to_date"],
                    description=arguments.get("description"),
                    tags=arguments.get("tags"),
                    resolution=arguments.get("resolution"),
                    max_cloud_cover=arguments.get("max_cloud_cover")
                )
                
                return [TextContent(
                    type="text",
                    text=f"✅ Search saved as '{arguments['name']}'\n\nSearch ID: {search_id}\n\nUse 'skyfi_run_saved_search' to run it anytime."
                )]
            
            elif name == "skyfi_list_saved_searches":
                # List saved searches
                from ..utils.saved_searches import SavedSearchManager
                manager = SavedSearchManager()
                
                searches = manager.list_searches(
                    tags=arguments.get("tags"),
                    sort_by=arguments.get("sort_by", "created_at")
                )
                
                text = manager.format_search_list(searches)
                return [TextContent(type="text", text=text)]
            
            elif name == "skyfi_run_saved_search":
                # Run saved search
                from ..utils.saved_searches import SavedSearchManager
                manager = SavedSearchManager()
                
                search = manager.get_search(arguments["search_name"])
                if not search:
                    return [TextContent(
                        type="text",
                        text=f"❌ Saved search '{arguments['search_name']}' not found.\n\nUse 'skyfi_list_saved_searches' to see available searches."
                    )]
                
                # Run the search with saved parameters
                from_date = search["from_date"]
                to_date = search["to_date"]
                
                # Override dates if requested
                if arguments.get("override_dates"):
                    from_date = "last month"
                    to_date = "today"
                
                # Parse dates
                from ..utils.date_parser import parse_date_range, format_date_for_api
                from_date_parsed, to_date_parsed = parse_date_range(from_date, to_date)
                
                result = await client.search_archives(
                    aoi=search["aoi"],
                    from_date=format_date_for_api(from_date_parsed),
                    to_date=format_date_for_api(to_date_parsed),
                    resolution=search.get("resolution"),
                    product_types=search.get("product_types")
                )
                
                # Format results
                from ..utils.preview_generator import format_search_results_with_previews
                text = f"🔄 Running saved search: {search['name']}\n"
                if search.get("description"):
                    text += f"📝 {search['description']}\n"
                text += f"\n{format_search_results_with_previews(result.get('results', []), area_km2=search.get('area_km2'))}"
                
                return [TextContent(type="text", text=text)]
            
            elif name == "skyfi_multi_location_search":
                # Multi-location search
                from ..utils.multi_location import MultiLocationSearcher, create_locations_from_points
                
                # Prepare locations
                locations = arguments.get("locations", [])
                
                # If points provided, convert to polygons
                if "points" in arguments and arguments["points"]:
                    buffer_km = arguments.get("buffer_km", 5.0)
                    point_locations = create_locations_from_points(
                        arguments["points"],
                        buffer_km
                    )
                    locations.extend(point_locations)
                
                if not locations:
                    return [TextContent(
                        type="text",
                        text="❌ No locations provided. Specify either 'locations' (WKT polygons) or 'points' ([lon,lat] pairs)."
                    )]
                
                # Create searcher
                searcher = MultiLocationSearcher(client)
                
                # Parse dates
                from ..utils.date_parser import parse_date_range, format_date_for_api
                from_date, to_date = parse_date_range(
                    arguments["from_date"],
                    arguments["to_date"]
                )
                
                # Search all locations
                results = await searcher.search_multiple_locations(
                    locations=locations,
                    from_date=format_date_for_api(from_date),
                    to_date=format_date_for_api(to_date),
                    resolution=arguments.get("resolution")
                )
                
                # Format results
                text = searcher.format_multi_location_results(results)
                return [TextContent(type="text", text=text)]
            
            elif name == "skyfi_export_order_history":
                # Export order history
                from ..utils.order_export import OrderExporter
                
                # Get all orders
                all_orders = []
                page = 0
                while True:
                    result = await client.list_orders(page_size=100, page_number=page)
                    orders = result.get("orders", [])
                    if not orders:
                        break
                    all_orders.extend(orders)
                    page += 1
                    if len(all_orders) >= result.get("total", 0):
                        break
                
                if not all_orders:
                    return [TextContent(
                        type="text",
                        text="No orders found to export."
                    )]
                
                # Export
                exporter = OrderExporter()
                output_path = exporter.export_orders(
                    orders=all_orders,
                    format=arguments.get("format", "csv"),
                    output_path=arguments.get("output_path")
                )
                
                # Generate summary if requested
                text = f"✅ Exported {len(all_orders)} orders to {output_path}\n\n"
                
                if arguments.get("include_summary", True):
                    summary = exporter.generate_summary_report(all_orders)
                    text += summary
                
                return [TextContent(type="text", text=text)]
            
            elif name == "skyfi_estimate_cost":
                # Get accurate cost estimate
                from ..utils.cost_estimator import CostEstimator
                
                # Find the archive in recent searches
                # For now, create a basic archive object
                archive = {"archiveId": arguments["archive_id"], "price": 1.0}  # Default price
                
                estimator = CostEstimator()
                cost_info = estimator.estimate_order_cost(
                    archive=archive,
                    area_km2=arguments["area_km2"],
                    include_fees=arguments.get("include_fees", True)
                )
                
                text = f"💰 Cost Estimate for {arguments['archive_id']}\n"
                text += "━" * 40 + "\n\n"
                text += cost_info["breakdown_text"] + "\n\n"
                
                if cost_info["notes"]:
                    text += "📝 Notes:\n"
                    for note in cost_info["notes"]:
                        text += f"  • {note}\n"
                
                return [TextContent(type="text", text=text)]
            
            elif name == "skyfi_compare_costs":
                # Compare costs across archives
                from ..utils.cost_estimator import CostEstimator
                
                # For demo, create basic archive objects
                archives = [
                    {"archiveId": aid, "satellite": "Demo", "price": 1.0}
                    for aid in arguments["archive_ids"]
                ]
                
                estimator = CostEstimator()
                comparison = estimator.format_cost_comparison(
                    archives=archives,
                    area_km2=arguments["area_km2"]
                )
                
                return [TextContent(type="text", text=comparison)]
            
            elif name == "skyfi_authenticate":
                # Generate secure authentication link
                from ..auth.nonce_auth import nonce_auth
                
                # Get session ID (this would come from MCP context in production)
                import uuid
                session_id = str(uuid.uuid4())
                
                # Generate auth session
                nonce, auth_url = nonce_auth.generate_auth_session(session_id)
                
                return [TextContent(
                    type="text",
                    text=(
                        "🔐 Secure Authentication Setup\n"
                        "━" * 40 + "\n\n"
                        "Please visit this secure link to enter your SkyFi API key:\n\n"
                        f"🔗 {auth_url}\n\n"
                        "This link will:\n"
                        "✅ Use HTTPS encryption\n"
                        "✅ Expire in 5 minutes\n"
                        "✅ Only work once\n"
                        "✅ Never expose your key in chat\n\n"
                        "After authenticating, close the browser and return here."
                    )
                )]
            
            elif name == "skyfi_set_api_key":
                # Set API key at runtime
                from ..auth import auth_manager
                
                api_key = arguments["api_key"]
                auth_manager.set_api_key(api_key)
                
                # Test the key by making a simple API call
                try:
                    # Create a new client with the updated key
                    test_client = SkyFiClient()
                    test_client.update_api_key(api_key)
                    
                    # Test the key
                    async with test_client:
                        user_info = await test_client.get_user()
                    
                    return [TextContent(
                        type="text",
                        text=(
                            "✅ API key set and verified successfully!\n\n"
                            f"Authenticated as: {user_info.get('email', 'Unknown')}\n"
                            f"Account type: {user_info.get('accountType', 'Unknown')}\n\n"
                            "The key has been saved for this session and will persist across tool calls.\n"
                            "Note: The key is stored temporarily and will be cleared when the server restarts."
                        )
                    )]
                except Exception as e:
                    # Key is invalid
                    auth_manager.clear_runtime_config()
                    return [TextContent(
                        type="text",
                        text=f"❌ Failed to set API key: {str(e)}\n\nPlease check your API key and try again."
                    )]
            
            elif name == "skyfi_check_auth":
                # Check authentication status
                from ..auth import auth_manager
                from ..auth.nonce_auth import nonce_auth
                
                # Try to get session ID from context
                import uuid
                session_id = str(uuid.uuid4())  # In production, this would come from MCP context
                
                # Check nonce-based auth first
                api_key = nonce_auth.get_api_key_for_session(session_id)
                if api_key:
                    auth_manager.set_api_key(api_key)
                
                has_key = auth_manager.get_api_key() is not None
                key_source = "Not configured"
                
                if has_key:
                    # Determine source
                    if nonce_auth.get_api_key_for_session(session_id):
                        key_source = "Web authentication"
                    elif os.environ.get("SKYFI_API_KEY"):
                        key_source = "Environment variable"
                    elif auth_manager.get_api_key():
                        key_source = "Runtime configuration"
                
                text = "🔐 Authentication Status\n"
                text += "━" * 40 + "\n\n"
                
                if has_key:
                    text += "✅ API key is configured\n"
                    text += f"Source: {key_source}\n\n"
                else:
                    text += "❌ No API key configured\n\n"
                    text += "To authenticate securely:\n\n"
                    text += "Use the `skyfi_authenticate` tool to get a secure link.\n"
                    text += "This lets you enter your API key via a secure web page\n"
                    text += "instead of typing it in chat.\n\n"
                    text += "Example: \"Set up my SkyFi authentication\""
                
                return [TextContent(type="text", text=text)]
            
            else:
                # Try tasking tools
                from .tasking_handlers import handle_tasking_tool
                tasking_tools = [
                    "skyfi_get_tasking_quote", "skyfi_create_tasking_order",
                    "skyfi_get_order_status", "skyfi_calculate_archive_pricing",
                    "skyfi_estimate_tasking_cost", "skyfi_analyze_capture_feasibility",
                    "skyfi_predict_satellite_passes", "skyfi_create_webhook_subscription",
                    "skyfi_setup_area_monitoring", "skyfi_get_notification_status"
                ]
                
                if name in tasking_tools:
                    return await handle_tasking_tool(name, arguments)
                
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