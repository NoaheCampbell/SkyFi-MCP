# Migration Guide

## Upgrading from Previous Versions

### Breaking Changes

#### Removed Tools (23 tools removed)

The following tools have been removed in favor of simpler alternatives:

**Authentication Tools** (use environment variables instead):
- `skyfi_authenticate` → Set `SKYFI_API_KEY` in environment
- `skyfi_check_auth` → Authentication is automatic

**Budget Management Tools** (use environment variables instead):
- `update_account_budget` → Set `SKYFI_COST_LIMIT`
- `request_budget_change` → Modify `SKYFI_COST_LIMIT`
- `confirm_budget_change` → Not needed
- `view_current_budget` → Use `skyfi_spending_report`

**Saved Searches** (removed completely):
- `skyfi_save_search`
- `skyfi_list_saved_searches`
- `skyfi_run_saved_search`

**Redundant Tools**:
- `skyfi_get_download_url` → Use `skyfi_download_order`
- `skyfi_get_pricing` → Use `skyfi_estimate_cost`
- `calculate_archive_pricing` → Use `skyfi_estimate_cost`
- `estimate_tasking_pricing` → Use `skyfi_get_tasking_quote`

**OSM Tools** (use simpler alternatives):
- `osm_batch_geocode` → Use `osm_geocode` multiple times
- `osm_search_nearby_pois` → Use `osm_geocode` with specific queries
- `osm_search_businesses` → Use `osm_geocode` with business names
- `osm_create_bounding_box` → Use `osm_generate_aoi` or `skyfi_search_bbox`

### New Tools Added

**Enhanced Search Tools**:
- `skyfi_search_exact` - Search with exact polygons (no auto-simplification)
- `skyfi_search_bbox` - Simple bounding box search (most reliable)

### Polygon Handling Changes

**Automatic Simplification**:
- Polygons with >25 points are now automatically simplified
- Complex polygons from OSM are automatically optimized
- 30+ landmarks have pre-defined bounding boxes

**To Keep Exact Polygons**:
```python
# Old way (might fail with 422 error)
skyfi_search_archives(aoi=complex_polygon, ...)

# New way (respects exact coordinates)
skyfi_search_exact(polygon=complex_polygon, ...)
```

### Configuration Changes

**Environment Variables**:
- `SKYFI_ENABLE_ORDERING` now defaults to `false` for safety
- New: `SKYFI_COST_LIMIT` (default: 40.0)
- New: `SKYFI_FORCE_LOWEST_COST` (default: true)

### API Changes

**Order Process**:
```python
# Old way (direct ordering)
skyfi_order_archive(...)  # This tool is disabled by default

# New way (two-step process)
1. skyfi_prepare_order(...)  # Returns quote and token
2. skyfi_confirm_order(token=..., confirmation_code=...)
```

### Docker Changes

**Running the server**:
```bash
# Old way
docker run skyfi-mcp

# New way (must specify Python command)
docker run skyfi-mcp python -m mcp_skyfi
```

## Migration Steps

1. **Update Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Update Tool Calls**:
   - Replace removed tools with their alternatives
   - Use `skyfi_search_bbox` for simple area searches
   - Use `skyfi_search_exact` for precise polygon searches

3. **Update Docker Configuration**:
   - Add `python -m mcp_skyfi` to Docker run commands
   - Update Claude Desktop config with new Docker args

4. **Test Your Integration**:
   ```python
   # Test basic search
   skyfi_search_archives(
       aoi="POLYGON((-73.98 40.76, -73.94 40.76, -73.94 40.80, -73.98 40.80, -73.98 40.76))",
       fromDate="last week",
       toDate="today"
   )
   ```

## Troubleshooting Migration Issues

### "Unknown tool" errors
- The tool has been removed - check the removed tools list above
- Use the suggested alternative tool

### 422 Polygon errors
- Your polygon is too complex
- Use `osm_generate_aoi` to create simple shapes
- Or use `skyfi_search_bbox` with coordinates

### Authentication failures
- Set `SKYFI_API_KEY` in environment instead of using auth tools
- Remove calls to `skyfi_authenticate`

### Budget errors
- Set `SKYFI_COST_LIMIT` in environment
- Use `skyfi_spending_report` to check budget status

## Getting Help

If you encounter issues during migration:
1. Check the error message for specific tool names
2. Refer to AVAILABLE_TOOLS.md for the current tool list
3. Use the examples in README.md
4. Report issues at https://github.com/NoaheCampbell/SkyFi-MCP/issues