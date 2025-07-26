#!/bin/bash
# Run the public SkyFi MCP server with ngrok

# Start the MCP server on HTTP transport
echo "Starting SkyFi MCP server..."
python -m mcp_skyfi --transport http --port 8080 &
SERVER_PID=$!

# Give the server time to start
sleep 3

# Start ngrok
echo "Starting ngrok tunnel..."
ngrok http 8080 --log stdout &
NGROK_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $SERVER_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    exit
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Keep script running
echo "Public SkyFi MCP server is running!"
echo "Share the ngrok URL with users"
echo "Users must set their own API key using skyfi_set_api_key"
echo "Press Ctrl+C to stop"

# Wait for processes
wait