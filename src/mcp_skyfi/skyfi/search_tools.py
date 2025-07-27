"""Additional search tools for SkyFi."""
from typing import List
from mcp.types import Tool

def register_search_tools() -> List[Tool]:
    """Register additional search tools."""
    return [
        Tool(
            name="skyfi_search_exact",
            description=(
                "Search for satellite imagery using exact coordinates or polygon. "
                "This tool bypasses automatic simplification and uses your exact polygon as-is. "
                "Use this when you need precise boundaries, but be aware that complex polygons may fail."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "polygon": {
                        "type": "string",
                        "description": "Exact WKT polygon or list of coordinates"
                    },
                    "fromDate": {
                        "type": "string",
                        "description": "Start date (ISO format or natural language)"
                    },
                    "toDate": {
                        "type": "string",
                        "description": "End date (ISO format or natural language)"
                    },
                    "resolution": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"],
                        "description": "Desired resolution level",
                        "default": "LOW"
                    },
                    "simplify_if_needed": {
                        "type": "boolean",
                        "description": "If true, will simplify polygon only if API rejects it",
                        "default": False
                    }
                },
                "required": ["polygon", "fromDate", "toDate"]
            }
        ),
        Tool(
            name="skyfi_search_bbox",
            description=(
                "Search for satellite imagery using a simple bounding box. "
                "Provide min/max coordinates to create a rectangular search area. "
                "This is the most reliable way to search and never fails due to complexity."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "min_lon": {
                        "type": "number",
                        "description": "Minimum longitude (western edge)"
                    },
                    "min_lat": {
                        "type": "number",
                        "description": "Minimum latitude (southern edge)"
                    },
                    "max_lon": {
                        "type": "number",
                        "description": "Maximum longitude (eastern edge)"
                    },
                    "max_lat": {
                        "type": "number",
                        "description": "Maximum latitude (northern edge)"
                    },
                    "fromDate": {
                        "type": "string",
                        "description": "Start date"
                    },
                    "toDate": {
                        "type": "string",
                        "description": "End date"
                    },
                    "resolution": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"],
                        "default": "LOW"
                    }
                },
                "required": ["min_lon", "min_lat", "max_lon", "max_lat", "fromDate", "toDate"]
            }
        )
    ]