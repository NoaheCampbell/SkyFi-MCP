"""Weather tool definitions for MCP."""
from typing import List

from mcp.types import Tool


async def register_weather_tools() -> List[Tool]:
    """Register weather tools with the MCP server."""
    return [
        Tool(
            name="weather_current",
            description="Get current weather conditions for a location",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location name (e.g., 'San Francisco, CA')"
                    },
                    "lat": {
                        "type": "number",
                        "description": "Latitude (use with lon instead of location)"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Longitude (use with lat instead of location)"
                    }
                },
                "oneOf": [
                    {"required": ["location"]},
                    {"required": ["lat", "lon"]}
                ]
            }
        ),
        Tool(
            name="weather_forecast",
            description="Get weather forecast for the next few days",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location name"
                    },
                    "lat": {
                        "type": "number",
                        "description": "Latitude"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Longitude"
                    },
                    "days": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 7,
                        "default": 3,
                        "description": "Number of days to forecast"
                    }
                },
                "oneOf": [
                    {"required": ["location"]},
                    {"required": ["lat", "lon"]}
                ]
            }
        ),
    ]