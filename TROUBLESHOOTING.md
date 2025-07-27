# Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### "spawn python ENOENT" error in Claude Desktop
**Problem**: Claude Desktop can't find Python
**Solution**:
```json
// Use full path to Python
{
  "command": "/usr/bin/python3",  // macOS/Linux
  "command": "C:\\Python311\\python.exe",  // Windows
}
```

#### Module not found errors
**Problem**: `ModuleNotFoundError: No module named 'mcp_skyfi'`
**Solution**:
```bash
# Install in development mode
pip install -e .

# Or install from GitHub
pip install git+https://github.com/NoaheCampbell/SkyFi-MCP.git
```

### API Errors

#### 401 Unauthorized
**Problem**: Invalid or missing API key
**Solutions**:
1. Check your API key is correct
2. Ensure you have a SkyFi Pro account
3. Verify environment variable is set:
   ```bash
   echo $SKYFI_API_KEY
   ```

#### 422 Unprocessable Entity
**Problem**: Polygon too complex for API
**Solutions**:
1. Use simpler polygons (<25 points):
   ```python
   # Instead of complex polygon
   osm_polygon_to_wkt("Central Park")
   
   # Use predefined bbox or generate simple shape
   osm_generate_aoi(center={...}, shape="square", size_km=2)
   ```
2. Use `skyfi_search_bbox` for simple searches
3. Enable auto-simplification (default behavior)

#### 429 Rate Limited
**Problem**: Too many API requests
**Solutions**:
1. Add delays between requests
2. Reduce concurrent searches
3. Check rate limit status in response headers

### Search Issues

#### No results found
**Possible causes**:
1. Date range too narrow
2. Area too small
3. Cloud coverage filters too strict
4. No imagery available for location

**Solutions**:
```python
# Wider date range
fromDate="1 month ago"
toDate="today"

# Larger area
size_km=5  # Instead of 1

# Remove filters
# Don't specify cloud_coverage or resolution
```

#### Wrong area searched
**Problem**: Polygon not what expected
**Solution**: Verify your polygon:
```python
# Check what polygon you're using
osm_polygon_to_wkt("Your Location", simplify=False)

# Use exact coordinates
skyfi_search_bbox(
    min_lon=-73.98, min_lat=40.76,
    max_lon=-73.94, max_lat=40.80
)
```

### Ordering Issues

#### "Ordering is disabled" error
**Problem**: Safety feature preventing accidental purchases
**Solution**: Enable ordering in environment:
```bash
export SKYFI_ENABLE_ORDERING=true
export SKYFI_COST_LIMIT=100.0
```

#### Order confirmation fails
**Problem**: Invalid token or timeout
**Solutions**:
1. Complete confirmation within 5 minutes
2. Use exact token and code from prepare_order
3. Check spending limit not exceeded

### Docker Issues

#### WebSocket server starts instead of MCP
**Problem**: Wrong Docker command
**Solution**: Specify Python module:
```json
"args": ["run", "-i", "--rm", "skyfi-mcp", "python", "-m", "mcp_skyfi"]
```

#### Container exits immediately
**Problem**: Missing required environment variables
**Solution**: Pass all required vars:
```bash
docker run -e SKYFI_API_KEY="your-key" skyfi-mcp python -m mcp_skyfi
```

### Performance Issues

#### Slow searches
**Causes**:
1. Large area searches
2. Long date ranges
3. Complex polygons

**Solutions**:
1. Break into smaller searches
2. Use lower resolution: `resolution="LOW"`
3. Simplify polygons

#### Memory errors
**Problem**: Processing too much data
**Solutions**:
1. Reduce search result limit
2. Process results in batches
3. Clear cache between searches

### Claude Desktop Integration

#### Tools not showing up
**Problem**: MCP server not connected
**Solutions**:
1. Restart Claude Desktop
2. Check logs: `~/Library/Logs/Claude/mcp-*.log`
3. Verify config file syntax
4. Test with simple echo server first

#### "Failed to start MCP server"
**Common causes**:
1. Invalid JSON in config
2. Wrong file paths
3. Missing dependencies

**Debug steps**:
```bash
# Test command directly
python3 -m mcp_skyfi

# Check Python path
which python3

# Verify installation
pip show mcp-skyfi
```

### Tool-Specific Issues

#### osm_polygon_to_wkt returns complex polygon
**Solution**: Use the simplified version or alternatives:
```python
# Option 1: Let it auto-simplify (default)
osm_polygon_to_wkt("Central Park")

# Option 2: Use area generation
osm_generate_aoi(center={...}, shape="rectangle")

# Option 3: Use landmark bbox
skyfi_search_archives(aoi="POLYGON((-73.982 40.764, ...))")
```

#### Weather tools not working
**Problem**: Missing weather API key
**Solution**: 
```bash
export WEATHER_API_KEY="your-openweathermap-key"
```

### Debugging Tips

#### Enable debug logging
```bash
export MCP_LOG_LEVEL=DEBUG
```

#### Check server logs
```bash
# Claude Desktop logs
tail -f ~/Library/Logs/Claude/mcp-*.log

# Docker logs
docker logs skyfi-mcp
```

#### Test individual components
```python
# Test API connection
python -m mcp_skyfi.test_connection

# Test specific tool
python -c "from mcp_skyfi.skyfi.client import SkyFiClient; ..."
```

### Getting Help

If issues persist:
1. Check error message details
2. Search existing issues: https://github.com/NoaheCampbell/SkyFi-MCP/issues
3. Create new issue with:
   - Error message
   - Tool being used
   - Environment details
   - Steps to reproduce