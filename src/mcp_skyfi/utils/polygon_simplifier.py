"""Simplify WKT polygons to reduce points while preserving shape."""
import re
import math
from typing import List, Tuple, Optional


def parse_wkt_polygon(wkt: str) -> List[Tuple[float, float]]:
    """Parse WKT polygon string to list of (lon, lat) tuples."""
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


def coords_to_wkt(coords: List[Tuple[float, float]]) -> str:
    """Convert list of coordinates back to WKT polygon."""
    if not coords:
        return ""
    
    # Ensure polygon is closed
    if coords[0] != coords[-1]:
        coords = coords + [coords[0]]
    
    coord_strings = [f"{lon} {lat}" for lon, lat in coords]
    return f"POLYGON(({', '.join(coord_strings)}))"


def perpendicular_distance(point: Tuple[float, float], 
                         line_start: Tuple[float, float], 
                         line_end: Tuple[float, float]) -> float:
    """Calculate perpendicular distance from point to line segment."""
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    # If line start and end are the same, return distance to point
    if x1 == x2 and y1 == y2:
        return math.sqrt((x0 - x1)**2 + (y0 - y1)**2)
    
    # Calculate perpendicular distance
    numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
    denominator = math.sqrt((y2 - y1)**2 + (x2 - x1)**2)
    
    if denominator == 0:
        return 0
    
    return numerator / denominator


def douglas_peucker(coords: List[Tuple[float, float]], 
                   epsilon: float) -> List[Tuple[float, float]]:
    """
    Simplify polygon using Douglas-Peucker algorithm.
    
    Args:
        coords: List of (lon, lat) coordinates
        epsilon: Maximum distance threshold (in degrees)
    
    Returns:
        Simplified list of coordinates
    """
    if len(coords) <= 2:
        return coords
    
    # Find point with maximum distance from line between first and last
    max_distance = 0
    max_index = 0
    
    for i in range(1, len(coords) - 1):
        distance = perpendicular_distance(coords[i], coords[0], coords[-1])
        if distance > max_distance:
            max_distance = distance
            max_index = i
    
    # If max distance is greater than epsilon, recursively simplify
    if max_distance > epsilon:
        # Recursive simplification
        left_simplified = douglas_peucker(coords[:max_index + 1], epsilon)
        right_simplified = douglas_peucker(coords[max_index:], epsilon)
        
        # Combine results (avoiding duplicate point at index)
        return left_simplified[:-1] + right_simplified
    else:
        # All points between start and end can be removed
        return [coords[0], coords[-1]]


def simplify_wkt_polygon(wkt: str, 
                        tolerance: Optional[float] = None,
                        target_points: Optional[int] = None,
                        min_points: int = 4) -> str:
    """
    Simplify a WKT polygon to reduce the number of points.
    
    Args:
        wkt: WKT polygon string
        tolerance: Simplification tolerance in degrees (default: auto-calculated)
        target_points: Target number of points (used if tolerance not specified)
        min_points: Minimum number of points to keep
    
    Returns:
        Simplified WKT polygon string
    """
    try:
        coords = parse_wkt_polygon(wkt)
        original_count = len(coords)
        
        # Skip if already simple enough
        if original_count <= min_points:
            return wkt
        
        # Remove closing point for processing
        if coords[0] == coords[-1]:
            coords = coords[:-1]
        
        # Auto-calculate tolerance if not provided
        if tolerance is None:
            if target_points and target_points >= min_points:
                # Start with a small tolerance and increase until we reach target
                tolerance = 0.0001
                simplified = coords
                
                while len(simplified) > target_points and tolerance < 1.0:
                    simplified = douglas_peucker(coords, tolerance)
                    if len(simplified) <= target_points:
                        break
                    tolerance *= 2
            else:
                # Default tolerance based on coordinate span
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                span = max(max(lons) - min(lons), max(lats) - min(lats))
                tolerance = span / 1000  # 0.1% of span
        
        # Simplify
        simplified = douglas_peucker(coords, tolerance)
        
        # Ensure minimum points
        if len(simplified) < min_points:
            simplified = coords[:min_points]
        
        # Convert back to WKT
        result = coords_to_wkt(simplified)
        
        # Log simplification
        new_count = len(simplified)
        if new_count < original_count:
            reduction = (1 - new_count / original_count) * 100
            print(f"Simplified polygon: {original_count} → {new_count} points ({reduction:.1f}% reduction)")
        
        return result
        
    except Exception as e:
        # If simplification fails, return original
        print(f"Simplification failed: {e}")
        return wkt


def estimate_wkt_size(wkt: str) -> int:
    """Estimate the byte size of a WKT string."""
    return len(wkt.encode('utf-8'))


def adaptive_simplify_wkt(wkt: str, max_bytes: int = 5000) -> str:
    """
    Adaptively simplify WKT to stay under a byte limit.
    
    Args:
        wkt: WKT polygon string
        max_bytes: Maximum allowed size in bytes
    
    Returns:
        Simplified WKT that fits within the byte limit
    """
    current_size = estimate_wkt_size(wkt)
    
    if current_size <= max_bytes:
        return wkt
    
    # Try progressively more aggressive simplification
    coords = parse_wkt_polygon(wkt)
    original_points = len(coords)
    
    # Try different target point counts
    for factor in [0.5, 0.3, 0.2, 0.1, 0.05]:
        target = max(4, int(original_points * factor))
        simplified = simplify_wkt_polygon(wkt, target_points=target)
        
        if estimate_wkt_size(simplified) <= max_bytes:
            return simplified
    
    # Last resort: return a bounding box
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    
    bbox_wkt = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
    print(f"Warning: Simplified to bounding box due to size constraints")
    
    return bbox_wkt