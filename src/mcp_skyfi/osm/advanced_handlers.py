"""Handlers for advanced OSM operations."""
import logging
import json
import math
from typing import Any, Dict, List
import asyncio

from mcp.types import TextContent

from .client import OSMClient
from .advanced_tools import (
    haversine_distance, 
    create_polygon_wkt, 
    create_bounding_box_wkt
)

logger = logging.getLogger(__name__)


async def handle_advanced_osm_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle advanced OSM tool calls."""
    try:
        if name == "osm_batch_geocode":
            return await batch_geocode(arguments)
        elif name == "osm_search_nearby_pois":
            return await search_nearby_pois(arguments)
        elif name == "osm_search_businesses":
            return await search_businesses(arguments)
        elif name == "osm_generate_aoi":
            return await generate_aoi(arguments)
        elif name == "osm_create_bounding_box":
            return await create_bounding_box(arguments)
        elif name == "osm_calculate_distance":
            return await calculate_distance(arguments)
        else:
            raise ValueError(f"Unknown advanced OSM tool: {name}")
    except Exception as e:
        logger.error(f"Error handling advanced OSM tool {name}: {e}")
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def batch_geocode(arguments: Dict[str, Any]) -> List[TextContent]:
    """Batch geocode multiple locations."""
    locations = arguments["locations"]
    country_code = arguments.get("country_code")
    include_details = arguments.get("include_details", False)
    
    async with OSMClient() as client:
        # Process locations concurrently
        tasks = []
        for location in locations:
            task = client.geocode(
                location, 
                country_codes=[country_code] if country_code else None
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        text = f"📍 **Batch Geocoding Results**\n{'=' * 40}\n\n"
        
        success_count = 0
        for i, (location, result) in enumerate(zip(locations, results)):
            if isinstance(result, Exception):
                text += f"❌ **{location}**: Error - {str(result)}\n"
            elif result:
                success_count += 1
                text += f"✅ **{location}**:\n"
                text += f"   📍 Coordinates: {result['lat']}, {result['lon']}\n"
                text += f"   📮 Display: {result['display_name']}\n"
                
                if include_details and 'boundingbox' in result:
                    bbox = result['boundingbox']
                    text += f"   📦 Bounding Box: [{bbox[0]}, {bbox[2]}] to [{bbox[1]}, {bbox[3]}]\n"
                
                text += "\n"
            else:
                text += f"❓ **{location}**: No results found\n"
        
        text += f"\n📊 **Summary**: {success_count}/{len(locations)} locations geocoded successfully"
        
        # Create JSON output for easy parsing
        json_results = []
        for location, result in zip(locations, results):
            if not isinstance(result, Exception) and result:
                json_results.append({
                    "query": location,
                    "lat": float(result['lat']),
                    "lon": float(result['lon']),
                    "display_name": result['display_name']
                })
        
        if json_results:
            text += f"\n\n**JSON Output:**\n```json\n{json.dumps(json_results, indent=2)}\n```"
        
        return [TextContent(type="text", text=text)]


async def search_nearby_pois(arguments: Dict[str, Any]) -> List[TextContent]:
    """Search for POIs near a location."""
    lat = arguments["lat"]
    lon = arguments["lon"]
    radius_km = arguments.get("radius_km", 1.0)
    poi_types = arguments.get("poi_types", [])
    limit = arguments.get("limit", 20)
    
    async with OSMClient() as client:
        # Define OSM tags for each POI type
        poi_tags = {
            "restaurant": ["amenity=restaurant", "amenity=cafe", "amenity=fast_food"],
            "hotel": ["tourism=hotel", "tourism=motel", "tourism=guest_house"],
            "shop": ["shop=*"],
            "landmark": ["tourism=attraction", "historic=*", "tourism=viewpoint"],
            "park": ["leisure=park", "leisure=garden"],
            "hospital": ["amenity=hospital", "amenity=clinic"],
            "school": ["amenity=school", "amenity=university"],
            "bank": ["amenity=bank", "amenity=atm"],
            "fuel": ["amenity=fuel"],
            "parking": ["amenity=parking"]
        }
        
        # Build search query
        if poi_types:
            tags = []
            for poi_type in poi_types:
                tags.extend(poi_tags.get(poi_type, []))
        else:
            # Search all types
            tags = [tag for tag_list in poi_tags.values() for tag in tag_list]
        
        # Search for each tag type
        all_results = []
        for tag in tags[:5]:  # Limit to prevent too many requests
            try:
                results = await client.search(
                    tag,
                    viewbox=f"{lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}",
                    bounded=True,
                    limit=limit
                )
                
                # Filter by distance
                for result in results:
                    if 'lat' in result and 'lon' in result:
                        dist = haversine_distance(
                            lat, lon,
                            float(result['lat']), float(result['lon'])
                        )
                        if dist <= radius_km:
                            result['distance_km'] = dist
                            result['tag'] = tag
                            all_results.append(result)
            except:
                continue
        
        # Sort by distance
        all_results.sort(key=lambda x: x.get('distance_km', 999))
        
        # Format results
        text = f"🗺️ **Nearby Points of Interest**\n{'=' * 40}\n\n"
        text += f"📍 Center: {lat}, {lon}\n"
        text += f"🔍 Search Radius: {radius_km} km\n"
        
        if poi_types:
            text += f"🏷️ Types: {', '.join(poi_types)}\n"
        
        text += f"\n**Found {len(all_results)} POIs:**\n\n"
        
        # Group by type
        by_type = {}
        for result in all_results[:limit]:
            poi_type = result['tag'].split('=')[0]
            if poi_type not in by_type:
                by_type[poi_type] = []
            by_type[poi_type].append(result)
        
        for poi_type, items in by_type.items():
            text += f"\n**{poi_type.title()}:**\n"
            for item in items[:5]:  # Limit per category
                name = item.get('name', item.get('display_name', 'Unnamed'))
                dist = item.get('distance_km', 0)
                text += f"  • {name} ({dist:.2f} km)\n"
                text += f"    📍 {item['lat']}, {item['lon']}\n"
        
        return [TextContent(type="text", text=text)]


async def search_businesses(arguments: Dict[str, Any]) -> List[TextContent]:
    """Search for specific businesses."""
    query = arguments["query"]
    near = arguments["near"]
    radius_km = arguments.get("radius_km", 5.0)
    category = arguments.get("category")
    
    async with OSMClient() as client:
        # First geocode the location
        location_result = await client.geocode(near)
        if not location_result:
            return [TextContent(
                type="text",
                text=f"❌ Could not find location: {near}"
            )]
        
        center_lat = float(location_result['lat'])
        center_lon = float(location_result['lon'])
        
        # Search for businesses
        search_query = query
        if category:
            # Add category-specific tags
            category_tags = {
                "food": "amenity=restaurant OR amenity=cafe OR amenity=fast_food",
                "retail": "shop=*",
                "service": "office=* OR craft=*",
                "entertainment": "leisure=* OR tourism=*",
                "health": "amenity=hospital OR amenity=pharmacy OR amenity=clinic",
                "finance": "amenity=bank OR office=financial"
            }
            if category in category_tags:
                search_query = f"{query} AND ({category_tags[category]})"
        
        # Search with viewbox
        viewbox_size = radius_km / 111.32  # Approximate degrees
        results = await client.search(
            search_query,
            viewbox=f"{center_lon-viewbox_size},{center_lat-viewbox_size},{center_lon+viewbox_size},{center_lat+viewbox_size}",
            bounded=True,
            limit=50
        )
        
        # Filter by distance and relevance
        filtered_results = []
        for result in results:
            if 'lat' in result and 'lon' in result:
                dist = haversine_distance(
                    center_lat, center_lon,
                    float(result['lat']), float(result['lon'])
                )
                if dist <= radius_km:
                    result['distance_km'] = dist
                    filtered_results.append(result)
        
        # Sort by distance
        filtered_results.sort(key=lambda x: x['distance_km'])
        
        text = f"🏢 **Business Search Results**\n{'=' * 40}\n\n"
        text += f"🔍 Query: '{query}'\n"
        text += f"📍 Near: {near} ({center_lat:.4f}, {center_lon:.4f})\n"
        text += f"📏 Radius: {radius_km} km\n"
        if category:
            text += f"🏷️ Category: {category}\n"
        
        text += f"\n**Found {len(filtered_results)} businesses:**\n\n"
        
        for i, result in enumerate(filtered_results[:20], 1):
            name = result.get('name', result.get('display_name', 'Unknown'))
            address = result.get('display_name', '')
            dist = result['distance_km']
            
            text += f"{i}. **{name}**\n"
            text += f"   📍 {result['lat']}, {result['lon']} ({dist:.2f} km away)\n"
            
            # Extract business type
            if 'type' in result:
                text += f"   🏷️ Type: {result['type']}\n"
            
            # Show partial address
            if address and address != name:
                parts = address.split(',')
                if len(parts) > 1:
                    text += f"   📮 {', '.join(parts[1:3])}\n"
            
            text += "\n"
        
        return [TextContent(type="text", text=text)]


async def generate_aoi(arguments: Dict[str, Any]) -> List[TextContent]:
    """Generate an AOI polygon."""
    center = arguments["center"]
    shape = arguments.get("shape", "square")
    size_km = arguments.get("size_km", 1.0)
    aspect_ratio = arguments.get("aspect_ratio", 1.0)
    
    center_lat = center["lat"]
    center_lon = center["lon"]
    
    # Generate WKT polygon
    wkt = create_polygon_wkt(center_lat, center_lon, shape, size_km, aspect_ratio)
    
    # Calculate actual area
    from ..utils.area_calculator import calculate_wkt_area_km2
    actual_area = calculate_wkt_area_km2(wkt)
    
    text = f"🎯 **Generated Area of Interest**\n{'=' * 40}\n\n"
    text += f"📍 Center: {center_lat}, {center_lon}\n"
    text += f"🔷 Shape: {shape}\n"
    text += f"📏 Size: {size_km} km"
    if shape == "rectangle" and aspect_ratio != 1.0:
        text += f" (aspect ratio: {aspect_ratio})"
    text += f"\n📐 Actual Area: {actual_area:.2f} km²\n"
    
    text += f"\n**WKT Polygon:**\n```\n{wkt}\n```\n"
    
    # Visual representation
    text += f"\n**Visual Preview:**\n"
    if shape == "circle":
        text += "     ⭕\n"
    elif shape == "square":
        text += "     ⬜\n"
    elif shape == "rectangle":
        text += "     ▭\n" if aspect_ratio > 1 else "     ▯\n"
    elif shape == "hexagon":
        text += "     ⬡\n"
    
    text += f"\n💡 Use this WKT in skyfi_search_archives to search for satellite imagery"
    
    # Add area warning if needed
    if actual_area < 5.0:
        text += f"\n\n⚠️ Note: This area is {actual_area:.2f} km², which is below the 5 km² minimum for orders."
        text += f"\n   The polygon will be automatically expanded when ordering."
    
    return [TextContent(type="text", text=text)]


async def create_bounding_box(arguments: Dict[str, Any]) -> List[TextContent]:
    """Create a bounding box from points."""
    points = arguments["points"]
    padding_km = arguments.get("padding_km", 0)
    output_format = arguments.get("output_format", "wkt")
    
    # Validate points
    if len(points) < 2:
        return [TextContent(
            type="text",
            text="❌ At least 2 points required to create a bounding box"
        )]
    
    # Calculate bounds
    lats = [p["lat"] for p in points]
    lons = [p["lon"] for p in points]
    
    min_lat = min(lats)
    max_lat = max(lats)
    min_lon = min(lons)
    max_lon = max(lons)
    
    # Create WKT
    wkt = create_bounding_box_wkt(points, padding_km)
    
    # Calculate area
    from ..utils.area_calculator import calculate_wkt_area_km2
    area_km2 = calculate_wkt_area_km2(wkt)
    
    text = f"📦 **Bounding Box Created**\n{'=' * 40}\n\n"
    text += f"📍 Points included: {len(points)}\n"
    text += f"📏 Bounds:\n"
    text += f"   • Latitude: {min_lat:.6f} to {max_lat:.6f}\n"
    text += f"   • Longitude: {min_lon:.6f} to {max_lon:.6f}\n"
    
    if padding_km > 0:
        text += f"🔲 Padding: {padding_km} km added\n"
    
    text += f"📐 Total Area: {area_km2:.2f} km²\n"
    
    # Output in requested format
    if output_format == "wkt":
        text += f"\n**WKT Output:**\n```\n{wkt}\n```"
    elif output_format == "geojson":
        geojson = {
            "type": "Polygon",
            "coordinates": [[
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat]
            ]]
        }
        text += f"\n**GeoJSON Output:**\n```json\n{json.dumps(geojson, indent=2)}\n```"
    elif output_format == "bounds":
        bounds = {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon
        }
        text += f"\n**Bounds Output:**\n```json\n{json.dumps(bounds, indent=2)}\n```"
    
    # Calculate distances between points
    text += f"\n\n**Point Distances:**\n"
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            dist = haversine_distance(
                points[i]["lat"], points[i]["lon"],
                points[j]["lat"], points[j]["lon"]
            )
            text += f"  • Point {i+1} to Point {j+1}: {dist:.2f} km\n"
    
    return [TextContent(type="text", text=text)]


async def calculate_distance(arguments: Dict[str, Any]) -> List[TextContent]:
    """Calculate distance between two points."""
    from_point = arguments["from"]
    to_point = arguments["to"]
    method = arguments.get("method", "haversine")
    unit = arguments.get("unit", "km")
    
    from_lat = from_point["lat"]
    from_lon = from_point["lon"]
    to_lat = to_point["lat"]
    to_lon = to_point["lon"]
    
    # Calculate distance in km
    if method == "haversine" or method == "great_circle":
        distance_km = haversine_distance(from_lat, from_lon, to_lat, to_lon)
    elif method == "vincenty":
        # For simplicity, use haversine (Vincenty is more complex)
        distance_km = haversine_distance(from_lat, from_lon, to_lat, to_lon)
        method += " (approximated with haversine)"
    else:
        distance_km = haversine_distance(from_lat, from_lon, to_lat, to_lon)
    
    # Convert units
    conversions = {
        "km": distance_km,
        "miles": distance_km * 0.621371,
        "meters": distance_km * 1000,
        "feet": distance_km * 3280.84
    }
    
    distance = conversions[unit]
    
    # Calculate bearing
    lat1_rad = math.radians(from_lat)
    lat2_rad = math.radians(to_lat)
    delta_lon = math.radians(to_lon - from_lon)
    
    x = math.sin(delta_lon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    bearing = math.degrees(math.atan2(x, y))
    bearing = (bearing + 360) % 360  # Normalize to 0-360
    
    # Get compass direction
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = int((bearing + 11.25) / 22.5) % 16
    compass = directions[index]
    
    text = f"📏 **Distance Calculation**\n{'=' * 40}\n\n"
    text += f"**From:** {from_lat:.6f}, {from_lon:.6f}\n"
    text += f"**To:** {to_lat:.6f}, {to_lon:.6f}\n"
    text += f"**Method:** {method}\n\n"
    
    text += f"**Distance:** {distance:.2f} {unit}\n\n"
    
    text += f"**Other Units:**\n"
    for u, val in conversions.items():
        if u != unit:
            text += f"  • {val:.2f} {u}\n"
    
    text += f"\n**Bearing:** {bearing:.1f}° ({compass})\n"
    
    # Add context
    text += f"\n**Context:**\n"
    if distance_km < 1:
        text += "  • Walking distance (~12 min walk)\n"
    elif distance_km < 5:
        text += "  • Short drive (~10 min by car)\n"
    elif distance_km < 50:
        text += "  • Medium drive (~45 min by car)\n"
    else:
        text += f"  • Long distance (~{distance_km/100:.1f} hours by car)\n"
    
    # Satellite imagery context
    if distance_km < 2:
        text += "  • Can be covered in a single high-res satellite image\n"
    elif distance_km < 10:
        text += "  • Requires 1-2 satellite images for complete coverage\n"
    else:
        text += "  • Requires multiple satellite images for complete coverage\n"
    
    return [TextContent(type="text", text=text)]