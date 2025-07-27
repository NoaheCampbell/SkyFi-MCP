# Authentication Guide

## Overview

The SkyFi MCP server supports multiple authentication methods depending on your deployment:

1. **Local/Development**: Environment variables
2. **Production/Multi-user**: Header-based authentication
3. **Cloud**: AWS Secrets Manager

## Authentication Methods

### 1. Environment Variables (Simplest)

For local development or single-user deployments:

```bash
# .env file or shell
export SKYFI_API_KEY="your-skyfi-api-key"
export WEATHER_API_KEY="your-openweathermap-key"  # Optional
```

### 2. Header Authentication (Multi-user)

For production deployments with multiple users:

```python
# Server expects headers:
headers = {
    "X-API-Key": "user-skyfi-api-key",
    "X-Weather-API-Key": "user-weather-key"  # Optional
}
```

Claude Desktop config:
```json
{
  "mcpServers": {
    "skyfi": {
      "transport": "http",
      "url": "https://your-server.com",
      "headers": {
        "X-API-Key": "your-skyfi-api-key"
      }
    }
  }
}
```

### 3. AWS Secrets Manager

For cloud deployments:

```bash
# Store secrets in AWS
aws secretsmanager create-secret \
  --name skyfi-mcp-keys \
  --secret-string '{"SKYFI_API_KEY":"your-key","WEATHER_API_KEY":"weather-key"}'

# Server automatically loads from AWS
export SKYFI_SECRET_NAME="skyfi-mcp-keys"
```

## Getting Your API Keys

### SkyFi API Key (Required)
1. Sign up at https://app.skyfi.com
2. Navigate to Settings → API Keys
3. Create a new API key (starts with `sk-`)
4. Requires a Pro account for API access

### Weather API Key (Optional)
1. Sign up at https://openweathermap.org/api
2. Free tier available
3. Enables weather tools for capture planning

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for local development
3. **Use header authentication** for production
4. **Rotate keys regularly**
5. **Set spending limits** with `SKYFI_COST_LIMIT`

## Troubleshooting

### 401 Unauthorized
- Verify your API key is correct
- Ensure you have a SkyFi Pro account
- Check key hasn't expired

### Missing API Key
- For local: Check environment variables are set
- For production: Verify headers are being sent
- For AWS: Check secret name and permissions

### Authentication Still Failing
1. Test API key directly: `curl -H "Authorization: Bearer YOUR_KEY" https://app.skyfi.com/platform-api/auth/whoami`
2. Check server logs for specific error messages
3. Verify no extra spaces in API key