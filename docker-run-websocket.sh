#!/bin/bash
# Run the Docker container with WebSocket bridge

docker run -d \
  --name skyfi-mcp-server \
  -p 8765:8765 \
  -e SKYFI_API_KEY="$SKYFI_API_KEY" \
  -e WEATHER_API_KEY="$WEATHER_API_KEY" \
  -e SKYFI_COST_LIMIT=40.0 \
  -e SKYFI_FORCE_LOWEST_COST=true \
  skyfi-mcp-test \
  python ws_bridge_v2.py

echo "SkyFi MCP server running on ws://localhost:8765"
echo "To stop: docker stop skyfi-mcp-server && docker rm skyfi-mcp-server"