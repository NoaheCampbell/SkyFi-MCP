# AWS Setup Guide for SkyFi MCP Server

## Quick Setup (5 minutes)

### 1. Connect to Your AWS Instance

```bash
ssh ubuntu@your-aws-instance-ip
```

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and Git
sudo apt install -y python3.10 python3-pip git

# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

### 3. Clone and Setup the Server

```bash
# Clone the repository
git clone https://github.com/NoaheCampbell/SkyFi-MCP.git
cd SkyFi-MCP

# Install Python dependencies
pip3 install -e .

# Set up configuration
cp config/.env.example .env
nano .env
```

Edit `.env` with your details:
```
NGROK_DOMAIN=your-reserved-domain.ngrok-free.app
NGROK_AUTHTOKEN=your_ngrok_auth_token_here
MCP_PORT=8080
AUTH_PORT=8081
```

### 4. Configure Ngrok

```bash
# Add your ngrok auth token
ngrok config add-authtoken YOUR_NGROK_AUTH_TOKEN
```

### 5. Start the Server

```bash
# Make the script executable
chmod +x scripts/start_production_server.sh

# Start the server
./scripts/start_production_server.sh
```

The server will output:
```
Starting SkyFi MCP Server...
Auth server running at: https://your-domain.ngrok-free.app
MCP server listening on port 8080
```

### 6. Configure Claude Desktop

On your local machine, update Claude Desktop config:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "skyfi": {
      "command": "python3",
      "args": ["-m", "mcp_skyfi"],
      "env": {
        "SKYFI_AUTH_URL": "https://your-domain.ngrok-free.app",
        "SKYFI_SECURE_MODE": "true"
      }
    }
  }
}
```

### 7. Test the Setup

1. Restart Claude Desktop
2. Ask Claude: "Authenticate with SkyFi"
3. Follow the secure web authentication flow

## Running as a Service (Optional)

To keep the server running permanently:

```bash
# Copy the service file
sudo cp scripts/skyfi-mcp.service /etc/systemd/system/

# Edit the service file with your user and paths
sudo nano /etc/systemd/system/skyfi-mcp.service

# Enable and start the service
sudo systemctl enable skyfi-mcp
sudo systemctl start skyfi-mcp

# Check status
sudo systemctl status skyfi-mcp
```

## Security Notes

- The server uses ngrok to provide a secure HTTPS endpoint
- API keys are never transmitted through the LLM chat
- Authentication uses temporary session tokens
- All communication is encrypted

## Troubleshooting

### Port Already in Use
```bash
# Find and kill the process using port 8080
sudo lsof -i :8080
sudo kill -9 <PID>
```

### Ngrok Not Starting
- Verify your auth token: `ngrok config check`
- Check your reserved domain is correct
- Ensure ports 8080 and 8081 are not blocked by AWS security group

### Can't Connect from Claude
- Check AWS security group allows inbound traffic on port 8080
- Verify ngrok tunnel is running: `curl https://your-domain.ngrok-free.app/health`
- Check server logs: `tail -f logs/skyfi-mcp.log`

## Next Steps

- Monitor usage: `tail -f logs/skyfi-mcp.log`
- Update the server: `git pull && pip3 install -e .`
- Check ngrok status: https://dashboard.ngrok.com