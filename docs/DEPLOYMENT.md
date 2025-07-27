# Deployment Guide

## Deployment Options

### 1. Local Development

```bash
# Install
pip install -e .

# Run directly
python -m mcp_skyfi

# Or with Claude Desktop
# Add to claude_desktop_config.json:
{
  "mcpServers": {
    "skyfi": {
      "command": "python3",
      "args": ["-m", "mcp_skyfi"],
      "env": {
        "SKYFI_API_KEY": "your-key-here"
      }
    }
  }
}
```

### 2. Docker

```bash
# Build
docker build -t skyfi-mcp .

# Run MCP server
docker run -e SKYFI_API_KEY="your-key" skyfi-mcp python -m mcp_skyfi

# Run WebSocket bridge (for remote access)
docker run -p 8765:8765 -e SKYFI_API_KEY="your-key" skyfi-mcp

# With Docker Compose
docker-compose up -d
```

### 3. Public Server (Ngrok)

```bash
# Start server
./scripts/run_public_server.sh

# Server will display:
# Public URL: https://abc123.ngrok.io

# Users add to Claude Desktop:
{
  "mcpServers": {
    "skyfi": {
      "transport": "http",
      "url": "https://abc123.ngrok.io"
    }
  }
}
```

### 4. Production (Fly.io)

```bash
# Deploy
fly deploy

# Scale
fly scale count 2

# Monitor
fly logs
```

### 5. AWS/Cloud

```bash
# EC2 with systemd
sudo cp scripts/skyfi-mcp.service /etc/systemd/system/
sudo systemctl enable skyfi-mcp
sudo systemctl start skyfi-mcp

# With AWS Secrets Manager
export SKYFI_SECRET_NAME="skyfi-mcp-keys"
```

## Environment Variables

Required:
- `SKYFI_API_KEY` - Your SkyFi API key

Optional:
- `WEATHER_API_KEY` - OpenWeatherMap API key
- `SKYFI_COST_LIMIT` - Maximum spending limit (default: 40.0)
- `SKYFI_FORCE_LOWEST_COST` - Always use cheapest options (default: true)
- `SKYFI_ENABLE_ORDERING` - Allow order placement (default: false)

## Security Considerations

1. **API Keys**: Use environment variables or header authentication
2. **HTTPS**: Always use HTTPS for production deployments
3. **Rate Limiting**: Configure rate limits for public servers
4. **Access Control**: Use authentication for multi-user deployments

## Monitoring

- Health check: `GET /health`
- Logs: Check container/systemd logs
- Metrics: Use OpenTelemetry (see MONITORING_USAGE.md)