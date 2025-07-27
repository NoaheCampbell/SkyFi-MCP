# AWS Deployment Guide

This guide covers deploying the SkyFi MCP server on AWS for remote access or team deployments.

## When to Use AWS Deployment

Consider AWS deployment if you need:
- Remote access to the MCP server from multiple locations
- Team access with centralized configuration
- Integration with AWS services (S3 delivery, Secrets Manager)
- Production-grade deployment with monitoring

For personal use, the local installation is simpler and recommended.

## Quick Start

### 1. Launch EC2 Instance

```bash
# Use Amazon Linux 2023 or Ubuntu 22.04
# Instance type: t3.micro is sufficient
# Security group: Allow SSH (port 22) from your IP
```

### 2. Install MCP Server

```bash
# Connect to instance
ssh ec2-user@your-instance-ip

# Install Python and dependencies
sudo yum install python3.11 python3.11-pip git -y  # Amazon Linux
# OR
sudo apt update && sudo apt install python3.11 python3-pip git -y  # Ubuntu

# Install MCP server
pip3 install git+https://github.com/NoaheCampbell/SkyFi-MCP.git
```

### 3. Configure Authentication

Choose one of these methods:

#### Option A: AWS Secrets Manager (Recommended for Production)

```bash
# Store API key
aws secretsmanager create-secret \
  --name skyfi/api-key \
  --secret-string '{"api_key":"your-skyfi-api-key-here"}'

# Grant EC2 instance access via IAM role
```

#### Option B: Environment Variables (Simple)

```bash
# Add to ~/.bashrc or systemd service
export SKYFI_API_KEY="your-skyfi-api-key-here"
```

### 4. Configure Claude Desktop

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "skyfi-remote": {
      "command": "ssh",
      "args": [
        "ec2-user@your-instance-ip",
        "python3 -m mcp_skyfi"
      ]
    }
  }
}
```

## Advanced Configuration

### Using Ngrok for HTTPS Access

If SSH access is not available:

```bash
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok

# Configure and start
ngrok config add-authtoken YOUR_NGROK_TOKEN
ngrok http 8080
```

### Systemd Service

Create `/etc/systemd/system/skyfi-mcp.service`:

```ini
[Unit]
Description=SkyFi MCP Server
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user
Environment="SKYFI_API_KEY=your-key-here"
ExecStart=/usr/bin/python3 -m mcp_skyfi
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable skyfi-mcp
sudo systemctl start skyfi-mcp
```

## Security Best Practices

1. **Never commit API keys** - Use Secrets Manager or environment variables
2. **Restrict SSH access** - Only allow from known IPs
3. **Use IAM roles** - Don't store AWS credentials on the instance
4. **Enable CloudWatch logs** - Monitor for unauthorized access
5. **Regular updates** - Keep the instance and software updated

## Troubleshooting

### Connection Issues
- Check security group allows SSH from your IP
- Verify instance is running
- Test with: `ssh -v user@instance-ip`

### Authentication Failures
- Verify API key is set correctly
- Check IAM role has Secrets Manager access
- Test locally first: `SKYFI_API_KEY=xxx python3 -m mcp_skyfi`

### Performance Issues
- Upgrade instance type if needed
- Check CloudWatch metrics
- Enable debug logging: `export MCP_LOG_LEVEL=DEBUG`

## Cost Optimization

- Use t3.micro or t4g.micro instances (free tier eligible)
- Stop instances when not in use
- Use spot instances for development
- Set up auto-shutdown schedules

For more deployment options, see the main README.