"""Calculate area of WKT polygons."""
import re
from typing import List, Tuple
import math


def parse_wkt_polygon(wkt: str) -> List[Tuple[float, float]]:
    """Parse WKT polygon string to list of (lon, lat) tuples."""
    # Extract coordinates from POLYGON((x1 y1, x2 y2, ...))
    match = re.match(r'POLYGON\s*\(\((.*)\)\)', wkt.strip())
    if not match:
        raise ValueError(f"Invalid WKT polygon format: {wkt}")
    
    coords_str = match.group(1)
    coords = []
    
    for coord_pair in coords_str.split(','):
        parts = coord_pair.strip().split()
        if len(parts) == 2:
            lon, lat = float(parts[0]), float(parts[1])
            coords.append((lon, lat))
    
    return coords


def calculate_polygon_area_km2(coords: List[Tuple[float, float]]) -> float:
    """
    Calculate area of polygon in square kilometers using shoelace formula.
    Assumes coordinates are in degrees (lon, lat).
    """
    if len(coords) < 3:
        return 0.0
    
    # Convert to radians and project to meters
    earth_radius_km = 6371.0
    
    # Calculate centroid for better accuracy
    centroid_lon = sum(c[0] for c in coords) / len(coords)
    centroid_lat = sum(c[1] for c in coords) / len(coords)
    
    # Convert to projected coordinates (simple equirectangular)
    # This is approximate but good enough for small areas
    projected = []
    for lon, lat in coords:
        x = (lon - centroid_lon) * math.cos(math.radians(centroid_lat)) * earth_radius_km * math.pi / 180
        y = (lat - centroid_lat) * earth_radius_km * math.pi / 180
        projected.append((x, y))
    
    # Shoelace formula
    area = 0.0
    n = len(projected)
    for i in range(n):
        j = (i + 1) % n
        area += projected[i][0] * projected[j][1]
        area -= projected[j][0] * projected[i][1]
    
    return abs(area) / 2.0


def calculate_wkt_area_km2(wkt: str) -> float:
    """Calculate area of WKT polygon in square kilometers."""
    coords = parse_wkt_polygon(wkt)
    return calculate_polygon_area_km2(coords)


def expand_polygon_to_minimum_area(wkt: str, min_area_km2: float = 5.0) -> str:
    """
    Expand a polygon to meet minimum area requirement.
    Expands from centroid to maintain shape.
    """
    coords = parse_wkt_polygon(wkt)
    current_area = calculate_polygon_area_km2(coords)
    
    if current_area >= min_area_km2:
        return wkt  # No expansion needed
    
    # Calculate expansion factor
    # Area scales with square of linear dimensions
    expansion_factor = math.sqrt(min_area_km2 / current_area)
    
    # Find centroid
    centroid_lon = sum(c[0] for c in coords) / len(coords)
    centroid_lat = sum(c[1] for c in coords) / len(coords)
    
    # Expand each point from centroid
    expanded_coords = []
    for lon, lat in coords:
        # Vector from centroid to point
        dx = lon - centroid_lon
        dy = lat - centroid_lat
        
        # Expand the vector
        new_lon = centroid_lon + dx * expansion_factor
        new_lat = centroid_lat + dy * expansion_factor
        
        expanded_coords.append(f"{new_lon} {new_lat}")
    
    # Reconstruct WKT
    coords_str = ", ".join(expanded_coords)
    return f"POLYGON(({coords_str}))"


def adjust_price_for_minimum_area(
    price_per_km2: float, 
    actual_area_km2: float, 
    min_area_km2: float = 25.0
) -> Tuple[float, float, str]:
    """
    Adjust price based on minimum area requirement.
    
    Returns:
        (adjusted_price, billed_area, explanation)
    """
    if actual_area_km2 >= min_area_km2:
        return price_per_km2 * actual_area_km2, actual_area_km2, ""
    
    # Must pay for minimum area
    adjusted_price = price_per_km2 * min_area_km2
    explanation = (
        f"Note: Minimum order size is {min_area_km2} km². "
        f"Your area is {actual_area_km2:.1f} km², but you'll be charged for {min_area_km2} km²."
    )
    return adjusted_price, min_area_km2, explanation