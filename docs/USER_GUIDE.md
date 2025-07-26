# SkyFi MCP User Guide

## Quick Start (2 minutes)

### 1. Get the Server URL

Your administrator will provide you with a URL like:
- `https://skyfi-mcp.ngrok.io` or
- `https://abc123.ngrok.io`

### 2. Add to Claude Desktop

Open your Claude Desktop configuration file:

**Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration (replace the URL with your actual server URL):

```json
{
  "mcpServers": {
    "skyfi": {
      "transport": "http",
      "url": "https://skyfi-mcp.ngrok.io"
    }
  }
}
```

### 3. Restart Claude Desktop

Quit and reopen Claude Desktop to load the new configuration.

### 4. Set Your API Key

In Claude, type:

```
Set my SkyFi API key to sk-your-actual-api-key-here
```

You'll see:
```
✅ API key set and verified successfully!
Authenticated as: your@email.com
Account type: Pro
```

## That's it! You're ready to use SkyFi 🛰️

## Example Commands

### Search for Images
```
Search for satellite images of Central Park from last week
```

### Check Your Budget
```
Show my SkyFi spending report
```

### Save a Search
```
Save this search as "Daily Manhattan Check" 
```

### Download an Order
```
Show my recent orders and download the completed ones
```

### Multi-Location Search
```
Search for images of Times Square, Central Park, and Brooklyn Bridge from yesterday
```

### Export Order History
```
Export my order history as a CSV file
```

## Important Notes

### 🔐 Security
- Your API key is only stored in memory during your session
- You'll need to set it again if you restart Claude Desktop
- Never share your API key with others

### 💰 Costs
- You're using your own SkyFi account
- All orders are billed to your account
- Check prices before ordering: `Show pricing for this area`

### 🚫 Safety Features
- Orders require confirmation before purchase
- Budget limits prevent overspending
- Low resolution is used by default to save money

## Troubleshooting

### "No API key configured"
You need to set your API key first. See step 4 above.

### "Authentication failed"
Your API key might be invalid. Check it at https://app.skyfi.com

### Connection errors
The server might be down. Contact your administrator.

### Can't see SkyFi tools
Make sure you:
1. Added the configuration correctly
2. Restarted Claude Desktop
3. Saved the config file as plain text (not .rtf or .doc)

## Getting Your API Key

1. Go to https://app.skyfi.com
2. Sign up or log in
3. Go to Settings → API Keys
4. Create a new API key
5. Copy the key (starts with `sk-`)

**Note**: You need a Pro account for API access.

## Privacy & Security

- ✅ Your API key is never stored on the server
- ✅ Each user's requests are isolated
- ✅ All connections are encrypted with HTTPS
- ✅ The server cannot see your search history

## Need Help?

- SkyFi Support: support@skyfi.com
- API Documentation: https://docs.skyfi.com
- Server Issues: Contact your administrator