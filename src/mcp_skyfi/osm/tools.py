"""OpenStreetMap tool definitions for MCP."""
from typing import List

from mcp.types import Tool


async def register_osm_tools() -> List[Tool]:
    """Register OSM tools with the MCP server."""
    return [
        Tool(
            name="osm_geocode",
            description="Convert address or place name to coordinates",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Address or place name to geocode (e.g., 'Eiffel Tower, Paris')"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 50,
                        "description": "Maximum number of results to return"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="osm_reverse_geocode",
            description="Convert coordinates to address",
            inputSchema={
                "type": "object",
                "properties": {
                    "lat": {
                        "type": "number",
                        "description": "Latitude"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Longitude"
                    },
                    "zoom": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 18,
                        "default": 18,
                        "description": "Zoom level for detail (higher = more detail)"
                    }
                },
                "required": ["lat", "lon"]
            }
        ),
        Tool(
            name="osm_polygon_to_wkt",
            description="Convert place name to WKT polygon for use with SkyFi API",
            inputSchema={
                "type": "object",
                "properties": {
                    "place": {
                        "type": "string",
                        "description": "Place name to get boundary polygon (e.g., 'Manhattan, New York')"
                    },
                    "simplify": {
                        "type": "boolean",
                        "default": True,
                        "description": "Simplify polygon to reduce complexity"
                    }
                },
                "required": ["place"]
            }
        ),
    ]