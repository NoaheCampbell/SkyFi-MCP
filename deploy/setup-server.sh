#!/bin/bash
# Quick deployment script for Ubuntu servers

set -e

echo "=== MCP SkyFi Server Setup ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "Please run as root (use sudo)"
   exit 1
fi

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install dependencies
echo "Installing dependencies..."
apt install -y python3 python3-pip socat supervisor git ufw

# Create service user
echo "Creating service user..."
useradd -m -s /bin/bash mcp 2>/dev/null || echo "User 'mcp' already exists"

# Clone repository
echo "Setting up application..."
REPO_PATH="/home/mcp/mcp-skyfi"
if [ -d "$REPO_PATH" ]; then
    echo "Repository already exists, pulling latest..."
    sudo -u mcp bash -c "cd $REPO_PATH && git pull"
else
    echo "Cloning repository..."
    echo "Enter your repository URL (or press Enter for local copy):"
    read -r REPO_URL
    if [ -z "$REPO_URL" ]; then
        # Copy from current directory
        cp -r "$(dirname "$0")/.." "$REPO_PATH"
        chown -R mcp:mcp "$REPO_PATH"
    else
        sudo -u mcp git clone "$REPO_URL" "$REPO_PATH"
    fi
fi

# Install Python packages
echo "Installing Python packages..."
cd "$REPO_PATH"
sudo -u mcp pip3 install -e .

# Create supervisor config
echo "Configuring service..."
cat > /etc/supervisor/conf.d/mcp-skyfi.conf <<EOF
[program:mcp-skyfi]
command=socat TCP-LISTEN:5456,fork,reuseaddr EXEC:"python3 -m mcp_skyfi"
directory=/home/mcp/mcp-skyfi
user=mcp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/mcp-skyfi.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PATH="/home/mcp/.local/bin:/usr/bin",HOME="/home/mcp"
EOF

# Configure firewall
echo "Configuring firewall..."
ufw allow 22/tcp  # SSH
ufw allow 5456/tcp  # MCP
ufw --force enable

# Create systemd service as alternative
echo "Creating systemd service..."
cat > /etc/systemd/system/mcp-skyfi.service <<EOF
[Unit]
Description=MCP SkyFi Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/home/mcp/mcp-skyfi
ExecStart=/usr/bin/socat TCP-LISTEN:5456,fork,reuseaddr EXEC:"python3 -m mcp_skyfi"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "Starting service..."
systemctl daemon-reload
systemctl enable mcp-skyfi
systemctl start mcp-skyfi

# Also start with supervisor
supervisorctl reload
supervisorctl start mcp-skyfi 2>/dev/null || true

# Get server info
SERVER_IP=$(curl -s ifconfig.me)

echo
echo "=== Setup Complete! ==="
echo
echo "Server IP: $SERVER_IP"
echo "Port: 5456"
echo
echo "Add this to your claude_desktop_config.json:"
echo
cat <<JSON
{
  "mcpServers": {
    "skyfi-remote": {
      "command": "socat",
      "args": [
        "-,raw,echo=0",
        "TCP:$SERVER_IP:5456"
      ],
      "env": {
        "SKYFI_API_KEY": "your-api-key-here",
        "SKYFI_COST_LIMIT": "40.0"
      }
    }
  }
}
JSON
echo
echo "Commands:"
echo "  Check status: systemctl status mcp-skyfi"
echo "  View logs: journalctl -u mcp-skyfi -f"
echo "  Restart: systemctl restart mcp-skyfi"