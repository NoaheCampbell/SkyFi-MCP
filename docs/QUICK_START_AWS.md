# Quick Start: SkyFi MCP on AWS

## 3-Step Setup

### Step 1: Download the Launcher

Save this file to your computer: [skyfi-mcp-launcher.py](../examples/skyfi-mcp-launcher.py)

For example: `~/Documents/skyfi-mcp-launcher.py`

### Step 2: Edit the Launcher

Open the file and change these three lines:

```python
SKYFI_API_KEY = "sk-your-actual-api-key-here"  # Your SkyFi API key
AWS_HOST = "ec2-1-2-3-4.compute-1.amazonaws.com"  # Your AWS instance
AWS_USER = "ec2-user"  # Usually ec2-user or ubuntu
```

### Step 3: Configure Claude Desktop

Add this to your Claude Desktop config:

**Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "skyfi": {
      "command": "python3",
      "args": ["/Users/yourname/Documents/skyfi-mcp-launcher.py"]
    }
  }
}
```

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "skyfi": {
      "command": "python",
      "args": ["C:\\Users\\yourname\\Documents\\skyfi-mcp-launcher.py"]
    }
  }
}
```

## That's It! 🎉

Restart Claude Desktop and you can now use SkyFi commands. Your API key stays safely on your local computer.

## First Time Test

In Claude, try:
```
Search for satellite images of central park from last week
```

## Troubleshooting

If it doesn't work:

1. **Check SSH access**: Can you SSH to your AWS instance?
   ```bash
   ssh ec2-user@your-instance.com
   ```

2. **Check Python**: Do you have Python 3 installed locally?
   ```bash
   python3 --version
   ```

3. **Check the launcher**: Did you edit all 3 values in the file?

4. **Check Claude config**: Is the path to the launcher correct?

## Security Note

⚠️ **Never commit the edited launcher file to Git** - it contains your API key!

Instead, keep it in a safe location on your local computer.