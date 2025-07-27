"""Smart search functionality that handles common search patterns."""
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from ..utils.landmark_areas import get_landmark_bounds, suggest_size_for_landmark
from ..utils.area_calculator import calculate_wkt_area_km2

logger = logging.getLogger(__name__)

def create_bounding_box_wkt(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> str:
    """Create a simple bounding box WKT."""
    return f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"

def expand_bounds(bounds: Tuple[float, float, float, float], factor: float = 1.2) -> Tuple[float, float, float, float]:
    """Expand bounds by a factor."""
    min_lon, min_lat, max_lon, max_lat = bounds
    
    # Calculate center and spans
    center_lon = (min_lon + max_lon) / 2
    center_lat = (min_lat + max_lat) / 2
    span_lon = (max_lon - min_lon) * factor / 2
    span_lat = (max_lat - min_lat) * factor / 2
    
    return (
        center_lon - span_lon,
        center_lat - span_lat,
        center_lon + span_lon,
        center_lat + span_lat
    )

def smart_aoi_from_query(query: str) -> Optional[str]:
    """
    Try to intelligently create an AOI from a search query.
    
    Args:
        query: Natural language search query
        
    Returns:
        WKT polygon or None if cannot determine
    """
    query_lower = query.lower().strip()
    
    # Check for known landmarks
    bounds = get_landmark_bounds(query_lower)
    if bounds:
        # Slightly expand landmark bounds for better coverage
        expanded = expand_bounds(bounds, factor=1.1)
        return create_bounding_box_wkt(*expanded)
    
    # Check for coordinate patterns
    import re
    coord_pattern = r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)'
    matches = re.findall(coord_pattern, query)
    if matches and len(matches) >= 2:
        # Found coordinates, create bounding box
        lons = [float(m[0]) for m in matches]
        lats = [float(m[1]) for m in matches]
        return create_bounding_box_wkt(min(lons), min(lats), max(lons), max(lats))
    
    return None

def suggest_search_improvements(aoi: str, error_message: str = None) -> str:
    """
    Suggest improvements for a failed search.
    
    Args:
        aoi: The AOI that was used
        error_message: Error message if available
        
    Returns:
        Helpful suggestions
    """
    suggestions = []
    
    # Check if polygon is too complex
    if "422" in str(error_message) or "Unprocessable" in str(error_message):
        suggestions.append("The polygon is too complex. Try:")
        suggestions.append("• Use osm_generate_aoi to create a simple shape")
        suggestions.append("• Manually create a simple bounding box")
        suggestions.append("• Search for a smaller area")
    
    # Check area size
    try:
        area = calculate_wkt_area_km2(aoi)
        if area < 5:
            suggestions.append(f"Area is {area:.1f} km² (minimum for ordering is 5 km²)")
        elif area > 10000:
            suggestions.append(f"Area is {area:.0f} km² - consider searching smaller regions")
    except:
        pass
    
    if not suggestions:
        suggestions.append("Try adjusting your search parameters or area")
    
    return "\n".join(suggestions)

def format_search_summary(request: Dict[str, Any], results: list) -> str:
    """
    Format a nice summary of search results.
    
    Args:
        request: The search request parameters
        results: List of archive results
        
    Returns:
        Formatted summary text
    """
    if not results:
        return "No images found for the specified criteria."
    
    # Group by date
    by_date = {}
    for archive in results:
        date = archive.get('captureTimestamp', 'Unknown')[:10]
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(archive)
    
    summary = f"Found {len(results)} satellite images:\n\n"
    
    # Show summary by date
    for date in sorted(by_date.keys(), reverse=True):
        archives = by_date[date]
        summary += f"📅 **{date}**: {len(archives)} images\n"
        
        # Show best image for this date
        best = min(archives, key=lambda x: x.get('cloudCoveragePercent', 100))
        summary += f"   Best: {best.get('satellite', 'Unknown')} - "
        summary += f"{best.get('cloudCoveragePercent', 0):.1f}% clouds"
        
        if best.get('openData'):
            summary += " (FREE)"
        else:
            price = best.get('priceForOneSquareKm', 0)
            if price > 0:
                summary += f" (${price}/km²)"
        
        summary += "\n"
    
    return summary