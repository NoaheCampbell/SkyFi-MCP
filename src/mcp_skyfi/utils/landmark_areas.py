"""Common landmark areas with pre-defined search boundaries."""

# Common landmarks with their approximate bounding boxes
# Format: name -> (min_lon, min_lat, max_lon, max_lat)
LANDMARK_BOUNDS = {
    # New York
    "central park": (-73.982, 40.764, -73.949, 40.801),
    "manhattan": (-74.019, 40.698, -73.907, 40.882),
    "times square": (-73.991, 40.754, -73.984, 40.761),
    "statue of liberty": (-74.049, 40.687, -74.040, 40.694),
    "brooklyn bridge": (-73.998, 40.702, -73.989, 40.712),
    "one world trade center": (-74.016, 40.709, -74.011, 40.714),
    
    # San Francisco
    "golden gate bridge": (-122.483, 37.807, -122.469, 37.833),
    "alcatraz": (-122.427, 37.824, -122.420, 37.830),
    "golden gate park": (-122.511, 37.765, -122.453, 37.774),
    "fishermans wharf": (-122.424, 37.805, -122.410, 37.812),
    
    # Washington DC
    "white house": (-77.040, 38.895, -77.034, 38.900),
    "capitol building": (-77.012, 38.887, -77.006, 38.892),
    "lincoln memorial": (-77.053, 38.887, -77.048, 38.891),
    "washington monument": (-77.037, 38.887, -77.033, 38.891),
    "national mall": (-77.053, 38.882, -77.010, 38.894),
    
    # Chicago
    "millennium park": (-87.624, 41.881, -87.619, 41.884),
    "navy pier": (-87.609, 41.890, -87.596, 41.894),
    "willis tower": (-87.638, 41.877, -87.634, 41.880),
    
    # Los Angeles
    "hollywood sign": (-118.324, 34.131, -118.319, 34.136),
    "griffith observatory": (-118.302, 34.116, -118.298, 34.120),
    "santa monica pier": (-118.500, 34.007, -118.494, 34.012),
    "dodger stadium": (-118.242, 34.070, -118.236, 34.076),
    
    # International
    "eiffel tower": (2.292, 48.855, 2.297, 48.860),
    "arc de triomphe": (2.293, 48.871, 2.298, 48.875),
    "louvre": (2.334, 48.859, 2.340, 48.863),
    "big ben": (-0.127, 51.499, -0.123, 51.502),
    "buckingham palace": (-0.144, 51.499, -0.139, 51.503),
    "tower bridge": (-0.078, 51.504, -0.073, 51.507),
    "colosseum": (12.490, 41.889, 12.494, 41.892),
    "vatican": (12.451, 41.901, 12.459, 41.908),
    "sydney opera house": (151.213, -33.859, 151.217, -33.855),
    "tokyo tower": (139.743, 35.656, 139.747, 35.660),
    "forbidden city": (116.388, 39.913, 116.402, 39.925),
    "taj mahal": (78.040, 27.172, 78.044, 27.176),
}

def get_landmark_bounds(query: str) -> tuple:
    """
    Get pre-defined bounds for a landmark.
    
    Args:
        query: Search query
        
    Returns:
        Tuple of (min_lon, min_lat, max_lon, max_lat) or None if not found
    """
    query_lower = query.lower().strip()
    
    # Check exact match first
    if query_lower in LANDMARK_BOUNDS:
        return LANDMARK_BOUNDS[query_lower]
    
    # Check partial matches
    for landmark, bounds in LANDMARK_BOUNDS.items():
        if landmark in query_lower or query_lower in landmark:
            return bounds
    
    return None

def landmark_to_wkt(query: str) -> str:
    """
    Convert a landmark query to a WKT polygon.
    
    Args:
        query: Landmark name
        
    Returns:
        WKT polygon string or empty string if not found
    """
    bounds = get_landmark_bounds(query)
    if not bounds:
        return ""
    
    min_lon, min_lat, max_lon, max_lat = bounds
    
    # Create WKT polygon from bounds
    wkt = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
    
    return wkt

def suggest_size_for_landmark(query: str) -> float:
    """
    Suggest an appropriate AOI size for a landmark.
    
    Args:
        query: Landmark name
        
    Returns:
        Suggested size in km
    """
    query_lower = query.lower().strip()
    
    # Large areas
    if any(term in query_lower for term in ["city", "manhattan", "national mall", "golden gate park"]):
        return 5.0
    
    # Medium areas
    if any(term in query_lower for term in ["park", "bridge", "stadium", "pier"]):
        return 2.0
    
    # Small areas
    if any(term in query_lower for term in ["tower", "building", "monument", "memorial"]):
        return 1.0
    
    # Default
    return 2.0