# MCP Demo Agents

This directory contains demo agents showing how to properly connect to the SkyFi MCP server with dynamic API key authentication via HTTP headers.

## Key Concept

The MCP philosophy is that **API keys are passed by the calling agent via headers**, not stored in server configuration. This enables:
- Multi-tenant usage (each user has their own key)
- Dynamic authentication
- No keys stored in config files
- Standard HTTP authentication patterns

## Demo Files

### 1. `demo_agent.py` - Command Line Demo
Shows basic connection and tool discovery.

```bash
# Without API key (only weather/OSM tools)
python demo_agent.py --demo

# With API key (all tools including SkyFi)
python demo_agent.py --demo --api-key YOUR_API_KEY

# Or via environment variable
export SKYFI_API_KEY=YOUR_API_KEY
python demo_agent.py --demo
```

### 2. `demo_agent_web.html` - Browser Demo
Interactive web interface showing how browser-based agents would connect.

```bash
# Start local server
python -m http.server 8080

# Open in browser
open http://localhost:8080/demo_agent_web.html
```

### 3. `demo_mcp_sdk.py` - Production SDK Example
Shows proper patterns for enterprise/production usage:
- Multi-user support
- Session management  
- Secure key handling

```bash
python demo_mcp_sdk.py
```

## How It Works

### For Regular HTTP Clients (Agents, Web Apps, etc.)

```python
# API key passed in headers dynamically
headers = {
    "Authorization": f"Bearer {user_api_key}"
}
response = requests.get("https://server/sse", headers=headers)
```

### For Claude Desktop

Claude Desktop has a limitation - it can only use static JSON configs. So for Claude Desktop specifically, the API key must be in the config:

```json
{
    "mcpServers": {
        "skyfi": {
            "command": "curl",
            "args": [
                "-N",
                "-H", "Authorization: Bearer YOUR_API_KEY",
                "http://localhost:8000/sse"
            ]
        }
    }
}
```

## Server Endpoints

- `GET /` - Server info
- `GET /health` - Health check
- `GET /sse` - SSE endpoint for MCP protocol

## Authentication Methods

The server accepts API keys via these headers (in order of precedence):
1. `X-Skyfi-Api-Key: YOUR_KEY`
2. `X-API-Key: YOUR_KEY`  
3. `Authorization: Bearer YOUR_KEY`

## Tool Access

- **Without API Key**: Weather and OSM tools only
- **With API Key**: All tools including SkyFi satellite imagery

## Production Deployment

1. Deploy server with HTTP transport:
   ```bash
   python -m src.mcp_skyfi --transport http --port 8000
   ```

2. Use ngrok for HTTPS:
   ```bash
   ngrok http 8000
   ```

3. Agents connect with their own API keys via headers

This follows the MCP philosophy where the server is stateless and authentication is handled per-request via standard HTTP headers.