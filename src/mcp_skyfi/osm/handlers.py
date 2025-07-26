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