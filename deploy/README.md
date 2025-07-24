# MCP SkyFi Server Deployment Guide

## Option 1: DigitalOcean (Recommended - $5/month)

### 1. Create Droplet
```bash
# Via DigitalOcean CLI
doctl compute droplet create mcp-skyfi \
  --region sfo3 \
  --size s-1vcpu-1gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys YOUR_SSH_KEY_ID
```

Or use the web interface:
- Ubuntu 22.04
- Basic ($5/month)
- Any region close to you

### 2. Initial Setup
SSH into your server:
```bash
ssh root@YOUR_SERVER_IP
```

Run the setup script:
```bash
# Update system
apt update && apt upgrade -y

# Install Python and dependencies
apt install -y python3 python3-pip socat supervisor

# Create app user
useradd -m -s /bin/bash mcp
su - mcp

# Clone your repository
git clone https://github.com/YOUR_USERNAME/mcp-skyfi.git
cd mcp-skyfi

# Install Python packages
pip3 install -e .
```

### 3. Configure Environment
Create `/home/mcp/.env`:
```bash
# DON'T store API key on server - client will provide it
# Only server-specific settings here
MCP_PORT=5456
```

### 4. Set Up Service
Create `/etc/supervisor/conf.d/mcp-skyfi.conf`:
```ini
[program:mcp-skyfi]
command=socat TCP-LISTEN:5456,fork,reuseaddr EXEC:"python3 -m mcp_skyfi"
directory=/home/mcp/mcp-skyfi
user=mcp
autostart=true
autorestart=true
stderr_logfile=/var/log/mcp-skyfi.err.log
stdout_logfile=/var/log/mcp-skyfi.out.log
environment=PATH="/home/mcp/.local/bin:/usr/bin"
```

### 5. Configure Firewall
```bash
# Allow only the MCP port
ufw allow 5456/tcp
ufw enable
```

### 6. Start Service
```bash
supervisorctl reload
supervisorctl start mcp-skyfi
```

### 7. Client Configuration
```json
{
  "mcpServers": {
    "skyfi-remote": {
      "command": "socat",
      "args": [
        "-,raw,echo=0",
        "TCP:YOUR_SERVER_IP:5456"
      ],
      "env": {
        "SKYFI_API_KEY": "your-api-key",
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
```

## Option 2: AWS EC2 (Free tier available)

### 1. Launch Instance
- AMI: Ubuntu Server 22.04 LTS
- Instance Type: t2.micro (free tier)
- Security Group: Allow TCP port 5456 from your IP

### 2. Setup (same as DigitalOcean steps 2-6)

## Option 3: Railway/Render (Easiest - $5/month)

### Using Railway
1. Create `railway.toml`:
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "socat TCP-LISTEN:$PORT,fork,reuseaddr EXEC:'python3 -m mcp_skyfi'"
```

2. Deploy:
```bash
railway login
railway up
```

3. Get URL from Railway dashboard

## Security Best Practices

1. **API Key Management**: Never store API keys on the server. Always pass from client.

2. **IP Whitelisting**: Restrict access to your IP:
```bash
ufw allow from YOUR_HOME_IP to any port 5456
```

3. **SSL/TLS**: For production, use stunnel:
```bash
apt install stunnel4
# Configure /etc/stunnel/stunnel.conf
```

4. **Monitoring**: Set up basic monitoring:
```bash
# Check if service is running
supervisorctl status mcp-skyfi

# Monitor logs
tail -f /var/log/mcp-skyfi.err.log
```

## Quick Start Script

Save as `deploy.sh` on your server:
```bash
#!/bin/bash
set -e

echo "Setting up MCP SkyFi Server..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip socat supervisor git

# Create service user
sudo useradd -m -s /bin/bash mcp || true

# Clone repository
sudo -u mcp git clone https://github.com/YOUR_USERNAME/mcp-skyfi.git /home/mcp/mcp-skyfi

# Install Python packages
cd /home/mcp/mcp-skyfi
sudo -u mcp pip3 install -e .

# Create supervisor config
sudo tee /etc/supervisor/conf.d/mcp-skyfi.conf > /dev/null <<EOF
[program:mcp-skyfi]
command=socat TCP-LISTEN:5456,fork,reuseaddr EXEC:"python3 -m mcp_skyfi"
directory=/home/mcp/mcp-skyfi
user=mcp
autostart=true
autorestart=true
stderr_logfile=/var/log/mcp-skyfi.err.log
stdout_logfile=/var/log/mcp-skyfi.out.log
environment=PATH="/home/mcp/.local/bin:/usr/bin"
EOF

# Configure firewall
sudo ufw allow 5456/tcp
sudo ufw --force enable

# Start service
sudo supervisorctl reload
sudo supervisorctl start mcp-skyfi

echo "✅ MCP SkyFi Server is running on port 5456"
echo "Server IP: $(curl -s ifconfig.me)"
```

Run with:
```bash
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/mcp-skyfi/main/deploy.sh | bash
```