# Polygon Optimization for SkyFi MCP Server

## Problem
The SkyFi API returns a 422 error when polygons have too many points (typically > 50 points or > 4000 bytes). This commonly happens when searching for places like "Central Park" which returns detailed boundary polygons with hundreds of points.

## Solution
We've implemented several optimization strategies:

### 1. Automatic Landmark Detection
For known landmarks, we use pre-defined bounding boxes instead of complex polygons:

```python
# When searching for "Central Park"
# Instead of 215-point polygon, returns:
POLYGON((-73.982 40.764, -73.949 40.764, -73.949 40.801, -73.982 40.801, -73.982 40.764))
```

Supported landmarks include:
- Major parks (Central Park, Golden Gate Park)
- Famous buildings (Empire State Building, White House)
- Bridges (Brooklyn Bridge, Golden Gate Bridge)
- International landmarks (Eiffel Tower, Colosseum, etc.)

### 2. Automatic Polygon Simplification
When polygons are too complex:
- Detects polygons with > 50 points or > 4000 bytes
- Uses Douglas-Peucker algorithm to simplify
- Maintains shape while reducing points by up to 98%
- Falls back to bounding box if needed

### 3. Better Error Messages
When a 422 error occurs, provides helpful guidance:
- Shows polygon complexity (number of points, area)
- Suggests using `osm_generate_aoi` for simple shapes
- Provides example polygons for common areas
- Explains the issue clearly

### 4. Alternative Tools
Enhanced `osm_generate_aoi` for creating simple shapes:
- Circles, squares, rectangles, hexagons
- Customizable size and aspect ratio
- Always produces API-compatible polygons

## New Search Tools

### skyfi_search_exact
Use this when you have exact coordinates and don't want automatic simplification:
```python
skyfi_search_exact(
    polygon="POLYGON((-73.9814 40.7685, -73.9814 40.7686, ...))",  # Your exact polygon
    fromDate="last week",
    toDate="today",
    simplify_if_needed=True  # Only simplify if API rejects it
)
```

### skyfi_search_bbox  
The most reliable search method using simple bounding box:
```python
skyfi_search_bbox(
    min_lon=-73.982,
    min_lat=40.764,
    max_lon=-73.949,
    max_lat=40.801,
    fromDate="last week",
    toDate="today"
)
```

## Usage Examples

### Good: Using Simple Shapes
```python
# Get coordinates
osm_geocode("Central Park")
# Returns: 40.7827725, -73.9653627

# Create simple rectangle
osm_generate_aoi(
    center={"lat": 40.7827725, "lon": -73.9653627},
    shape="rectangle",
    size_km=3,
    aspect_ratio=1.5
)
```

### Good: Using Landmark Detection
```python
osm_polygon_to_wkt("Central Park")
# Automatically returns simplified 5-point polygon
```

### Good: Manual Simple Polygon
```python
skyfi_search_archives(
    aoi="POLYGON((-73.982 40.764, -73.949 40.764, -73.949 40.801, -73.982 40.801, -73.982 40.764))",
    fromDate="2 weeks ago",
    toDate="today"
)
```

### Bad: Using Complex Polygon
```python
# Don't use the full 215-point Central Park boundary
# Will fail with 422 error
```

## Technical Details

### Polygon Complexity Limits
- Maximum points: ~25 (automatic simplification threshold)
- Maximum size: ~2000 bytes (automatic simplification threshold)
- API accepts: Simple polygons (4-25 points)
- User-provided exact polygons are respected (use `skyfi_search_exact`)

### Simplification Algorithm
- Douglas-Peucker line simplification
- Adaptive tolerance based on target size
- Preserves area and general shape
- Falls back to bounding box if needed

### Pre-defined Landmarks
Located in `src/mcp_skyfi/utils/landmark_areas.py`
- 30+ major landmarks worldwide
- Optimized bounding boxes
- Easy to extend with new locations