#!/bin/bash
# Alternative ngrok setup using HTTP tunnel (no credit card required)

echo "Setting up ngrok HTTP tunnel for MCP server..."

# Check dependencies
if ! command -v ngrok &> /dev/null; then
    echo "ngrok not found. Please install it:"
    echo "  brew install ngrok"
    exit 1
fi

# Use a different port to avoid conflicts
PORT=8123

# Kill any existing processes
pkill -f "python.*http_bridge.py"
pkill -f "ngrok http $PORT"

# Create HTTP bridge server
echo "Creating HTTP-to-STDIO bridge..."
cd "$(dirname "$0")"

cat > http_bridge.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import subprocess
import json
from aiohttp import web
import sys
import os

async def handle_mcp_request(request):
    """Handle MCP requests over HTTP"""
    try:
        # Get the request body
        body = await request.read()
        
        # Start MCP process for this request
        env = os.environ.copy()
        # Add environment variables from headers
        for key, value in request.headers.items():
            if key.startswith('X-Env-'):
                env_key = key[6:].replace('-', '_')
                env[env_key] = value
        
        # Run MCP command
        process = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'mcp_skyfi',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        # Send request and get response
        stdout, stderr = await process.communicate(body)
        
        if stderr:
            print(f"MCP stderr: {stderr.decode()}", file=sys.stderr)
        
        return web.Response(body=stdout, content_type='application/json')
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return web.Response(text=str(e), status=500)

async def health_check(request):
    """Health check endpoint"""
    return web.Response(text="OK")

app = web.Application()
app.router.add_post('/mcp', handle_mcp_request)
app.router.add_get('/health', health_check)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8123'))
    print(f"HTTP bridge listening on port {port}", file=sys.stderr)
    web.run_app(app, host='0.0.0.0', port=port)
EOF

# Install aiohttp if needed
pip3 install aiohttp >/dev/null 2>&1

# Start HTTP bridge
python3 http_bridge.py &
BRIDGE_PID=$!

# Give bridge time to start
sleep 2

# Create ngrok tunnel
echo "Creating ngrok HTTP tunnel..."
ngrok http $PORT > /dev/null 2>&1 &
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
        for tunnel in data['tunnels']:
            if tunnel.get('proto') == 'https':
                print(tunnel['public_url'])
                break
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
    kill $BRIDGE_PID $NGROK_PID 2>/dev/null
    exit 1
fi

echo
echo "✅ Server is running!"
echo "Tunnel URL: $TUNNEL_URL"
echo
echo "On your CLIENT machine:"
echo "1. Copy the http-client-wrapper.py file from this directory"
echo "2. Add this to claude_desktop_config.json:"
echo
cat << EOF
{
  "mcpServers": {
    "skyfi-remote": {
      "command": "python3",
      "args": [
        "/path/to/http-client-wrapper.py",
        "$TUNNEL_URL/mcp"
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
    kill $BRIDGE_PID $NGROK_PID 2>/dev/null
    rm -f http_bridge.py
    exit
}

# Wait for interrupt
trap cleanup INT
wait