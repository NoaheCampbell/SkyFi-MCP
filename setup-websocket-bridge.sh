#!/bin/bash
# WebSocket bridge for MCP - allows JSON-only client config

echo "Setting up WebSocket bridge for MCP server..."

# Check dependencies
if ! command -v ngrok &> /dev/null; then
    echo "ngrok not found. Please install it:"
    echo "  brew install ngrok"
    exit 1
fi

# Install Python dependencies
pip3 install websockets aiohttp >/dev/null 2>&1

PORT=8457

# Kill existing processes
pkill -f "python.*websocket_bridge.py"
pkill -f "ngrok http $PORT"

cd "$(dirname "$0")"

# Create WebSocket bridge
cat > websocket_bridge.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import websockets
import subprocess
import json
import os
import sys

async def handle_websocket(websocket, path):
    """Handle WebSocket connection"""
    print(f"New connection from {websocket.remote_address}", file=sys.stderr)
    
    # Get environment from query params or headers
    env = os.environ.copy()
    
    # Start MCP process
    process = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'mcp_skyfi',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    
    # Forward messages between WebSocket and process
    async def ws_to_process():
        try:
            async for message in websocket:
                process.stdin.write(message.encode() + b'\n')
                await process.stdin.drain()
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            process.stdin.close()
    
    async def process_to_ws():
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            try:
                await websocket.send(line.decode().strip())
            except websockets.exceptions.ConnectionClosed:
                break
    
    # Run both tasks
    await asyncio.gather(ws_to_process(), process_to_ws())
    await process.wait()
    print(f"Connection closed from {websocket.remote_address}", file=sys.stderr)

async def main():
    port = int(os.environ.get('PORT', '8457'))
    print(f"WebSocket bridge listening on port {port}", file=sys.stderr)
    async with websockets.serve(handle_websocket, '0.0.0.0', port):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
EOF

# Start WebSocket bridge
python3 websocket_bridge.py &
BRIDGE_PID=$!
sleep 2

# Create ngrok tunnel
echo "Creating ngrok tunnel..."
ngrok http $PORT > /dev/null 2>&1 &
NGROK_PID=$!

echo "Waiting for ngrok..."
sleep 5

# Get tunnel URL
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
    kill $BRIDGE_PID $NGROK_PID 2>/dev/null
    exit 1
fi

# Convert https to wss
WS_URL=$(echo $TUNNEL_URL | sed 's/https:/wss:/')

echo
echo "✅ Server is running!"
echo
echo "UNFORTUNATELY: Claude Desktop doesn't support WebSocket connections directly."
echo "You still need a small client wrapper."
echo
echo "But wait... let me try one more approach with socat!"

# Kill WebSocket processes
kill $BRIDGE_PID $NGROK_PID 2>/dev/null

# Try TCP tunnel instead
echo
echo "Setting up TCP tunnel instead..."

# Start socat TCP to STDIO bridge
PORT=5456
socat TCP-LISTEN:$PORT,fork,reuseaddr EXEC:"python3 -m mcp_skyfi" &
SOCAT_PID=$!
sleep 2

# Create ngrok TCP tunnel
ngrok tcp $PORT > /dev/null 2>&1 &
NGROK_PID=$!
sleep 5

# Get TCP tunnel URL
for i in {1..5}; do
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
    echo "Waiting for TCP tunnel... (attempt $i/5)"
    sleep 2
done

if [ -z "$TUNNEL_URL" ]; then
    echo "Failed - ngrok requires a credit card for TCP endpoints"
    echo
    echo "SOLUTION: For true JSON-only config, you need to:"
    echo "1. Deploy this MCP server to a cloud VM with a public IP"
    echo "2. Run: socat TCP-LISTEN:5456,fork,reuseaddr EXEC:'python3 -m mcp_skyfi'"
    echo "3. Use this in claude_desktop_config.json:"
    echo
    cat << 'EOF'
{
  "mcpServers": {
    "skyfi-remote": {
      "command": "socat",
      "args": [
        "-,raw,echo=0",
        "TCP:YOUR_SERVER_IP:5456"
      ],
      "env": {
        "SKYFI_API_KEY": "your-key"
      }
    }
  }
}
EOF
    kill $SOCAT_PID $NGROK_PID 2>/dev/null
    exit 1
fi

# Extract host and port
TUNNEL_HOST=$(echo $TUNNEL_URL | sed 's/tcp:\/\///' | cut -d: -f1)
TUNNEL_PORT=$(echo $TUNNEL_URL | sed 's/tcp:\/\///' | cut -d: -f2)

echo
echo "✅ TCP tunnel ready!"
echo
echo "Add this to claude_desktop_config.json (JSON ONLY!):"
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
echo "NOTE: Client needs socat installed (brew install socat)"
echo "Press Ctrl+C to stop"

cleanup() {
    echo "\nShutting down..."
    kill $SOCAT_PID $NGROK_PID 2>/dev/null
    rm -f websocket_bridge.py
    exit
}

trap cleanup INT
wait