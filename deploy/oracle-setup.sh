#!/bin/bash
# Setup script for Oracle Cloud Always Free instance

set -e

echo "=== MCP SkyFi Server Setup for Oracle Cloud ==="

# Install dependencies
echo "Installing dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip git

# Install socat from source (Oracle's repos might be limited)
cd /tmp
wget http://www.dest-unreach.org/socat/download/socat-1.7.4.4.tar.gz
tar xvzf socat-1.7.4.4.tar.gz
cd socat-1.7.4.4
./configure
make
sudo make install

# Create service user
echo "Creating service user..."
sudo useradd -m -s /bin/bash mcp 2>/dev/null || echo "User exists"

# Get the code
echo "Setting up application..."
cd /home/mcp
sudo -u mcp git clone https://github.com/YOUR_USERNAME/mcp-skyfi.git 2>/dev/null || echo "Repo exists"
cd mcp-skyfi
sudo -u mcp git pull

# Install Python packages
echo "Installing Python packages..."
sudo -u mcp pip3 install -e .

# Create systemd service
echo "Creating service..."
sudo tee /etc/systemd/system/mcp-skyfi.service > /dev/null <<EOF
[Unit]
Description=MCP SkyFi Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/home/mcp/mcp-skyfi
ExecStart=/usr/local/bin/socat TCP-LISTEN:5456,fork,reuseaddr EXEC:"python3 -m mcp_skyfi"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Oracle firewall (iptables)
echo "Configuring firewall..."
sudo iptables -I INPUT -p tcp --dport 5456 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables/rules.v4

# Enable and start service
echo "Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable mcp-skyfi
sudo systemctl start mcp-skyfi

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)

echo
echo "=== Setup Complete! ==="
echo
echo "Server is running at: $PUBLIC_IP:5456"
echo
echo "IMPORTANT: In Oracle Cloud Console, add this security rule:"
echo "  - Go to your instance → Virtual Cloud Network"
echo "  - Security Lists → Default Security List"
echo "  - Add Ingress Rule:"
echo "    - Source: 0.0.0.0/0"
echo "    - Destination Port: 5456"
echo "    - Protocol: TCP"
echo
echo "Then update your claude_desktop_config.json:"
echo "\"command\": \"nc\","
echo "\"args\": [\"$PUBLIC_IP\", \"5456\"]"