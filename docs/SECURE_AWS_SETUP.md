# Secure AWS Setup for SkyFi MCP Server

This guide shows how to securely pass your SkyFi API key as an HTTPS header without storing it on the AWS instance.

## Overview

The solution uses a local transport wrapper that:
1. Reads your API key from your LOCAL environment
2. Injects it into every MCP request as a header
3. Forwards requests to the AWS instance via SSH
4. The AWS instance never stores or sees your API key in logs

## Setup Steps

### 1. On Your Local Machine

#### Install the Transport Wrapper

```bash
# Clone the repository locally
git clone https://github.com/yourusername/mcp-skyfi.git
cd mcp-skyfi

# Make the wrapper executable
chmod +x examples/mcp-transport-wrapper.py
# or
chmod +x examples/mcp-transport-wrapper.js
```

#### Set Your API Key Locally

```bash
# Add to your ~/.bashrc or ~/.zshrc
export SKYFI_API_KEY="sk-your-actual-api-key"

# Also set the AWS instance details
export MCP_SKYFI_HOST="your-ec2-instance.amazonaws.com"
export MCP_SKYFI_USER="ec2-user"
```

### 2. On AWS Instance

Deploy the MCP server WITHOUT any API keys:

```bash
# Install MCP server
git clone https://github.com/yourusername/mcp-skyfi.git
cd mcp-skyfi
python3 -m venv venv
source venv/bin/activate
pip install -e .

# No need to set SKYFI_API_KEY!
```

### 3. Configure Claude Desktop

Edit your Claude Desktop configuration:

**Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "skyfi": {
      "command": "python3",
      "args": [
        "/path/to/your/local/mcp-skyfi/examples/mcp-transport-wrapper.py"
      ]
    }
  }
}
```

Or if using Node.js:

```json
{
  "mcpServers": {
    "skyfi": {
      "command": "node",
      "args": [
        "/path/to/your/local/mcp-skyfi/examples/mcp-transport-wrapper.js"
      ]
    }
  }
}
```

### 4. How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Claude Desktop │────►│ Local Transport │────►│   AWS Instance  │
│                 │     │    Wrapper      │ SSH │   (MCP Server)  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        Injects API Key
                        from local env
                        into headers
```

1. Claude Desktop sends MCP requests to the local wrapper
2. The wrapper reads your API key from your LOCAL environment
3. It injects the key as an `X-Skyfi-Api-Key` header
4. The modified request is sent via SSH to AWS
5. The MCP server on AWS uses the header for authentication
6. Your API key never touches the AWS instance's disk or environment

## Security Benefits

✅ **API key never stored on AWS** - Only exists in request headers  
✅ **No environment variables on server** - Can't be leaked via logs  
✅ **Encrypted in transit** - SSH provides encryption  
✅ **Per-session authentication** - Each Claude session authenticates separately  
✅ **No manual configuration** - Set once locally, works forever  

## Testing

Test the setup:

```bash
# Check SSH connection
ssh ec2-user@your-instance.amazonaws.com "echo Connected"

# Test the wrapper directly
echo '{"method":"list_tools","id":1}' | python3 examples/mcp-transport-wrapper.py

# In Claude Desktop
"Check what tools are available"
```

## Troubleshooting

### "API key not configured" error

The header injection might not be working. Check:
- `echo $SKYFI_API_KEY` shows your key locally
- The wrapper script has correct permissions
- SSH connection works without password prompts

### Connection timeouts

- Check AWS security group allows SSH from your IP
- Verify the instance is running
- Test SSH connection manually first

### Debug mode

Enable debug logging:

```bash
export DEBUG=1
# Then restart Claude Desktop
```

## Advanced: Multiple API Keys

For multiple users, modify the wrapper to read from different sources:

```python
# In mcp-transport-wrapper.py
if os.environ.get('USER') == 'alice':
    API_KEY = os.environ.get('ALICE_SKYFI_KEY')
elif os.environ.get('USER') == 'bob':
    API_KEY = os.environ.get('BOB_SKYFI_KEY')
```

## Production Considerations

For production use, consider:

1. **Use AWS Systems Manager Session Manager** instead of direct SSH
2. **Implement request signing** with HMAC for additional security
3. **Add request rate limiting** in the wrapper
4. **Log requests locally** (without API keys) for audit trails
5. **Use a dedicated proxy server** instead of SSH for better performance

This approach ensures your API key remains secure while allowing seamless use of the MCP server on AWS!