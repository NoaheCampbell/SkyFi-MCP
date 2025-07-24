#!/bin/bash
# Quick test script for remote MCP connection

echo "MCP Remote Connection Test"
echo "========================="

# Get connection details
read -p "Server username: " SERVER_USER
read -p "Server IP address: " SERVER_IP
read -p "Path to mcp-skyfi on server [/Users/$SERVER_USER/mcp-skyfi]: " SERVER_PATH
SERVER_PATH=${SERVER_PATH:-/Users/$SERVER_USER/mcp-skyfi}

echo
echo "Testing SSH connection..."
ssh -o ConnectTimeout=5 $SERVER_USER@$SERVER_IP "echo 'SSH connection successful!'"

if [ $? -ne 0 ]; then
    echo "❌ SSH connection failed. Please check:"
    echo "   - SSH is enabled on server"
    echo "   - Username and IP are correct"
    echo "   - Both machines are on same network"
    exit 1
fi

echo
echo "Testing MCP server..."
ssh $SERVER_USER@$SERVER_IP "cd $SERVER_PATH && python3 -c 'import mcp_skyfi; print(\"MCP module found!\")'"

if [ $? -ne 0 ]; then
    echo "❌ MCP server not found. Please check:"
    echo "   - Path is correct: $SERVER_PATH"
    echo "   - MCP server is installed on server"
    exit 1
fi

echo
echo "✅ Everything looks good!"
echo
echo "Add this to your claude_desktop_config.json:"
echo
cat << EOF
{
  "mcpServers": {
    "skyfi-remote": {
      "command": "ssh",
      "args": [
        "$SERVER_USER@$SERVER_IP",
        "$SERVER_PATH/run-server.sh"
      ]
    }
  }
}
EOF