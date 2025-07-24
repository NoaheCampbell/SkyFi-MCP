#!/bin/bash
# Test script for HTTP server

echo "Testing SkyFi MCP HTTP Server..."
echo ""

# Test root endpoint
echo "1. Testing root endpoint..."
curl -s http://localhost:8000/ | python3 -m json.tool
echo ""

# Test health endpoint
echo "2. Testing health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

# Test SSE endpoint without auth
echo "3. Testing SSE endpoint without authentication..."
curl -N -H "Accept: text/event-stream" http://localhost:8000/sse &
PID=$!
sleep 2
kill $PID 2>/dev/null
echo ""

# Test SSE endpoint with auth
echo "4. Testing SSE endpoint with authentication..."
echo "Replace YOUR_API_KEY with your actual API key:"
echo 'curl -N -H "Authorization: Bearer YOUR_API_KEY" -H "Accept: text/event-stream" http://localhost:8000/sse'