# Migration Guide

## Recent Changes

### Removed Tools (Latest Version)

The following tools have been removed to simplify the API:

**Search Tools** (consolidated into `skyfi_search_archives`):
- `skyfi_search_exact` → Use `skyfi_search_archives` 
- `skyfi_search_bbox` → Use `skyfi_search_archives`

**OSM Tools** (removed due to complexity issues):
- `osm_polygon_to_wkt` → Use `osm_generate_aoi` for simple shapes

### Search Behavior Changes

**Resolution Handling**:
- When `resolution` is specified, only matching results are returned
- `openData` flag is automatically set based on resolution:
  - LOW resolution → `openData: true` (free imagery)
  - HIGH/MEDIUM resolution → `openData: false` (paid imagery)

**Simplified Search**:
```python
# All searches now use the unified tool
skyfi_search_archives(
    aoi="POLYGON((-73.98 40.76, -73.94 40.76, -73.94 40.80, -73.98 40.80, -73.98 40.76))",
    fromDate="2024-01-01",
    toDate="2024-01-31",
    resolution="HIGH"  # Will only return HIGH resolution results
)
```

## Configuration

**Environment Variables**:
- `SKYFI_API_KEY` - Your SkyFi API key (required)
- `SKYFI_COST_LIMIT` - Maximum spending limit (default: 40.0)
- `SKYFI_FORCE_LOWEST_COST` - Prefer lowest cost options (default: true)
- `SKYFI_ENABLE_ORDERING` - Enable order placement (default: false)
- `WEATHER_API_KEY` - OpenWeatherMap API key (optional)

## Common Migration Issues

### Polygon Too Complex (422 Error)
- Use `osm_generate_aoi` to create simple shapes (square, circle, etc.)
- Keep polygons under 25 points
- Use pre-simplified landmark names when available

### Authentication Errors
- API keys now set via environment variables or headers
- No more in-session authentication tools
- See docs/AUTHENTICATION.md for details

## Getting Help

- Check available tools: See README.md
- Report issues: https://github.com/NoaheCampbell/SkyFi-MCP/issues