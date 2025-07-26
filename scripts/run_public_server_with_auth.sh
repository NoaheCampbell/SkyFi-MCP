#!/bin/bash
# Run the public SkyFi MCP server with web authentication

# Configuration
MCP_PORT=8080
AUTH_PORT=8081
NGROK_SUBDOMAIN=${NGROK_SUBDOMAIN:-"skyfi-mcp"}

# Start the web auth server
echo "Starting authentication web server on port $AUTH_PORT..."
cd "$(dirname "$0")/.."
source venv/bin/activate
uvicorn src.mcp_skyfi.auth.web_auth:app --port $AUTH_PORT --host 0.0.0.0 &
AUTH_PID=$!

# Give auth server time to start
sleep 2

# Start the MCP server
echo "Starting MCP server on port $MCP_PORT..."
python -m src.mcp_skyfi.servers.public_server --transport http --port $MCP_PORT &
MCP_PID=$!

# Give MCP server time to start
sleep 2

# Start ngrok with both ports
echo "Starting ngrok tunnel..."
cat > /tmp/ngrok-config.yml << EOF
version: 2
tunnels:
  mcp:
    proto: http
    addr: $MCP_PORT
    subdomain: $NGROK_SUBDOMAIN
  auth:
    proto: http
    addr: $AUTH_PORT
    subdomain: ${NGROK_SUBDOMAIN}-auth
EOF

ngrok start --all --config /tmp/ngrok-config.yml &
NGROK_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $AUTH_PID 2>/dev/null
    kill $MCP_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    rm -f /tmp/ngrok-config.yml
    exit
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Show status
sleep 3
echo ""
echo "🚀 Public SkyFi MCP Server is running!"
echo ""
echo "MCP Server URL: https://${NGROK_SUBDOMAIN}.ngrok.io"
echo "Auth Server URL: https://${NGROK_SUBDOMAIN}-auth.ngrok.io"
echo ""
echo "Share the MCP URL with users for Claude Desktop configuration"
echo "Users will authenticate via secure web links - no API keys in chat!"
echo ""
echo "Press Ctrl+C to stop"

# Keep script running
wait