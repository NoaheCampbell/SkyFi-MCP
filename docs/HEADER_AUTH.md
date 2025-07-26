# Header-Based Authentication for SkyFi MCP

This document explains how to pass API keys as HTTPS headers when using the SkyFi MCP server.

## The Challenge

When running MCP servers on remote instances (like AWS), we need a secure way to pass API keys without:
- Storing them in environment variables on the server
- Typing them into chat interfaces
- Saving them in files

## Solutions

### Option 1: Custom MCP Transport (Recommended)

Create a custom transport wrapper that adds headers to all requests:

```javascript
// mcp-skyfi-transport.js
const { spawn } = require('child_process');
const { Transform } = require('stream');

class HeaderInjector extends Transform {
  constructor(apiKey) {
    super();
    this.apiKey = apiKey;
  }
  
  _transform(chunk, encoding, callback) {
    try {
      const data = JSON.parse(chunk);
      
      // Inject API key into request metadata
      if (data.method) {
        data.metadata = data.metadata || {};
        data.metadata.headers = {
          'X-Skyfi-Api-Key': this.apiKey
        };
      }
      
      this.push(JSON.stringify(data) + '\n');
    } catch (e) {
      this.push(chunk);
    }
    callback();
  }
}

// Launch MCP server with header injection
const apiKey = process.env.SKYFI_API_KEY_LOCAL; // Read from LOCAL env
const server = spawn('ssh', [
  'user@aws-instance',
  'python', '-m', 'mcp_skyfi'
]);

const injector = new HeaderInjector(apiKey);
process.stdin.pipe(injector).pipe(server.stdin);
server.stdout.pipe(process.stdout);
```

Then in Claude Desktop config:
```json
{
  "mcpServers": {
    "skyfi": {
      "command": "node",
      "args": ["/path/to/mcp-skyfi-transport.js"]
    }
  }
}
```

### Option 2: Proxy Server

Run a local proxy that adds headers:

```python
# local-proxy.py
import asyncio
import json
import os
from subprocess import Popen, PIPE

async def proxy_with_headers():
    # Get API key from local environment
    api_key = os.environ.get('SKYFI_API_KEY')
    
    # Connect to remote MCP server
    process = Popen(
        ['ssh', 'user@aws-instance', 'python', '-m', 'mcp_skyfi'],
        stdin=PIPE, stdout=PIPE, text=True
    )
    
    while True:
        # Read from stdin
        line = await asyncio.get_event_loop().run_in_executor(None, input)
        data = json.loads(line)
        
        # Add API key to metadata
        if 'method' in data:
            data.setdefault('metadata', {})
            data['metadata']['skyfi_api_key'] = api_key
        
        # Send to remote server
        process.stdin.write(json.dumps(data) + '\n')
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        print(response, end='')

if __name__ == '__main__':
    asyncio.run(proxy_with_headers())
```

### Option 3: Environment Variable Forwarding

Use SSH's SendEnv to forward specific environment variables:

```bash
# ~/.ssh/config
Host skyfi-mcp
  HostName your-aws-instance.com
  User ec2-user
  SendEnv SKYFI_API_KEY
  SetEnv MCP_MODE=header_auth
```

Then the server reads from the forwarded environment.

### Option 4: Secure WebSocket Bridge

For production use, implement a WebSocket bridge with proper authentication:

```python
# ws-bridge-server.py (runs on AWS)
from fastapi import FastAPI, WebSocket, Header, HTTPException
import asyncio

app = FastAPI()

@app.websocket("/mcp")
async def mcp_bridge(
    websocket: WebSocket,
    x_skyfi_api_key: str = Header(None)
):
    if not x_skyfi_api_key:
        await websocket.close(code=1008, reason="Missing API Key")
        return
    
    await websocket.accept()
    
    # Launch MCP server with API key
    process = await asyncio.create_subprocess_exec(
        'python', '-m', 'mcp_skyfi',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        env={**os.environ, 'SKYFI_API_KEY': x_skyfi_api_key}
    )
    
    # Bridge WebSocket to process
    async def forward_to_process():
        async for message in websocket.iter_text():
            process.stdin.write(message.encode() + b'\n')
            await process.stdin.drain()
    
    async def forward_from_process():
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            await websocket.send_text(line.decode())
    
    await asyncio.gather(
        forward_to_process(),
        forward_from_process()
    )
```

Then connect from Claude Desktop using a WebSocket client.

## Recommended Approach

For maximum security and ease of use:

1. **Development**: Use local MCP server with environment variables
2. **Production**: Use the WebSocket bridge with HTTPS/WSS
3. **Quick Setup**: Use SSH environment forwarding

The key principle is: **API keys should only exist on the client side**, never stored on the server.

## Implementation in Auth Manager

The auth manager already supports reading from request context:

```python
# In header_auth.py
api_key = header_auth.extract_api_key_from_context(context)
```

This looks for keys in:
- `context['headers']['X-Skyfi-Api-Key']`
- `context['headers']['Authorization']` (Bearer token)
- `context['metadata']['skyfi_api_key']`

The MCP server just needs to receive the context with these headers, which the transport layer provides.