# Production Setup Guide

This guide walks through setting up the SkyFi MCP server with your reserved ngrok domain.

## Prerequisites

- AWS EC2 instance (Ubuntu 22.04 recommended)
- Reserved ngrok domain (from ngrok.com)
- Python 3.11+

## Step 1: Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Install other dependencies
sudo apt install git nginx supervisor -y

# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

## Step 2: Clone and Configure

```bash
# Clone repository
cd ~
git clone https://github.com/yourusername/mcp-skyfi.git
cd mcp-skyfi

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Create config from example
cp config/.env.example .env
```

## Step 3: Configure Your Domain

Edit `.env` with your settings:

```bash
nano .env
```

```env
# Your reserved ngrok domain (without https://)
NGROK_DOMAIN=your-domain.ngrok-free.app

# Your ngrok auth token
NGROK_AUTHTOKEN=2abc123_YourActualTokenHere

# Server ports
MCP_PORT=8080
AUTH_PORT=8081
```

## Step 4: Test the Server

```bash
# Make script executable
chmod +x scripts/start_production_server.sh

# Test run
./scripts/start_production_server.sh
```

You should see:
```
==============================================
   SkyFi MCP Server - Production Mode
==============================================

🌐 Public URL: https://your-domain.ngrok-free.app
🔐 Auth URL: https://your-domain.ngrok-free.app/auth/[nonce]

📋 User Configuration for Claude Desktop:
...
```

Test by visiting `https://your-domain.ngrok-free.app` in a browser.

## Step 5: Set Up as System Service

```bash
# Create log directory
sudo mkdir -p /var/log/skyfi-mcp
sudo chown $USER:$USER /var/log/skyfi-mcp

# Copy service file
sudo cp scripts/skyfi-mcp.service /etc/systemd/system/

# Edit service file to match your paths
sudo nano /etc/systemd/system/skyfi-mcp.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable skyfi-mcp
sudo systemctl start skyfi-mcp

# Check status
sudo systemctl status skyfi-mcp
```

## Step 6: Set Up Log Rotation

```bash
sudo nano /etc/logrotate.d/skyfi-mcp
```

Add:
```
/var/log/skyfi-mcp/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 ubuntu ubuntu
}
```

## Step 7: Monitor the Service

```bash
# View logs
tail -f /var/log/skyfi-mcp/server.log

# Check ngrok status
curl http://localhost:4040/api/tunnels

# Restart if needed
sudo systemctl restart skyfi-mcp
```

## User Instructions

Share this with your users:

### For Claude Desktop Users:

1. Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "skyfi": {
      "transport": "http",
      "url": "https://your-domain.ngrok-free.app"
    }
  }
}
```

2. Restart Claude Desktop

3. In Claude, say: "Set up my SkyFi authentication"

4. Click the secure link provided

5. Enter your SkyFi API key on the web page

6. Return to Claude and start using SkyFi!

## Security Considerations

### Firewall Rules

```bash
# Only allow necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (redirect)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Ngrok Configuration

Your ngrok tunnel is already HTTPS secured, but you can add:

- **Basic Auth**: In ngrok dashboard, add basic auth to your endpoint
- **IP Restrictions**: Limit access to specific IP ranges
- **Request Headers**: Add custom headers for additional security

### Monitoring

Set up alerts for:
- High CPU/memory usage
- Unusual traffic patterns
- Authentication failures
- Service downtime

## Troubleshooting

### Service won't start
```bash
# Check logs
journalctl -u skyfi-mcp -n 50

# Check if ports are in use
sudo lsof -i :8080
sudo lsof -i :8081
```

### Ngrok connection issues
```bash
# Verify auth token
ngrok config check

# Test direct connection
curl http://localhost:8080

# Check ngrok status
curl http://localhost:4040/api/tunnels
```

### Authentication not working
- Check web server is running on port 8081
- Verify ngrok is forwarding both /auth and / paths
- Check browser console for errors

## Cost Management

With your ngrok reserved domain:
- **Personal plan**: $8/month for 1 domain
- **Pro plan**: $20/month for custom domains
- **EC2 costs**: ~$10-20/month for t3.small

Total: ~$18-40/month depending on setup

## Backup and Recovery

```bash
# Backup configuration
tar -czf skyfi-backup.tar.gz .env logs/

# Backup user sessions (if persistent)
cp -r /tmp/skyfi-sessions backup/

# Restore
tar -xzf skyfi-backup.tar.gz
```

Your server is now production-ready with secure authentication!