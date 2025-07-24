# SkyFi MCP Server Specification

## Overview

The SkyFi MCP Server is a Model Context Protocol implementation that provides agent-friendly access to SkyFi's satellite imagery API, integrated with weather and OpenStreetMap tools for comprehensive geospatial intelligence capabilities.

## Architecture

### Core Components

1. **MCP Transport Layer**
   - STDIO transport for Claude Desktop integration
   - HTTP transport for LangGraph/OpenAI compatibility
   - SSE support for streaming responses

2. **Service Modules**
   - **SkyFi Service**: Satellite imagery search, ordering, and delivery
   - **Weather Service**: Location-based weather data
   - **OSM Service**: OpenStreetMap queries and geocoding

3. **Authentication Layer**
   - API Key authentication (X-Skyfi-Api-Key header)
   - Environment variable configuration
   - Per-request auth override support

## Tool Definitions

### SkyFi Tools

#### `skyfi_search_archives`
Search for available satellite imagery in the SkyFi catalog.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "aoi": {
      "type": "string",
      "description": "Area of Interest as WKT polygon"
    },
    "fromDate": {
      "type": "string",
      "format": "date-time",
      "description": "Start date for search (ISO 8601)"
    },
    "toDate": {
      "type": "string",
      "format": "date-time",
      "description": "End date for search (ISO 8601)"
    },
    "openData": {
      "type": "boolean",
      "default": true,
      "description": "Include open data sources"
    },
    "productTypes": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["DAY", "NIGHT", "MULTISPECTRAL", "SAR"]
      },
      "description": "Types of imagery products"
    },
    "resolution": {
      "type": "string",
      "enum": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"],
      "description": "Desired resolution level"
    }
  },
  "required": ["aoi", "fromDate", "toDate"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "archiveId": { "type": "string" },
          "captureDate": { "type": "string", "format": "date-time" },
          "resolution": { "type": "number" },
          "cloudCover": { "type": "number" },
          "satellite": { "type": "string" },
          "productType": { "type": "string" },
          "price": { "type": "number" },
          "coverage": { "type": "number" }
        }
      }
    },
    "totalResults": { "type": "integer" },
    "searchId": { "type": "string" }
  }
}
```

#### `skyfi_order_archive`
Order satellite imagery from the catalog with delivery to cloud storage.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "aoi": {
      "type": "string",
      "description": "Area of Interest as WKT polygon"
    },
    "archiveId": {
      "type": "string",
      "description": "Archive ID from search results"
    },
    "deliveryDriver": {
      "type": "string",
      "enum": ["S3", "GS", "AZURE"],
      "description": "Cloud storage provider"
    },
    "deliveryParams": {
      "type": "object",
      "description": "Provider-specific delivery parameters"
    }
  },
  "required": ["aoi", "archiveId", "deliveryDriver", "deliveryParams"]
}
```

#### `skyfi_get_user`
Get current authenticated user information.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {}
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "userId": { "type": "string" },
    "email": { "type": "string" },
    "accountType": { "type": "string" },
    "credits": { "type": "number" },
    "organization": { "type": "string" }
  }
}
```

### Weather Tools

#### `weather_current`
Get current weather conditions for a location.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "location": {
      "type": "string",
      "description": "Location name or coordinates"
    },
    "lat": {
      "type": "number",
      "description": "Latitude (alternative to location)"
    },
    "lon": {
      "type": "number",
      "description": "Longitude (alternative to location)"
    }
  },
  "oneOf": [
    { "required": ["location"] },
    { "required": ["lat", "lon"] }
  ]
}
```

#### `weather_forecast`
Get weather forecast for the next 7 days.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "location": { "type": "string" },
    "lat": { "type": "number" },
    "lon": { "type": "number" },
    "days": {
      "type": "integer",
      "minimum": 1,
      "maximum": 7,
      "default": 3
    }
  }
}
```

### OpenStreetMap Tools

#### `osm_geocode`
Convert address to coordinates.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Address or place name to geocode"
    },
    "limit": {
      "type": "integer",
      "default": 5,
      "description": "Maximum number of results"
    }
  },
  "required": ["query"]
}
```

#### `osm_reverse_geocode`
Convert coordinates to address.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "lat": { "type": "number" },
    "lon": { "type": "number" },
    "zoom": {
      "type": "integer",
      "minimum": 0,
      "maximum": 18,
      "default": 18
    }
  },
  "required": ["lat", "lon"]
}
```

#### `osm_polygon_to_wkt`
Convert place name to WKT polygon for use with SkyFi API.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "place": {
      "type": "string",
      "description": "Place name to get boundary polygon"
    },
    "simplify": {
      "type": "boolean",
      "default": true,
      "description": "Simplify polygon for API compatibility"
    }
  },
  "required": ["place"]
}
```

## Configuration

### Environment Variables

```bash
# Required
SKYFI_API_KEY=your-api-key

# Optional
SKYFI_API_URL=https://app.skyfi.com/platform-api
WEATHER_API_KEY=your-weather-api-key
WEATHER_API_URL=https://api.openweathermap.org/data/3.0

# Server Configuration
MCP_TRANSPORT=stdio  # or http
MCP_HTTP_PORT=8080
MCP_LOG_LEVEL=INFO
```

### Config File (config.json)

```json
{
  "skyfi": {
    "api_key": "your-api-key",
    "api_url": "https://app.skyfi.com/platform-api"
  },
  "weather": {
    "api_key": "your-weather-api-key",
    "provider": "openweathermap"
  },
  "server": {
    "transport": "stdio",
    "log_level": "INFO"
  }
}
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "type": "authentication_error",
    "message": "Invalid API key provided",
    "details": {
      "service": "skyfi",
      "endpoint": "/auth/whoami"
    },
    "troubleshooting": [
      "Check that SKYFI_API_KEY is set correctly",
      "Verify your API key at app.skyfi.com",
      "Ensure you have a Pro account"
    ]
  }
}
```

### Error Types

- `authentication_error`: Invalid or missing credentials
- `validation_error`: Invalid input parameters
- `api_error`: External API returned an error
- `network_error`: Connection or timeout issues
- `configuration_error`: Missing required configuration

## Integration Examples

### Claude Desktop Integration

```json
{
  "mcpServers": {
    "skyfi": {
      "command": "python",
      "args": ["-m", "mcp_skyfi"],
      "env": {
        "SKYFI_API_KEY": "your-api-key"
      }
    }
  }
}
```

### LangGraph Integration

```python
from langchain.tools import Tool
from mcp_skyfi.client import SkyFiMCPClient

client = SkyFiMCPClient(
    base_url="http://localhost:8080",
    api_key="your-skyfi-api-key"
)

tools = [
    Tool(
        name="search_satellite_imagery",
        func=client.skyfi_search_archives,
        description="Search for satellite imagery"
    ),
    Tool(
        name="get_weather",
        func=client.weather_current,
        description="Get current weather conditions"
    )
]
```

### HTTP API Usage

```bash
# Get manifest
curl http://localhost:8080/mcp/manifest

# Search for imagery
curl -X POST http://localhost:8080/tools/skyfi_search_archives \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "aoi": "POLYGON((...))",
    "fromDate": "2024-01-01T00:00:00Z",
    "toDate": "2024-12-31T23:59:59Z"
  }'
```

## Performance Considerations

1. **Connection Pooling**: Maintain persistent connections to external APIs
2. **Response Caching**: Cache geocoding results and weather data (configurable TTL)
3. **Rate Limiting**: Respect API rate limits with built-in throttling
4. **Async Operations**: All I/O operations are async-first

## Security

1. **API Key Storage**: Never log or expose API keys
2. **Input Validation**: Strict JSON Schema validation on all inputs
3. **HTTPS Only**: Enforce HTTPS for all external API calls
4. **Sanitization**: WKT polygon validation and sanitization

## Monitoring and Logging

### Structured Logging

```json
{
  "timestamp": "2024-12-01T10:30:00Z",
  "level": "INFO",
  "service": "skyfi",
  "tool": "skyfi_search_archives",
  "duration_ms": 1250,
  "status": "success",
  "metadata": {
    "result_count": 15,
    "search_area_km2": 25.5
  }
}
```

### Metrics

- Tool invocation counts
- Response times per tool
- Error rates by type
- API credit usage tracking

## Development Workflow

1. **Local Development**
   ```bash
   # Install dependencies
   pip install -e ".[dev]"
   
   # Run tests
   pytest
   
   # Start server
   python -m mcp_skyfi
   ```

2. **Testing**
   - Unit tests for all tools
   - Integration tests with mock APIs
   - MCP protocol compliance tests
   - End-to-end testing with Claude Desktop

3. **Documentation**
   - Tool-specific examples
   - Common workflows
   - Troubleshooting guide
   - API migration guide

## Future Enhancements

1. **Caching Layer**: Redis-based caching for expensive operations
2. **Batch Operations**: Support for multiple AOI searches
3. **Webhook Support**: Real-time notifications for order completion
4. **Analytics Dashboard**: Usage statistics and cost tracking
5. **Multi-tenant Support**: Organization-level API key management