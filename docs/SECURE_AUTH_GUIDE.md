# Secure Authentication Guide for SkyFi MCP

## Overview

This guide explains the secure authentication system that prevents users from typing API keys into chat.

## How It Works

1. **User requests authentication** via the `skyfi_authenticate` tool
2. **Server generates a unique link** with a one-time nonce
3. **User visits the link** in their browser (HTTPS secured)
4. **User enters API key** on the secure web page
5. **Server validates and stores** the key for their session
6. **User returns to Claude** and can use all features

## User Flow

### Step 1: Connect to Server

Add to Claude Desktop config:
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

### Step 2: Request Authentication

In Claude:
```
User: "Set up my SkyFi authentication"

Claude: I'll generate a secure authentication link for you.

🔐 Secure Authentication Setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please visit this secure link to enter your SkyFi API key:

🔗 https://skyfi-mcp-auth.ngrok.io/auth/abc123xyz...

This link will:
✅ Use HTTPS encryption
✅ Expire in 5 minutes
✅ Only work once
✅ Never expose your key in chat

After authenticating, close the browser and return here.
```

### Step 3: Visit Secure Link

User clicks the link and sees:

![Auth Page](auth-page-mockup.png)

- Clean, professional interface
- HTTPS secured connection
- Password field hides the API key
- Real-time validation
- Clear success/error messages

### Step 4: Enter API Key

User enters their SkyFi API key:
- Key is validated with SkyFi API
- If valid, shows success message
- Browser can be closed

### Step 5: Return to Claude

```
User: "Check my authentication status"

Claude: Let me check your authentication status.

🔐 Authentication Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ API key is configured
Source: Web authentication

You're all set to use SkyFi features!
```

## Security Features

### For Users
- ✅ **Never type API key in chat** - No exposure to LLM
- ✅ **HTTPS encryption** - Secure transmission
- ✅ **One-time links** - Can't be reused
- ✅ **Time-limited** - Links expire in 5 minutes
- ✅ **Session-based** - Key only valid for current session

### For Server
- ✅ **No persistent storage** - Keys only in memory
- ✅ **Nonce validation** - Prevents replay attacks
- ✅ **API key validation** - Checks with SkyFi before accepting
- ✅ **Session isolation** - Each user's key is separate
- ✅ **Automatic cleanup** - Expired sessions are removed

## Technical Implementation

### Nonce Generation
```python
# Cryptographically secure random token
nonce = secrets.token_urlsafe(32)
```

### Session Management
```python
sessions[nonce] = {
    'session_id': mcp_session_id,
    'created_at': datetime.utcnow(),
    'expires_at': datetime.utcnow() + timedelta(minutes=5),
    'status': 'pending',
    'api_key': None
}
```

### Authentication Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Claude    │────►│ MCP Server  │────►│ Auth Server │
│  Desktop    │     │   (8080)    │     │   (8081)    │
└─────────────┘     └─────────────┘     └─────────────┘
      │                     │                    │
      │ 1. authenticate     │                    │
      │────────────────────►│                    │
      │                     │ 2. generate nonce  │
      │◄────────────────────│                    │
      │ 3. show link        │                    │
      │                     │                    │
      │                     │                    │
┌─────────────┐            │                    │
│   Browser   │            │                    │
│             │────────────┼────────────────────►
│             │ 4. visit link                   │
│             │◄────────────────────────────────┤
│             │ 5. show form                    │
│             │─────────────────────────────────►
│             │ 6. submit key                   │
│             │◄────────────────────────────────┤
│             │ 7. validate & store             │
└─────────────┘                                 │
      │                                         │
      │ 8. return to Claude                     │
      │                                         │
      ▼                                         ▼
```

## Deployment

### Basic Setup
```bash
./scripts/run_public_server_with_auth.sh
```

### Production Setup
```bash
# Use systemd service
sudo cp skyfi-mcp.service /etc/systemd/system/
sudo systemctl enable skyfi-mcp
sudo systemctl start skyfi-mcp

# Use reverse proxy (nginx)
server {
    listen 443 ssl;
    server_name skyfi-mcp.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8080;
    }
    
    location /auth {
        proxy_pass http://localhost:8081;
    }
}
```

## Troubleshooting

### "Invalid authentication link"
- Link was already used
- Link expired (>5 minutes)
- Request a new link

### "API key validation failed"
- Check API key is correct
- Verify SkyFi account is active
- Ensure Pro subscription

### "No API key configured"
- Complete authentication first
- Check if session expired
- Request new auth link

## Benefits Over Other Methods

| Method | Security | User Experience | Implementation |
|--------|----------|----------------|----------------|
| Type in chat | ❌ Poor | ❌ Poor | ✅ Simple |
| Environment vars | ✅ Good | ❌ Complex | ❌ Complex |
| Config files | ✅ Good | ❌ Complex | ❌ Complex |
| **Web auth** | ✅ Excellent | ✅ Simple | ✅ Moderate |

## Future Enhancements

1. **OAuth Integration** - Direct SkyFi login
2. **Remember Device** - Optional persistent auth
3. **2FA Support** - Additional security layer
4. **Team Management** - Admin-controlled access