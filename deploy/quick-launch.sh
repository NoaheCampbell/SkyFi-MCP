#!/bin/bash
# Quick setup script to run on AWS instance

set -e

echo "=== MCP SkyFi Quick Setup ==="

# Update system
sudo apt update
sudo apt install -y python3 python3-pip socat git

# Clone repository
git clone https://github.com/NoaheCampbell/SkyFi-MCP.git

cd SkyFi-MCP

# Install Python package
pip3 install -e .

# Create startup script
cat > start-mcp.sh << 'EOF'
#!/bin/bash
cd $(dirname $0)
echo "Starting MCP server on port 5456..."
echo "To stop: Ctrl+C"
socat TCP-LISTEN:5456,fork,reuseaddr EXEC:"python3 -m mcp_skyfi"
EOF
chmod +x start-mcp.sh

# Create systemd service for auto-start
sudo tee /etc/systemd/system/mcp-skyfi.service > /dev/null << EOF
[Unit]
Description=MCP SkyFi Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/SkyFi-MCP
ExecStart=/usr/bin/socat TCP-LISTEN:5456,fork,reuseaddr EXEC:"python3 -m mcp_skyfi"
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable mcp-skyfi
sudo systemctl start mcp-skyfi

echo
echo "✅ Setup complete!"
echo "Service status:"
sudo systemctl status mcp-skyfi --no-pager

echo
echo "Your server IP will be shown after launch"
echo "Test with: nc YOUR_IP 5456"