# SkyFi MCP Server

A Model Context Protocol (MCP) server that provides access to SkyFi's satellite imagery API through Claude Desktop, Cursor, and other MCP-compatible clients.

**29 tools** for satellite imagery search, ordering, tasking, monitoring, and geographic operations.

## Features

- 🛰️ **Satellite Image Search** - Search for satellite imagery with natural language dates
- 💰 **Cost Controls** - Built-in spending limits and cost tracking
- 📊 **Order Management** - Track and download your satellite image orders
- 🌍 **Multi-Location Search** - Search multiple areas simultaneously
- 📈 **Order History Export** - Export orders to CSV, JSON, HTML, or Markdown
- 🎯 **Satellite Tasking** - Request new satellite captures for specific areas
- 📡 **Area Monitoring** - Set up webhooks to monitor areas for new imagery
- 🗺️ **OpenStreetMap Integration** - Convert locations to polygons for searches
- 🐳 **Docker Support** - Easy deployment with Docker containers
- 🌤️ **Weather Integration** - Get weather data for capture planning

## Quick Start

### Prerequisites

- Python 3.10+
- SkyFi Pro account and API key (get it at [app.skyfi.com](https://app.skyfi.com))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/NoaheCampbell/SkyFi-MCP.git
cd SkyFi-MCP
```

2. Install the package:
```bash
pip install -e .
```

3. Set up your environment:
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - SKYFI_API_KEY: Your SkyFi API key (required)
# - WEATHER_API_KEY: Your OpenWeatherMap API key (optional, for weather features)
```

### Testing the Server

Run the server directly to test:
```bash
python -m mcp_skyfi
```

## Claude Desktop Setup

Add this to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "skyfi": {
      "command": "python3",
      "args": ["-m", "mcp_skyfi"],
      "env": {
        "SKYFI_API_KEY": "YOUR_SKYFI_API_KEY_HERE",
        "WEATHER_API_KEY": "YOUR_OPENWEATHERMAP_API_KEY_HERE",
        "SKYFI_COST_LIMIT": "40.0",
        "SKYFI_FORCE_LOWEST_COST": "true"
      }
    }
  }
}
```

**Note:** If you get a "spawn python ENOENT" error, try using the full path to python:
```json
{
  "mcpServers": {
    "skyfi": {
      "command": "/usr/bin/python3",
      "args": ["-m", "mcp_skyfi"],
      "env": {
        "SKYFI_API_KEY": "YOUR_SKYFI_API_KEY_HERE",
        "WEATHER_API_KEY": "YOUR_OPENWEATHERMAP_API_KEY_HERE",
        "SKYFI_COST_LIMIT": "40.0",
        "SKYFI_FORCE_LOWEST_COST": "true"
      }
    }
  }
}
```

Restart Claude Desktop after updating the configuration.

## Docker Setup

You can also run the MCP server using Docker:

1. Build the Docker image:
```bash
docker build -t skyfi-mcp .
```

2. Run the container:
```bash
docker run -d \
  --name skyfi-mcp \
  -e SKYFI_API_KEY="YOUR_SKYFI_API_KEY" \
  -e WEATHER_API_KEY="YOUR_OPENWEATHERMAP_API_KEY" \
  -p 8765:8765 \
  skyfi-mcp
```

3. Update Claude Desktop config for Docker:
```json
{
  "mcpServers": {
    "skyfi-mcp-docker": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--name", "skyfi-mcp-test",
        "-e", "SKYFI_API_KEY=YOUR_API_KEY",
        "-e", "WEATHER_API_KEY=YOUR_WEATHER_KEY",
        "skyfi-mcp",
        "python", "-m", "mcp_skyfi"
      ]
    }
  }
}
```

## Available Tools

### SkyFi Tools

#### `skyfi_search_archives`
Search for satellite imagery in a specific area and time range.

Example:
```
Search for satellite images of Central Park from the last month
```

#### `skyfi_prepare_order` / `skyfi_confirm_order`
Two-step ordering process with safety checks:
1. Prepare an order to get pricing and confirmation token
2. Confirm the order with the token to complete purchase

#### `skyfi_list_orders`
List your recent satellite image orders.

#### `skyfi_download_order`
Download a completed order.

#### `skyfi_export_order_history`
Export your order history to various formats.

#### `skyfi_get_user`
Get your account information and available credits.

### Weather Tools

**Note:** Weather tools require an OpenWeatherMap API key. Get one free at [openweathermap.org](https://openweathermap.org/api).

#### `weather_current`
Get current weather conditions for any location.

Example:
```
What's the weather in San Francisco?
```

#### `weather_forecast`
Get weather forecast for the next few days.

Example:
```
What's the weather forecast for New York for the next 3 days?
```

### Satellite Tasking Tools

#### `skyfi_get_tasking_quote`
Get a quote for tasking a satellite to capture new imagery.

#### `skyfi_create_tasking_order`
Place an order for new satellite imagery capture.

#### `skyfi_analyze_capture_feasibility`
Analyze the feasibility of capturing imagery for an area.

#### `skyfi_predict_satellite_passes`
Predict when satellites will pass over an area.

### Monitoring Tools

#### `skyfi_create_webhook_subscription`
Set up webhooks to monitor for new imagery.

#### `skyfi_setup_area_monitoring`
Monitor specific areas for new satellite captures.

#### `skyfi_get_notification_status`
Check the status of your monitoring subscriptions.

### OpenStreetMap Tools

#### `osm_geocode`
Convert addresses to coordinates.

Example:
```
Get coordinates for the Eiffel Tower
```

#### `osm_reverse_geocode`
Convert coordinates to addresses.

#### `osm_polygon_to_wkt`
Convert place names to WKT polygons for satellite image searches.

Example:
```
Get the boundary polygon for Manhattan
```

#### `osm_generate_aoi`
Generate area of interest polygons (circles, squares, etc.) around a point.

#### `osm_calculate_distance`
Calculate distances between geographic points.

## Example Workflows

### Finding Satellite Images of a City

1. Use `osm_polygon_to_wkt` to get the boundary:
   ```
   Get the WKT polygon for San Francisco
   ```

2. Use `skyfi_search_archives` with the polygon:
   ```
   Search for satellite images of that area from January 2024
   ```

### Weather-Aware Image Selection

1. Check weather conditions:
   ```
   What's been the weather in Miami for the past week?
   ```

2. Search for clear-day images:
   ```
   Find satellite images of Miami from days with low cloud cover
   ```

## Configuration

### Environment Variables

- `SKYFI_API_KEY` (required): Your SkyFi API key
- `SKYFI_API_URL`: Override the API endpoint (default: https://app.skyfi.com/platform-api)
- `SKYFI_COST_LIMIT`: Maximum spending limit (default: 40.0)
- `SKYFI_FORCE_LOWEST_COST`: Always select lowest cost option (default: true)
- `WEATHER_API_KEY`: OpenWeatherMap API key for weather features
- `MCP_LOG_LEVEL`: Logging level (default: INFO)

### Using with Other Clients

The server supports the standard MCP protocol and can be used with any MCP-compatible client.

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Code Quality

```bash
ruff check src/
mypy src/
```

## Troubleshooting

### "Invalid API Key" Error

1. Verify your API key at [app.skyfi.com](https://app.skyfi.com)
2. Ensure you have a Pro account
3. Check that `SKYFI_API_KEY` is set correctly in your environment

### No Results from Search

1. Verify the date range includes available imagery
2. Try a larger area or different location
3. Check if open data is enabled (some areas may only have commercial imagery)

### Connection Issues

1. Check your internet connection
2. Verify the API URL is accessible
3. Try increasing the timeout in the configuration

## Integration Guides

See [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) for detailed guides on using SkyFi MCP with:
- Claude Desktop & Cursor
- Langchain, Vercel AI SDK, ADK
- OpenAI, Anthropic, Google Gemini
- Multi-user cloud deployments

## Deployment Options

### Local Installation
```bash
pip install git+https://github.com/NoaheCampbell/SkyFi-MCP.git
```

### Cloud Deployment (Multi-user)
- Docker + Fly.io deployment included
- WebSocket bridge for remote access
- Header-based authentication for multiple users

## License

MIT License - see LICENSE file for details.

## Support

- SkyFi API Documentation: [docs.skyfi.com](https://docs.skyfi.com)
- Integration Guide: [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)
- Issues: [GitHub Issues](https://github.com/NoaheCampbell/SkyFi-MCP/issues)
- SkyFi Support: support@skyfi.com