# SkyFi MCP Demos

This directory contains comprehensive demonstrations of the SkyFi MCP server capabilities, showcasing real-world applications and integration patterns.

## Available Demos

### 1. Advanced Geospatial Research Agent (`advanced_geospatial_agent.py`)

A production-ready agent that performs complex geospatial analysis tasks.

**Features:**
- Natural language location processing
- Multi-step workflows combining satellite imagery, weather, and map data
- Cost optimization for imagery acquisition
- Change detection and monitoring capabilities
- Rich terminal UI with progress tracking
- Export to multiple formats (Markdown, JSON, HTML)

**Use Cases:**
- Location intelligence and analysis
- Environmental monitoring
- Urban planning research
- Disaster assessment

### 2. Practical Use Cases (`practical_use_cases.py`)

Industry-specific demonstrations showing how different sectors can leverage satellite imagery.

**Included Scenarios:**
- **Real Estate Development**: Site analysis, historical comparison, development tracking
- **Agricultural Monitoring**: Crop health monitoring, growing season analysis, yield estimation
- **Disaster Response**: Rapid damage assessment, before/after comparison, response planning
- **Environmental Monitoring**: Deforestation tracking, carbon credit verification, conservation
- **Infrastructure Inspection**: Pipeline monitoring, utility inspection, maintenance planning

### 3. Basic Demo Agent (`demo_agent.py`)

Simple example showing core MCP connection and tool usage patterns.

**Features:**
- HTTP/SSE connection setup
- Basic tool calling
- Error handling
- Authentication examples

### 4. Interactive Web Demo (`web_demo.py`)

Modern web-based demo showcasing SkyFi MCP capabilities with an interactive map interface.

**Features:**
- 🗺️ Interactive Leaflet.js map with click-to-analyze functionality
- 🛰️ Real-time satellite imagery search with thumbnail previews
- 🌤️ Integrated weather data for locations
- 💰 Cost estimation for satellite imagery
- 📍 Geocoding and reverse geocoding
- 🎯 Visual feedback with markers and activity feed

**Run it:**
```bash
python demos/web_demo.py
# Open http://localhost:8888 in your browser
```

### 5. MCP Chat Demo (`mcp_chat_demo.py`)

Full-featured chat interface demonstrating the Model Context Protocol with natural language interaction.

**Features:**
- 💬 Component-based React UI with real-time chat
- 🤖 Natural language understanding for all MCP tools
- 🗺️ Interactive map with polygon visualization
- 📸 Satellite imagery results with thumbnails
- 🎯 Quick action buttons for common tasks
- 🔧 Live tool execution visualization
- 📊 Support for all 30+ SkyFi MCP tools

**Run it:**
```bash
python demos/mcp_chat_demo.py
# Open http://localhost:8889 in your browser
```

**Quick Actions Available:**
- Find Location - Geocode any address
- Get Address - Reverse geocode coordinates
- Create Area - Generate AOI polygons
- Current Weather - Get real-time weather
- Weather Forecast - 5-day predictions
- Search Images - Find satellite imagery
- Cost Estimate - Get pricing information
- Account Info - View SkyFi account details

## Quick Start

### Prerequisites

```bash
# Install the SkyFi MCP server
pip install skyfi-mcp

# For advanced demos
pip install rich aiohttp

# Set your API key
export SKYFI_API_KEY="your-skyfi-api-key"
```

### Running the Demos

#### Option 1: Local MCP Server

```bash
# Terminal 1: Start the MCP server
python -m mcp_skyfi

# Terminal 2: Run a demo
python demos/advanced_geospatial_agent.py
```

#### Option 2: Remote MCP Server

```bash
# Connect to hosted MCP server
python demos/advanced_geospatial_agent.py --mcp-url https://skyfi-mcp.fly.dev
```

#### Option 3: Docker

```bash
# Build and run with Docker
docker build -t skyfi-mcp-demos .
docker run -e SKYFI_API_KEY=$SKYFI_API_KEY skyfi-mcp-demos python demos/practical_use_cases.py
```

## Demo Configurations

### Environment Variables

```bash
# Required
export SKYFI_API_KEY="your-api-key"

# Optional
export MCP_URL="http://localhost:8000"  # Default MCP server URL
export MCP_LOG_LEVEL="INFO"              # Logging verbosity
export DEMO_OUTPUT_DIR="./output"        # Where to save results
```

### Configuration File

Create `demo_config.json`:

```json
{
  "mcp_url": "http://localhost:8000",
  "api_key": "your-api-key",
  "default_location": "New York City",
  "output_format": "markdown",
  "cost_limit": 1000
}
```

## Integration Examples

### Python Integration

```python
from demos.advanced_geospatial_agent import GeospatialResearchAgent

async def my_analysis():
    async with GeospatialResearchAgent() as agent:
        # Analyze a location
        result = await agent.analyze_location("Silicon Valley")
        
        # Generate cost-optimized order
        order = await agent.generate_cost_optimized_order(
            "San Francisco Bay Area",
            {"max_budget": 500, "resolution": "high"}
        )
        
        # Export results
        report = await agent.export_analysis("markdown")
```

### JavaScript Integration

```javascript
// Using the web demo as a library
import { MCPClient } from './demo_agent_web.js';

const client = new MCPClient('http://localhost:8000/sse');

// Search for imagery
const results = await client.callTool('skyfi_search_archives', {
    aoi: 'POLYGON((-74.0 40.7, -74.0 40.8, -73.9 40.8, -73.9 40.7, -74.0 40.7))',
    fromDate: '2024-01-01',
    toDate: '2024-12-31'
});
```

### Command Line Usage

```bash
# Run specific use case
python -c "
from demos.practical_use_cases import PracticalUseCases
import asyncio

async def run():
    async with PracticalUseCases() as uc:
        result = await uc.real_estate_site_analysis('Times Square, NYC')
        print(result)

asyncio.run(run())
"
```

## Advanced Features

### Custom Workflows

Create your own workflows by combining MCP tools:

```python
# Example: Wildfire monitoring workflow
async def wildfire_monitoring(location: str):
    # 1. Get location and create monitoring area
    geocode = await agent.call_tool("osm_geocode", {"query": location})
    aoi = await agent.call_tool("osm_generate_aoi", {
        "center": {"lat": lat, "lon": lon},
        "shape": "circle",
        "radius_km": 50
    })
    
    # 2. Search for thermal anomalies
    thermal_search = await agent.call_tool("skyfi_search_archives", {
        "aoi": aoi["wkt"],
        "satelliteTypes": ["Sentinel-2", "MODIS"],  # Thermal capable
        "fromDate": "yesterday",
        "toDate": "today"
    })
    
    # 3. Check weather conditions
    weather = await agent.call_tool("weather_current", {
        "location": {"lat": lat, "lon": lon}
    })
    
    # 4. Generate alert if needed
    if thermal_search["results"] and weather["wind"]["speed"] > 20:
        return {"alert": "High fire risk", "immediate_action": "Order detailed imagery"}
```

### Performance Optimization

```python
# Parallel execution for better performance
import asyncio

async def parallel_analysis(locations: List[str]):
    tasks = [
        agent.analyze_location(loc) 
        for loc in locations
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### Error Handling

```python
# Robust error handling
try:
    result = await agent.call_tool("skyfi_search_archives", params)
except MCPError as e:
    if e.code == "rate_limit":
        await asyncio.sleep(60)
        result = await agent.call_tool("skyfi_search_archives", params)
    else:
        logger.error(f"MCP Error: {e}")
        return fallback_result
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if MCP server is running
   curl http://localhost:8000/health
   
   # Start server if needed
   python -m mcp_skyfi
   ```

2. **Authentication Errors**
   ```bash
   # Verify API key
   echo $SKYFI_API_KEY
   
   # Test authentication
   curl -H "Authorization: Bearer $SKYFI_API_KEY" https://api.skyfi.com/user
   ```

3. **Tool Not Found**
   ```python
   # List available tools
   tools = await agent.call_tool("list_tools", {})
   print(tools)
   ```

### Debug Mode

Enable detailed logging:

```bash
export MCP_LOG_LEVEL=DEBUG
export PYTHONPATH=$PYTHONPATH:$(pwd)
python -m demos.advanced_geospatial_agent --debug
```

## Contributing

To add new demos:

1. Create a new file in the `demos/` directory
2. Follow the existing patterns for MCP integration
3. Add documentation to this README
4. Include error handling and logging
5. Test with both local and remote MCP servers

## Resources

- [SkyFi MCP Documentation](../README.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [SkyFi API Documentation](https://docs.skyfi.com)
- [Technical Article: Building Demo Agent](../docs/BUILDING_DEMO_AGENT.md)

## Support

- GitHub Issues: https://github.com/NoaheCampbell/SkyFi-MCP/issues
- SkyFi Support: support@skyfi.com