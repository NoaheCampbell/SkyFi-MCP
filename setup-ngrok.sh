#!/bin/bash
# Setup script for ngrok tunneling with socat bridge

echo "Setting up ngrok for MCP server remote access..."

# Check dependencies
if ! command -v ngrok &> /dev/null; then
    echo "ngrok not found. Please install it:"
    echo "  brew install ngrok"
    exit 1
fi

if ! command -v socat &> /dev/null; then
    echo "socat not found. Please install it:"
    echo "  brew install socat"
    exit 1
fi

# Use a different port to avoid conflicts
PORT=5123

# Kill any existing processes
pkill -f "socat TCP-LISTEN:$PORT"
pkill -f "ngrok tcp $PORT"

# Start socat to bridge TCP to the MCP server
echo "Starting socat bridge on port $PORT..."
cd "$(dirname "$0")"
socat TCP-LISTEN:$PORT,fork,reuseaddr EXEC:"python3 -m mcp_skyfi" &
SOCAT_PID=$!

# Give socat time to start
sleep 2

# Create ngrok tunnel
echo "Creating ngrok tunnel..."
ngrok tcp $PORT > /dev/null 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
echo "Waiting for ngrok to initialize..."
sleep 5

# Extract tunnel URL with retries
echo "Getting tunnel URL..."
for i in {1..10}; do
    RESPONSE=$(curl -s http://localhost:4040/api/tunnels)
    if [ ! -z "$RESPONSE" ]; then
        TUNNEL_URL=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'tunnels' in data and data['tunnels']:
        print(data['tunnels'][0]['public_url'])
except:
    pass
" 2>/dev/null)
        if [ ! -z "$TUNNEL_URL" ]; then
            break
        fi
    fi
    echo "Waiting for tunnel... (attempt $i/10)"
    sleep 2
done

if [ -z "$TUNNEL_URL" ]; then
    echo "Failed to get ngrok tunnel URL"
    echo "Response from ngrok: $RESPONSE"
    echo "Make sure ngrok is authenticated. Run: ngrok authtoken YOUR_TOKEN"
    kill $SOCAT_PID $NGROK_PID 2>/dev/null
    exit 1
fi

# Extract host and port
TUNNEL_HOST=$(echo $TUNNEL_URL | sed 's/tcp:\/\///' | cut -d: -f1)
TUNNEL_PORT=$(echo $TUNNEL_URL | sed 's/tcp:\/\///' | cut -d: -f2)

echo
echo "✅ Server is running!"
echo "Tunnel URL: $TUNNEL_URL"
echo
echo "On your CLIENT machine:"
echo "1. First install socat: brew install socat"
echo "2. Add this to claude_desktop_config.json:"
echo
cat << EOF
{
  "mcpServers": {
    "skyfi-remote": {
      "command": "socat",
      "args": [
        "-,raw,echo=0",
        "TCP:$TUNNEL_HOST:$TUNNEL_PORT"
      ],
      "env": {
        "SKYFI_API_KEY": "YOUR_SKYFI_API_KEY_HERE",
        "SKYFI_COST_LIMIT": "40.0",
        "SKYFI_FORCE_LOWEST_COST": "true",
        "SKYFI_ENABLE_ORDERING": "true",
        "SKYFI_REQUIRE_CONFIRMATION": "true",
        "SKYFI_REQUIRE_HUMAN_APPROVAL": "true",
        "SKYFI_MAX_ORDER_COST": "20.0",
        "SKYFI_DAILY_LIMIT": "40.0"
      }
    }
  }
}
EOF
echo
echo "Press Ctrl+C to stop the server"

# Cleanup function
cleanup() {
    echo "\nShutting down..."
    kill $SOCAT_PID $NGROK_PID 2>/dev/null
    exit
}

# Wait for interrupt
trap cleanup INT
wait