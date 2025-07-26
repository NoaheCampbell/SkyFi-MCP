# Public SkyFi MCP Server Setup

This guide explains how to run a public SkyFi MCP server that multiple users can connect to with their own API keys.

## How It Works

1. You run one MCP server instance on AWS
2. Ngrok provides a secure public URL
3. Users connect via the ngrok URL
4. Each user provides their own SkyFi API key
5. The server uses their key for their requests only

## Server Setup (AWS)

### 1. Launch EC2 Instance

```bash
# Recommended: t3.small or larger
# Open ports: 22 (SSH), 8080 (MCP)
```

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv -y

# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok

# Configure ngrok auth token (get from ngrok.com)
ngrok config add-authtoken YOUR_NGROK_AUTH_TOKEN
```

### 3. Install MCP Server

```bash
# Clone repository
git clone https://github.com/yourusername/mcp-skyfi.git
cd mcp-skyfi

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
```

### 4. Run the Public Server

```bash
# Make the script executable
chmod +x scripts/run_public_server.sh

# Run the server
./scripts/run_public_server.sh
```

This will output something like:
```
Starting SkyFi MCP server...
Starting ngrok tunnel...
Public SkyFi MCP server is running!
Forwarding https://abc123.ngrok.io -> http://localhost:8080
Share the ngrok URL with users
```

## User Setup

### 1. Configure Claude Desktop

Users add this to their Claude Desktop config:

```json
{
  "mcpServers": {
    "skyfi": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "https://abc123.ngrok.io/mcp",
        "-H", "Content-Type: application/json",
        "--no-buffer"
      ]
    }
  }
}
```

Or for better integration, use the MCP HTTP client:

```json
{
  "mcpServers": {
    "skyfi": {
      "transport": "http",
      "url": "https://abc123.ngrok.io"
    }
  }
}
```

### 2. First Time Use

When users first connect:

```
User: "Check SkyFi status"

Claude: I'll check the SkyFi authentication status.
[Uses skyfi_check_auth]

❌ No API key configured!

To use SkyFi tools, you must first set your API key:

1. Get your API key from https://app.skyfi.com
2. Use: skyfi_set_api_key with your key

User: "Set my API key to sk-abc123..."

Claude: I'll set your SkyFi API key.
[Uses skyfi_set_api_key]

✅ API key set and verified successfully!

Authenticated as: user@example.com
Account type: Pro

You can now use all SkyFi features!
```

## Security Features

### For Server Operators

- ✅ No API keys stored on server
- ✅ Ngrok provides HTTPS encryption
- ✅ Can add rate limiting via ngrok
- ✅ Can restrict access via ngrok auth
- ✅ Server logs don't contain API keys

### For Users

- ✅ API key only sent when needed
- ✅ Key is validated before use
- ✅ Each user uses their own key
- ✅ Keys expire with session
- ✅ No cross-user contamination

## Advanced Configuration

### Custom Domain

```bash
# Use custom domain with ngrok
ngrok http 8080 --domain=skyfi-mcp.yourdomain.com
```

### Authentication

Add basic auth to ngrok:

```bash
ngrok http 8080 --basic-auth="user:password"
```

### Rate Limiting

Configure in ngrok dashboard or add to server:

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/mcp")
@limiter.limit("100/hour")
async def handle_mcp(request: Request):
    # Handle MCP request
```

### Monitoring

```bash
# Add logging
export MCP_LOG_LEVEL=DEBUG

# Monitor with systemd
sudo systemctl status skyfi-mcp

# Check ngrok status
curl http://localhost:4040/api/tunnels
```

## Cost Considerations

### Server Costs
- EC2 t3.small: ~$15/month
- Ngrok Pro: $20/month (for custom domains)
- Total: ~$35/month

### User Costs
- Each user pays for their own SkyFi API usage
- No shared billing or cost allocation needed

## Limitations

1. **Session State**: API keys are per-session, users must re-enter after disconnect
2. **Concurrency**: Single server instance may have limits
3. **Latency**: Adds network hop vs local server
4. **Ngrok Limits**: Free tier has connection limits

## Alternative: Docker Deployment

For easier deployment, use Docker:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8080
CMD ["python", "-m", "mcp_skyfi", "--transport", "http", "--port", "8080"]
```

Then run with:
```bash
docker build -t skyfi-mcp .
docker run -p 8080:8080 skyfi-mcp
```

This public server approach eliminates the need for users to:
- Install anything locally
- Manage SSH keys
- Configure AWS credentials
- Run their own servers

They just need their SkyFi API key and the ngrok URL!