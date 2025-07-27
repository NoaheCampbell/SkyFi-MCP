"""Advanced OpenStreetMap tools for SkyFi MCP."""
import logging
from typing import Any, Dict, List, Optional
import asyncio
import math

from mcp.types import Tool

logger = logging.getLogger(__name__)


async def register_advanced_osm_tools() -> List[Tool]:
    """Register advanced OSM tools."""
    return [
        Tool(
            name="osm_generate_aoi",
            description=(
                "Generate an Area of Interest (AOI) polygon around a location. "
                "Creates various shapes (circle, square, custom) for satellite imagery search."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "center": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lon": {"type": "number"}
                        },
                        "description": "Center point of the AOI"
                    },
                    "shape": {
                        "type": "string",
                        "description": "Shape of the AOI",
                        "enum": ["circle", "square", "rectangle", "hexagon"],
                        "default": "square"
                    },
                    "size_km": {
                        "type": "number",
                        "description": "Size in kilometers (radius for circle, side for square)",
                        "default": 1.0
                    },
                    "aspect_ratio": {
                        "type": "number",
                        "description": "Width/height ratio for rectangle shape",
                        "default": 1.0
                    }
                },
                "required": ["center"]
            }
        ),
        Tool(
            name="osm_calculate_distance",
            description=(
                "Calculate distance between two geographic points. "
                "Supports multiple calculation methods for different use cases."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "from": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lon": {"type": "number"}
                        },
                        "description": "Starting point"
                    },
                    "to": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lon": {"type": "number"}
                        },
                        "description": "Ending point"
                    },
                    "method": {
                        "type": "string",
                        "description": "Distance calculation method",
                        "enum": ["haversine", "vincenty", "great_circle"],
                        "default": "haversine"
                    },
                    "unit": {
                        "type": "string",
                        "description": "Output unit",
                        "enum": ["km", "miles", "meters", "feet"],
                        "default": "km"
                    }
                },
                "required": ["from", "to"]
            }
        )
    ]


# Utility functions for calculations

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula (km)."""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def create_polygon_wkt(center_lat: float, center_lon: float, shape: str, size_km: float, aspect_ratio: float = 1.0) -> str:
    """Create a WKT polygon of specified shape around a center point."""
    # Approximate degrees per km
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(center_lat))
    
    if shape == "circle":
        # Approximate circle with 32-sided polygon
        points = []
        for i in range(32):
            angle = 2 * math.pi * i / 32
            lat_offset = (size_km * math.sin(angle)) / km_per_deg_lat
            lon_offset = (size_km * math.cos(angle)) / km_per_deg_lon
            points.append(f"{center_lon + lon_offset} {center_lat + lat_offset}")
        points.append(points[0])  # Close the polygon
        
    elif shape == "square":
        half_size_lat = size_km / (2 * km_per_deg_lat)
        half_size_lon = size_km / (2 * km_per_deg_lon)
        points = [
            f"{center_lon - half_size_lon} {center_lat - half_size_lat}",
            f"{center_lon + half_size_lon} {center_lat - half_size_lat}",
            f"{center_lon + half_size_lon} {center_lat + half_size_lat}",
            f"{center_lon - half_size_lon} {center_lat + half_size_lat}",
            f"{center_lon - half_size_lon} {center_lat - half_size_lat}"
        ]
        
    elif shape == "rectangle":
        half_width = (size_km * math.sqrt(aspect_ratio)) / (2 * km_per_deg_lon)
        half_height = (size_km / math.sqrt(aspect_ratio)) / (2 * km_per_deg_lat)
        points = [
            f"{center_lon - half_width} {center_lat - half_height}",
            f"{center_lon + half_width} {center_lat - half_height}",
            f"{center_lon + half_width} {center_lat + half_height}",
            f"{center_lon - half_width} {center_lat + half_height}",
            f"{center_lon - half_width} {center_lat - half_height}"
        ]
        
    elif shape == "hexagon":
        points = []
        for i in range(6):
            angle = math.pi / 3 * i
            lat_offset = (size_km * math.sin(angle)) / km_per_deg_lat
            lon_offset = (size_km * math.cos(angle)) / km_per_deg_lon
            points.append(f"{center_lon + lon_offset} {center_lat + lat_offset}")
        points.append(points[0])
        
    else:
        # Default to square
        return create_polygon_wkt(center_lat, center_lon, "square", size_km)
    
    return f"POLYGON(({', '.join(points)}))"


def create_bounding_box_wkt(points: List[Dict[str, float]], padding_km: float = 0) -> str:
    """Create a bounding box WKT from a list of points."""
    if not points or len(points) < 2:
        raise ValueError("At least 2 points required for bounding box")
    
    lats = [p["lat"] for p in points]
    lons = [p["lon"] for p in points]
    
    min_lat = min(lats)
    max_lat = max(lats)
    min_lon = min(lons)
    max_lon = max(lons)
    
    if padding_km > 0:
        # Add padding
        center_lat = (min_lat + max_lat) / 2
        km_per_deg_lat = 111.32
        km_per_deg_lon = 111.32 * math.cos(math.radians(center_lat))
        
        lat_padding = padding_km / km_per_deg_lat
        lon_padding = padding_km / km_per_deg_lon
        
        min_lat -= lat_padding
        max_lat += lat_padding
        min_lon -= lon_padding
        max_lon += lon_padding
    
    # Create WKT polygon
    coords = [
        f"{min_lon} {min_lat}",
        f"{max_lon} {min_lat}",
        f"{max_lon} {max_lat}",
        f"{min_lon} {max_lat}",
        f"{min_lon} {min_lat}"
    ]
    
    return f"POLYGON(({', '.join(coords)}))"