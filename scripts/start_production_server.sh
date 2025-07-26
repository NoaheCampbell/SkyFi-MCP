#!/bin/bash
# Production startup script for SkyFi MCP with reserved ngrok domain

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check required variables
if [ -z "$NGROK_DOMAIN" ]; then
    echo "Error: NGROK_DOMAIN not set. Please create .env file from .env.example"
    exit 1
fi

if [ -z "$NGROK_AUTHTOKEN" ]; then
    echo "Error: NGROK_AUTHTOKEN not set. Please create .env file from .env.example"
    exit 1
fi

# Set defaults
MCP_PORT=${MCP_PORT:-8080}
AUTH_PORT=${AUTH_PORT:-8081}

# Configure ngrok
ngrok config add-authtoken $NGROK_AUTHTOKEN

# Start services
echo "Starting SkyFi MCP Server..."
echo "Domain: https://$NGROK_DOMAIN"
echo ""

# Start auth server
echo "Starting authentication server on port $AUTH_PORT..."
source venv/bin/activate
python -m uvicorn src.mcp_skyfi.auth.web_auth:app \
    --host 0.0.0.0 \
    --port $AUTH_PORT \
    --log-level info &
AUTH_PID=$!

# Start MCP server
echo "Starting MCP server on port $MCP_PORT..."
python -m src.mcp_skyfi.servers.public_server \
    --transport http \
    --host 0.0.0.0 \
    --port $MCP_PORT &
MCP_PID=$!

# Give servers time to start
sleep 3

# Start ngrok with reserved domain
echo "Starting ngrok tunnel to $NGROK_DOMAIN..."
ngrok http $MCP_PORT \
    --domain=$NGROK_DOMAIN \
    --log=stdout \
    --log-level=info &
NGROK_PID=$!

# Function to cleanup on exit
cleanup() {
    echo -e "\nShutting down services..."
    kill $AUTH_PID 2>/dev/null
    kill $MCP_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    exit
}

trap cleanup EXIT INT TERM

# Wait for ngrok to be ready
sleep 5

# Display status
clear
echo "=============================================="
echo "   SkyFi MCP Server - Production Mode"
echo "=============================================="
echo ""
echo "🌐 Public URL: https://$NGROK_DOMAIN"
echo "🔐 Auth URL: https://$NGROK_DOMAIN/auth/[nonce]"
echo ""
echo "📋 User Configuration for Claude Desktop:"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "skyfi": {'
echo '      "transport": "http",'
echo "      \"url\": \"https://$NGROK_DOMAIN\""
echo '    }'
echo '  }'
echo '}'
echo ""
echo "=============================================="
echo ""
echo "✅ Server is running!"
echo "Press Ctrl+C to stop"
echo ""

# Keep running
wait