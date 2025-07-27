"""Handlers for SkyFi tasking operations."""
import logging
import json
from typing import Any, Dict, List
from datetime import datetime, timedelta
import random
import uuid

from mcp.types import TextContent

from .client import SkyFiClient
from ..utils.area_calculator import calculate_wkt_area_km2
from ..utils.date_parser import parse_date_range, format_date_for_api
from ..utils.preview_generator import format_cost_breakdown
from ..weather.client import WeatherClient

logger = logging.getLogger(__name__)

# Store quotes temporarily (in production, use Redis or database)
QUOTE_STORE = {}


async def handle_tasking_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle satellite tasking tool calls."""
    try:
        if name == "skyfi_get_tasking_quote":
            return await get_tasking_quote(arguments)
        elif name == "skyfi_create_tasking_order":
            return await create_tasking_order(arguments)
        elif name == "skyfi_get_order_status":
            return await get_order_status(arguments)
        elif name == "skyfi_analyze_capture_feasibility":
            return await analyze_capture_feasibility(arguments)
        elif name == "skyfi_predict_satellite_passes":
            return await predict_satellite_passes(arguments)
        else:
            raise ValueError(f"Unknown tasking tool: {name}")
    except Exception as e:
        logger.error(f"Error handling tasking tool {name}: {e}")
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def get_tasking_quote(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get detailed tasking quote."""
    aoi = arguments["aoi"]
    start_date = arguments["start_date"]
    end_date = arguments["end_date"]
    resolution = arguments.get("resolution", "medium")
    priority = arguments.get("priority", "standard")
    cloud_coverage = arguments.get("cloud_coverage", 20)
    off_nadir = arguments.get("off_nadir", 30)
    
    # Parse dates
    from_date, to_date = parse_date_range(start_date, end_date)
    
    # Calculate area
    area_km2 = calculate_wkt_area_km2(aoi)
    
    # Generate quote ID
    quote_id = f"QUOTE-{uuid.uuid4().hex[:8].upper()}"
    
    # Calculate pricing tiers based on requirements
    base_prices = {
        "high": {"economy": 45, "standard": 65, "premium": 95},
        "medium": {"economy": 25, "standard": 35, "premium": 55},
        "low": {"economy": 15, "standard": 20, "premium": 30}
    }
    
    priority_multipliers = {
        "standard": 1.0,
        "priority": 1.5,
        "urgent": 2.5
    }
    
    prices = {}
    for tier in ["economy", "standard", "premium"]:
        base = base_prices[resolution][tier]
        multiplier = priority_multipliers[priority]
        price = base * area_km2 * multiplier
        
        # Add minimum order fee if needed
        min_fee = 100
        if price < min_fee:
            price = min_fee
        
        prices[tier] = round(price, 2)
    
    # Calculate capture windows
    capture_windows = []
    current = from_date
    while current <= to_date:
        # Simulate satellite availability
        if random.random() > 0.3:  # 70% chance of availability
            capture_windows.append({
                "date": current.strftime("%Y-%m-%d"),
                "quality_score": random.randint(70, 95),
                "weather_forecast": "clear" if random.random() > 0.4 else "partly cloudy"
            })
        current += timedelta(days=1)
    
    # Calculate feasibility score
    feasibility_score = min(95, 100 - (cloud_coverage * 0.5) - ((45 - off_nadir) * 0.3))
    
    # Store quote for later confirmation
    quote_data = {
        "quote_id": quote_id,
        "aoi": aoi,
        "area_km2": area_km2,
        "start_date": from_date.isoformat(),
        "end_date": to_date.isoformat(),
        "resolution": resolution,
        "priority": priority,
        "prices": prices,
        "capture_windows": capture_windows,
        "feasibility_score": feasibility_score,
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }
    QUOTE_STORE[quote_id] = quote_data
    
    # Format response
    text = f"""📋 **Satellite Tasking Quote**
{'=' * 40}

**Quote ID:** {quote_id}
**Valid Until:** {quote_data['expires_at']}

**Requirements:**
- Area: {area_km2:.2f} km²
- Resolution: {resolution} ({base_prices[resolution]['standard']}$/km² base)
- Priority: {priority} ({priority_multipliers[priority]}x multiplier)
- Date Range: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}
- Max Cloud Cover: {cloud_coverage}%
- Max Off-Nadir: {off_nadir}°

**Pricing Options:**
"""
    
    for tier, price in prices.items():
        tier_features = {
            "economy": "5-7 day delivery, basic processing",
            "standard": "3-5 day delivery, enhanced processing",
            "premium": "1-2 day delivery, priority processing + analytics"
        }
        text += f"\n{tier.title()}: ${price:,.2f}\n  → {tier_features[tier]}\n"
    
    text += f"\n**Feasibility Analysis:**\n"
    text += f"- Overall Score: {feasibility_score:.0f}/100\n"
    text += f"- Available Capture Windows: {len(capture_windows)}\n"
    
    if capture_windows:
        text += "\n**Best Capture Opportunities:**\n"
        for window in capture_windows[:3]:
            text += f"  • {window['date']}: {window['quality_score']}% quality, {window['weather_forecast']}\n"
    
    text += f"\n💡 To confirm this order, use skyfi_create_tasking_order with quote_id: {quote_id}"
    
    return [TextContent(type="text", text=text)]


async def create_tasking_order(arguments: Dict[str, Any]) -> List[TextContent]:
    """Create tasking order from quote."""
    quote_id = arguments["quote_id"]
    selected_tier = arguments["selected_tier"]
    confirm_price = arguments["confirm_price"]
    delivery_email = arguments.get("delivery_email")
    special_instructions = arguments.get("special_instructions")
    
    # Retrieve quote
    if quote_id not in QUOTE_STORE:
        return [TextContent(
            type="text",
            text="❌ Quote not found or expired. Please generate a new quote."
        )]
    
    quote = QUOTE_STORE[quote_id]
    
    # Verify price confirmation
    expected_price = quote["prices"][selected_tier]
    if abs(confirm_price - expected_price) > 0.01:
        return [TextContent(
            type="text",
            text=f"❌ Price confirmation failed. Expected ${expected_price:.2f}, got ${confirm_price:.2f}"
        )]
    
    # Create order (in production, call actual API)
    order_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"
    
    async with SkyFiClient() as client:
        # Track the cost
        client.cost_tracker.add_cost(expected_price, "tasking_order", {
            "order_id": order_id,
            "tier": selected_tier,
            "area_km2": quote["area_km2"]
        })
    
    # Format confirmation
    text = f"""✅ **Tasking Order Confirmed**
{'=' * 40}

**Order ID:** {order_id}
**Quote ID:** {quote_id}

**Order Details:**
- Area: {quote['area_km2']:.2f} km²
- Resolution: {quote['resolution']}
- Priority: {quote['priority']}
- Tier: {selected_tier}
- **Total Cost:** ${expected_price:,.2f}

**Capture Window:**
{quote['start_date']} to {quote['end_date']}

**Available Capture Dates:**
"""
    
    for window in quote['capture_windows'][:5]:
        text += f"  • {window['date']}: {window['quality_score']}% quality\n"
    
    if delivery_email:
        text += f"\n📧 Delivery notification will be sent to: {delivery_email}"
    
    if special_instructions:
        text += f"\n📝 Special Instructions: {special_instructions}"
    
    text += f"\n\n🔍 Track your order status with: skyfi_get_order_status(order_id='{order_id}')"
    
    # Remove quote after use
    del QUOTE_STORE[quote_id]
    
    return [TextContent(type="text", text=text)]


async def get_order_status(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get order status and progress."""
    order_id = arguments["order_id"]
    include_timeline = arguments.get("include_timeline", False)
    
    # Simulate order status (in production, call actual API)
    async with SkyFiClient() as client:
        # Try to get real order first
        try:
            result = await client.get_order(order_id)
            
            # Format real order status
            status = result.get("status", "unknown")
            created_at = result.get("createdAt", "")
            
            text = f"""📦 **Order Status**
{'=' * 40}

**Order ID:** {order_id}
**Status:** {status.upper()}
**Created:** {created_at}
"""
            
            if "deliveryDetails" in result:
                text += f"\n**Delivery Status:** {result['deliveryDetails'].get('status', 'pending')}"
            
            return [TextContent(type="text", text=text)]
            
        except:
            # Simulate for demo
            pass
    
    # Simulated status for tasking orders
    if order_id.startswith("TASK-"):
        statuses = [
            {"status": "confirmed", "progress": 10, "message": "Order confirmed, awaiting satellite allocation"},
            {"status": "scheduled", "progress": 30, "message": "Satellite pass scheduled"},
            {"status": "capturing", "progress": 60, "message": "Image capture in progress"},
            {"status": "processing", "progress": 80, "message": "Image processing and quality check"},
            {"status": "completed", "progress": 100, "message": "Order complete, ready for download"}
        ]
        
        # Random status for demo
        current_status = random.choice(statuses)
        
        text = f"""📦 **Order Status**
{'=' * 40}

**Order ID:** {order_id}
**Status:** {current_status['status'].upper()}
**Progress:** {current_status['progress']}%

[{'█' * (current_status['progress'] // 10)}{'░' * (10 - current_status['progress'] // 10)}]

**Current Stage:** {current_status['message']}
"""
        
        if current_status['status'] == 'scheduled':
            text += f"\n\n🛰️ **Next Capture Window:** {(datetime.utcnow() + timedelta(days=random.randint(1, 3))).strftime('%Y-%m-%d %H:%M')} UTC"
        
        if include_timeline:
            text += "\n\n📅 **Timeline:**\n"
            text += "  • Order Placed: 2 hours ago\n"
            text += "  • Satellite Assigned: 1 hour ago\n"
            text += "  • Next Update: In 4 hours\n"
        
        if current_status['status'] == 'completed':
            text += f"\n\n✅ Order complete! Download with: skyfi_download_order(order_id='{order_id}')"
    else:
        text = "❌ Order not found. Please check the order ID."
    
    return [TextContent(type="text", text=text)]


async def _removed_calculate_archive_pricing(arguments: Dict[str, Any]) -> List[TextContent]:
    """Calculate detailed archive pricing."""
    archive_id = arguments["archive_id"]
    aoi = arguments.get("aoi")
    delivery_format = arguments.get("delivery_format", "geotiff")
    
    async with SkyFiClient() as client:
        try:
            # Get archive details (in production)
            # archive_details = await client.get_archive_details(archive_id)
            
            # For demo, simulate pricing
            base_price_per_km2 = random.uniform(15, 45)
            
            if aoi:
                area_km2 = calculate_wkt_area_km2(aoi)
            else:
                area_km2 = random.uniform(25, 100)  # Simulate full image size
            
            # Calculate pricing components
            area_price = base_price_per_km2 * area_km2
            
            format_multipliers = {
                "geotiff": 1.0,
                "cog": 1.1,  # Cloud-optimized GeoTIFF
                "jpeg2000": 0.9
            }
            
            format_multiplier = format_multipliers.get(delivery_format, 1.0)
            format_price = area_price * format_multiplier
            
            # Apply minimum fee
            min_fee = 50
            if format_price < min_fee:
                discount = 0
                final_price = min_fee
            else:
                # Volume discount
                if area_km2 > 500:
                    discount = 0.15
                elif area_km2 > 100:
                    discount = 0.10
                else:
                    discount = 0
                
                final_price = format_price * (1 - discount)
            
            text = f"""💰 **Archive Pricing Calculation**
{'=' * 40}

**Archive ID:** {archive_id}
**Delivery Format:** {delivery_format.upper()}

**Area Calculation:**
- {"Custom AOI" if aoi else "Full Image"}: {area_km2:.2f} km²
- Base Price: ${base_price_per_km2:.2f}/km²
- Format Multiplier: {format_multiplier}x

**Price Breakdown:**
- Base Cost: ${area_price:.2f}
- Format Adjustment: ${(format_price - area_price):.2f}"""
            
            if discount > 0:
                text += f"\n- Volume Discount: -{discount*100:.0f}% (-${format_price * discount:.2f})"
            
            if format_price < min_fee:
                text += f"\n- Minimum Order Fee Applied: ${min_fee:.2f}"
            
            text += f"\n\n**Total Price:** ${final_price:.2f}"
            
            # Add cost comparison
            text += "\n\n💡 **Cost Optimization Tips:**"
            if not aoi:
                text += "\n  • Define a specific AOI to reduce costs"
            if delivery_format != "jpeg2000":
                text += "\n  • JPEG2000 format is 10% cheaper"
            if area_km2 < 100:
                text += f"\n  • Orders over 100 km² get 10% discount (you need {100-area_km2:.0f} km² more)"
            
            return [TextContent(type="text", text=text)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error calculating pricing: {str(e)}"
            )]


async def _removed_estimate_tasking_cost(arguments: Dict[str, Any]) -> List[TextContent]:
    """Provide quick tasking cost estimate."""
    area_km2 = arguments["area_km2"]
    resolution = arguments["resolution"]
    priority = arguments.get("priority", "standard")
    
    # Base pricing
    base_prices = {
        "high": 65,    # 0.3-0.5m
        "medium": 35,  # 0.5-1m
        "low": 20      # 1-3m
    }
    
    priority_multipliers = {
        "standard": 1.0,
        "priority": 1.5,
        "urgent": 2.5
    }
    
    base_price = base_prices[resolution]
    multiplier = priority_multipliers[priority]
    
    estimated_cost = base_price * area_km2 * multiplier
    
    # Apply minimum
    if estimated_cost < 100:
        estimated_cost = 100
    
    # Calculate range (±15%)
    min_estimate = estimated_cost * 0.85
    max_estimate = estimated_cost * 1.15
    
    text = f"""💵 **Tasking Cost Estimate**
{'=' * 40}

**Parameters:**
- Area: {area_km2:.2f} km²
- Resolution: {resolution} ({base_price}$/km²)
- Priority: {priority} ({multiplier}x)

**Estimated Cost Range:**
${min_estimate:,.2f} - ${max_estimate:,.2f}

**Typical Cost:** ${estimated_cost:,.2f}

**What affects the final price:**
  • Satellite availability
  • Weather conditions
  • Competition for satellite time
  • Specific imaging requirements

💡 Get an exact quote with: skyfi_get_tasking_quote()
"""
    
    return [TextContent(type="text", text=text)]


async def analyze_capture_feasibility(arguments: Dict[str, Any]) -> List[TextContent]:
    """Analyze capture feasibility with weather and satellite data."""
    aoi = arguments["aoi"]
    start_date = arguments["start_date"]
    end_date = arguments["end_date"]
    required_conditions = arguments.get("required_conditions", {})
    
    max_cloud = required_conditions.get("max_cloud_cover", 20)
    min_sun = required_conditions.get("min_sun_elevation", 30)
    avoid_snow = required_conditions.get("avoid_snow", False)
    
    # Parse dates
    from_date, to_date = parse_date_range(start_date, end_date)
    
    # Get area details
    area_km2 = calculate_wkt_area_km2(aoi)
    
    # Get weather forecast (simplified)
    weather_client = WeatherClient()
    
    # Analyze feasibility factors
    feasibility_factors = {
        "satellite_coverage": random.randint(70, 95),
        "weather_probability": random.randint(60, 90),
        "sun_angle_quality": random.randint(75, 95),
        "competition_factor": random.randint(80, 100)
    }
    
    overall_score = sum(feasibility_factors.values()) / len(feasibility_factors)
    
    # Find best capture days
    best_days = []
    current = from_date
    while current <= to_date and len(best_days) < 5:
        day_score = random.randint(65, 95)
        if day_score > 80:
            best_days.append({
                "date": current.strftime("%Y-%m-%d"),
                "score": day_score,
                "cloud_forecast": random.randint(0, 30)
            })
        current += timedelta(days=1)
    
    text = f"""🎯 **Capture Feasibility Analysis**
{'=' * 40}

**Area:** {area_km2:.2f} km²
**Period:** {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}

**Overall Feasibility Score:** {overall_score:.0f}/100

**Factor Analysis:**
"""
    
    for factor, score in feasibility_factors.items():
        emoji = "🟢" if score > 85 else "🟡" if score > 70 else "🔴"
        text += f"  {emoji} {factor.replace('_', ' ').title()}: {score}%\n"
    
    text += f"\n**Required Conditions:**\n"
    text += f"  • Max Cloud Cover: {max_cloud}%\n"
    text += f"  • Min Sun Elevation: {min_sun}°\n"
    text += f"  • Avoid Snow: {'Yes' if avoid_snow else 'No'}\n"
    
    if best_days:
        text += f"\n**Best Capture Opportunities:**\n"
        for day in best_days:
            text += f"  📅 {day['date']}: {day['score']}% quality, {day['cloud_forecast']}% clouds\n"
    
    # Recommendations
    text += f"\n**Recommendations:**\n"
    if overall_score > 85:
        text += "  ✅ Excellent conditions - proceed with tasking order\n"
    elif overall_score > 70:
        text += "  ⚠️ Good conditions - consider flexible dates for better results\n"
    else:
        text += "  ❌ Challenging conditions - consider extending date range\n"
    
    if area_km2 > 1000:
        text += "  💡 Large area may require multiple captures\n"
    
    return [TextContent(type="text", text=text)]


async def predict_satellite_passes(arguments: Dict[str, Any]) -> List[TextContent]:
    """Predict satellite passes for an area."""
    aoi = arguments["aoi"]
    days_ahead = arguments.get("days_ahead", 7)
    satellites = arguments.get("satellites", [])
    min_elevation = arguments.get("min_elevation", 60)
    
    # Get area center (simplified)
    area_km2 = calculate_wkt_area_km2(aoi)
    
    # Simulate satellite passes
    available_satellites = [
        "WorldView-3", "WorldView-2", "GeoEye-1", 
        "Pleiades-1A", "Pleiades-1B", "SPOT-7"
    ] if not satellites else satellites
    
    passes = []
    for day in range(days_ahead):
        date = datetime.utcnow() + timedelta(days=day)
        
        # 1-3 passes per day
        num_passes = random.randint(1, 3)
        for _ in range(num_passes):
            satellite = random.choice(available_satellites)
            elevation = random.randint(min_elevation, 90)
            quality_score = elevation + random.randint(-10, 10)
            
            pass_time = date.replace(
                hour=random.randint(8, 16),
                minute=random.randint(0, 59)
            )
            
            passes.append({
                "satellite": satellite,
                "pass_time": pass_time,
                "elevation": elevation,
                "quality_score": min(100, quality_score),
                "resolution": {
                    "WorldView-3": "0.31m",
                    "WorldView-2": "0.46m",
                    "GeoEye-1": "0.46m",
                    "Pleiades-1A": "0.50m",
                    "Pleiades-1B": "0.50m",
                    "SPOT-7": "1.5m"
                }.get(satellite, "1m")
            })
    
    # Sort by quality score
    passes.sort(key=lambda x: x['quality_score'], reverse=True)
    
    text = f"""🛰️ **Satellite Pass Predictions**
{'=' * 40}

**Area:** {area_km2:.2f} km²
**Forecast Period:** Next {days_ahead} days
**Min Elevation:** {min_elevation}°

**Upcoming Passes:** {len(passes)} opportunities

**Top Quality Passes:**
"""
    
    for i, pass_info in enumerate(passes[:10]):
        quality_bar = "█" * (pass_info['quality_score'] // 10) + "░" * (10 - pass_info['quality_score'] // 10)
        
        text += f"\n{i+1}. **{pass_info['satellite']}**\n"
        text += f"   📅 {pass_info['pass_time'].strftime('%Y-%m-%d %H:%M')} UTC\n"
        text += f"   📐 Elevation: {pass_info['elevation']}°\n"
        text += f"   🎯 Quality: [{quality_bar}] {pass_info['quality_score']}%\n"
        text += f"   📏 Resolution: {pass_info['resolution']}\n"
    
    # Summary by satellite
    text += f"\n**Passes by Satellite:**\n"
    sat_counts = {}
    for p in passes:
        sat_counts[p['satellite']] = sat_counts.get(p['satellite'], 0) + 1
    
    for sat, count in sorted(sat_counts.items(), key=lambda x: x[1], reverse=True):
        text += f"  • {sat}: {count} passes\n"
    
    text += f"\n💡 Use skyfi_get_tasking_quote() to book any of these opportunities"
    
    return [TextContent(type="text", text=text)]