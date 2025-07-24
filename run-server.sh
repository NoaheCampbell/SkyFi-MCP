#!/bin/bash
# MCP SkyFi Server Runner for Remote Hosting

# Client provides all configuration via env variables
# Server just runs with whatever the client sends

# Validate required API key
if [ -z "$SKYFI_API_KEY" ]; then
    echo "Error: SKYFI_API_KEY not provided by client" >&2
    exit 1
fi

# Log startup (to stderr so it doesn't interfere with STDIO)
echo "Starting MCP SkyFi Server..." >&2
echo "API Key: ${SKYFI_API_KEY:0:20}..." >&2
echo "Cost Limit: ${SKYFI_COST_LIMIT:-40.0}" >&2
echo "Ordering Enabled: ${SKYFI_ENABLE_ORDERING:-false}" >&2
echo "Daily Limit: ${SKYFI_DAILY_LIMIT:-40.0}" >&2

# Change to script directory
cd "$(dirname "$0")"

# Run the MCP server with client's configuration
python3 -m mcp_skyfi