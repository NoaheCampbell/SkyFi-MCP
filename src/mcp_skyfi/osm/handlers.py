"""Handlers for OpenStreetMap tool calls."""
import json
import logging
from typing import Any, Dict, List
from urllib.parse import quote

import httpx
from mcp.types import TextContent

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "mcp-skyfi/0.1.0"


async def handle_osm_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle OSM tool calls."""
    headers = {"User-Agent": USER_AGENT}
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if name == "osm_geocode":
                query = arguments["query"]
                limit = arguments.get("limit", 5)
                
                response = await client.get(
                    f"{NOMINATIM_URL}/search",
                    params={
                        "q": query,
                        "format": "json",
                        "limit": limit,
                        "polygon_geojson": 1,
                    },
                    headers=headers,
                )
                response.raise_for_status()
                results = response.json()
                
                if not results:
                    return [TextContent(type="text", text=f"No results found for '{query}'")]
                
                text = f"Geocoding results for '{query}':\n\n"
                for idx, result in enumerate(results, 1):
                    text += f"{idx}. {result.get('display_name', 'Unknown')}\n"
                    text += f"   Lat: {result.get('lat', 'N/A')}, Lon: {result.get('lon', 'N/A')}\n"
                    text += f"   Type: {result.get('type', 'N/A')}\n\n"
                
                return [TextContent(type="text", text=text)]
            
            elif name == "osm_reverse_geocode":
                lat = arguments["lat"]
                lon = arguments["lon"]
                zoom = arguments.get("zoom", 18)
                
                response = await client.get(
                    f"{NOMINATIM_URL}/reverse",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "format": "json",
                        "zoom": zoom,
                    },
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()
                
                text = f"Address for coordinates ({lat}, {lon}):\n\n"
                text += f"Full Address: {result.get('display_name', 'Unknown')}\n"
                
                if "address" in result:
                    text += "\nAddress Components:\n"
                    for key, value in result["address"].items():
                        text += f"  {key}: {value}\n"
                
                return [TextContent(type="text", text=text)]
            
            elif name == "osm_polygon_to_wkt":
                place = arguments["place"]
                simplify = arguments.get("simplify", True)
                
                # First, geocode the place
                response = await client.get(
                    f"{NOMINATIM_URL}/search",
                    params={
                        "q": place,
                        "format": "json",
                        "limit": 1,
                        "polygon_text": 1,  # Get WKT directly
                    },
                    headers=headers,
                )
                response.raise_for_status()
                results = response.json()
                
                if not results or "geotext" not in results[0]:
                    return [TextContent(
                        type="text",
                        text=f"Could not find polygon boundary for '{place}'. Try a more specific location name."
                    )]
                
                wkt = results[0]["geotext"]
                display_name = results[0].get("display_name", place)
                lat = float(results[0].get("lat", 0))
                lon = float(results[0].get("lon", 0))
                
                # Import simplification utilities
                from ..utils.polygon_simplifier import parse_wkt_polygon, adaptive_simplify_wkt, estimate_wkt_size
                from ..utils.area_calculator import calculate_wkt_area_km2
                from ..utils.landmark_areas import landmark_to_wkt, get_landmark_bounds
                
                # Check polygon complexity
                try:
                    coords = parse_wkt_polygon(wkt)
                    original_points = len(coords)
                    original_size = estimate_wkt_size(wkt)
                    area_km2 = calculate_wkt_area_km2(wkt)
                    
                    # Check if this is a known landmark and polygon is complex
                    # Use lower threshold for automatic simplification
                    if original_points > 25 or original_size > 2000:
                        landmark_wkt = landmark_to_wkt(place)
                        if landmark_wkt:
                            landmark_area = calculate_wkt_area_km2(landmark_wkt)
                            text = f"🏛️ **Known Landmark: {place.title()}**\n\n"
                            text += f"Original polygon has {original_points} points - too complex for SkyFi API.\n"
                            text += f"Using pre-defined bounding box instead:\n\n"
                            text += f"```\n{landmark_wkt}\n```\n\n"
                            text += f"**Details:**\n"
                            text += f"- Area: {landmark_area:.2f} km²\n"
                            text += f"- Center: {lat}, {lon}\n\n"
                            text += "✅ This simplified polygon is optimized for SkyFi searches.\n\n"
                            text += f"💡 For exact boundaries, use `simplify=False` parameter (may cause API errors)."
                            return [TextContent(type="text", text=text)]
                    
                    # If polygon is too complex, simplify it
                    if original_points > 25 or original_size > 2000:
                        if simplify:
                            simplified_wkt = adaptive_simplify_wkt(wkt, max_bytes=3000)
                            simplified_points = len(parse_wkt_polygon(simplified_wkt))
                            
                            text = f"⚠️ **Complex Polygon Detected for '{display_name}'**\n\n"
                            text += f"Original polygon has {original_points} points ({original_size} bytes) - too complex for SkyFi API.\n"
                            text += f"Area: {area_km2:.2f} km²\n\n"
                            text += f"**Simplified polygon ({simplified_points} points):**\n```\n{simplified_wkt}\n```\n\n"
                            
                            # Also provide alternative approaches
                            text += "**Alternative approaches:**\n\n"
                            text += f"1. **Use a bounding box instead:**\n"
                            text += f"   Use `osm_generate_aoi` with center ({lat}, {lon}) and appropriate size\n\n"
                            text += f"2. **Create a simple polygon manually:**\n"
                            text += f"   For Central Park example: `POLYGON((-73.982 40.768, -73.947 40.768, -73.947 40.800, -73.982 40.800, -73.982 40.768))`\n\n"
                            text += f"3. **Search without exact boundaries:**\n"
                            text += f"   Many areas work well with simple rectangles that encompass the area of interest"
                            
                            return [TextContent(type="text", text=text)]
                        else:
                            # Return original with warning
                            text = f"⚠️ **Warning: Complex Polygon**\n\n"
                            text += f"'{display_name}' has {original_points} points which may cause API errors.\n"
                            text += f"Consider using `simplify=True` parameter or using `osm_generate_aoi` instead.\n\n"
                            text += f"Original WKT:\n{wkt}"
                            return [TextContent(type="text", text=text)]
                    
                    # Polygon is simple enough
                    text = f"✅ **WKT Polygon for '{display_name}':**\n\n"
                    text += f"```\n{wkt}\n```\n\n"
                    text += f"**Details:**\n"
                    text += f"- Points: {original_points}\n"
                    text += f"- Area: {area_km2:.2f} km²\n"
                    text += f"- Center: {lat}, {lon}\n\n"
                    text += "This polygon can be used directly with the skyfi_search_archives tool."
                    
                except Exception as e:
                    # If analysis fails, return original
                    text = f"WKT Polygon for '{display_name}':\n\n{wkt}\n\n"
                    text += "This polygon can be used directly with the skyfi_search_archives tool."
                
                return [TextContent(type="text", text=text)]
            
            else:
                # Try advanced OSM tools
                from .advanced_handlers import handle_advanced_osm_tool
                advanced_tools = [
                    "osm_batch_geocode", "osm_search_nearby_pois",
                    "osm_search_businesses", "osm_generate_aoi",
                    "osm_create_bounding_box", "osm_calculate_distance"
                ]
                
                if name in advanced_tools:
                    return await handle_advanced_osm_tool(name, arguments)
                
                raise ValueError(f"Unknown OSM tool: {name}")
    
    except httpx.RequestError as e:
        logger.error(f"Network error in OSM tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Network error: {str(e)}. Please check your internet connection."
        )]
    except Exception as e:
        logger.error(f"Error handling OSM tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]