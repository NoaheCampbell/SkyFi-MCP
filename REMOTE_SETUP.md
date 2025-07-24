# Remote MCP Server Setup Guide

This guide helps you set up the MCP SkyFi server on one machine and connect to it from another.

## Server Machine Setup

### 1. Enable SSH Access

On the server machine:
```bash
# macOS: Enable Remote Login
sudo systemsetup -setremotelogin on

# Or via System Preferences:
# System Preferences > Sharing > Remote Login ✓
```

### 2. Get Server Info

```bash
# Get your username
whoami

# Get your IP address
# macOS:
ifconfig | grep "inet " | grep -v 127.0.0.1

# You'll see something like: inet 192.168.1.100
```

### 3. Install MCP Server

```bash
# Clone/copy the mcp-skyfi folder to server
cd ~
# Copy your mcp-skyfi folder here

# Install dependencies
cd mcp-skyfi
pip3 install -e .

# Test the server locally
./run-server.sh
# Press Ctrl+C to stop
```

### 4. Test SSH Access

From your server machine, note:
- Username: `your-username`
- IP Address: `192.168.x.x`
- MCP Path: `/Users/your-username/mcp-skyfi`

## Client Machine Setup

### 1. Test SSH Connection

From the client machine:
```bash
# Test basic SSH
ssh your-username@192.168.x.x

# Test running MCP via SSH
ssh your-username@192.168.x.x "/Users/your-username/mcp-skyfi/run-server.sh"
```

### 2. Set Up SSH Key (Optional but Recommended)

```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096

# Copy to server
ssh-copy-id your-username@192.168.x.x
```

### 3. Configure Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "skyfi-remote": {
      "command": "ssh",
      "args": [
        "your-username@192.168.x.x",
        "/Users/your-username/mcp-skyfi/run-server.sh"
      ]
    }
  }
}
```

With SSH key:
```json
{
  "mcpServers": {
    "skyfi-remote": {
      "command": "ssh",
      "args": [
        "-i", "/Users/client-user/.ssh/id_rsa",
        "your-username@192.168.x.x",
        "/Users/your-username/mcp-skyfi/run-server.sh"
      ]
    }
  }
}
```

### 4. Test in Claude Desktop

1. Save the config
2. Restart Claude Desktop
3. Look for "skyfi-remote" in the MCP servers
4. Test with: "Get my SkyFi user info"

## Troubleshooting

### "Permission denied"
- Check SSH is enabled on server
- Verify username and password
- Try setting up SSH keys

### "Connection refused"
- Check server IP address
- Ensure both machines are on same network
- Check firewall settings

### "Command not found"
- Verify the path to mcp-skyfi is correct
- Ensure Python 3 is installed on server
- Check run-server.sh is executable

### Tools don't appear
- Click trash icon next to server in Claude Desktop
- Check SSH works manually first
- Look for errors in Claude Desktop developer console

## Security Notes

For local testing this is fine, but for production:
1. Use SSH keys instead of passwords
2. Restrict SSH access to specific IPs
3. Move API keys to server environment variables
4. Consider using a VPN for remote access

## Next Steps

Once this works locally, you can:
1. Move server to cloud (AWS, DigitalOcean, etc.)
2. Use domain name instead of IP
3. Set up proper monitoring
4. Add SSL/TLS for additional security