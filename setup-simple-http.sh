#!/bin/bash
# Simple HTTP server that works with curl in Claude Desktop

echo "Setting up simple HTTP tunnel for MCP server..."

# Check dependencies
if ! command -v ngrok &> /dev/null; then
    echo "ngrok not found. Please install it:"
    echo "  brew install ngrok"
    exit 1
fi

# Use a different port to avoid conflicts
PORT=8456

# Kill any existing processes
pkill -f "python.*simple_http_bridge.py"
pkill -f "ngrok http $PORT"

# Create simple HTTP bridge
echo "Creating HTTP bridge..."
cd "$(dirname "$0")"

cat > simple_http_bridge.py << 'EOF'
#!/usr/bin/env python3
import subprocess
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class MCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Read the request
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')
        
        # Set up environment
        env = os.environ.copy()
        
        # Run MCP command
        process = subprocess.Popen(
            ['python3', '-m', 'mcp_skyfi'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )
        
        # Get response
        stdout, stderr = process.communicate(body)
        
        # Send response
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(stdout.encode('utf-8'))
        
    def log_message(self, format, *args):
        # Suppress logs
        pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8456'))
    server = HTTPServer(('0.0.0.0', port), MCPHandler)
    print(f"HTTP bridge listening on port {port}")
    server.serve_forever()
EOF

# Start HTTP bridge
python3 simple_http_bridge.py &
BRIDGE_PID=$!
sleep 2

# Create ngrok tunnel
echo "Creating ngrok tunnel..."
ngrok http $PORT > /dev/null 2>&1 &
NGROK_PID=$!

# Wait for ngrok
echo "Waiting for ngrok to initialize..."
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

echo
echo "✅ Server is running at: $TUNNEL_URL"
echo
echo "Add this to claude_desktop_config.json on your CLIENT:"
echo
cat << EOF
{
  "mcpServers": {
    "skyfi-remote": {
      "command": "sh",
      "args": [
        "-c",
        "echo '\$SKYFI_API_KEY' | curl -s -X POST --data-binary @- $TUNNEL_URL"
      ],
      "env": {
        "SKYFI_API_KEY": "YOUR_SKYFI_API_KEY_HERE"
      }
    }
  }
}
EOF
echo
echo "Press Ctrl+C to stop the server"

cleanup() {
    echo "\nShutting down..."
    kill $BRIDGE_PID $NGROK_PID 2>/dev/null
    rm -f simple_http_bridge.py
    exit
}

trap cleanup INT
wait