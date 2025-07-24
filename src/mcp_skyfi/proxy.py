#!/usr/bin/env python3
"""MCP STDIO to HTTP proxy for remote servers."""
import asyncio
import json
import sys
import os
from typing import Optional

import httpx
from mcp.server.stdio import stdio_server


class MCPProxy:
    """Proxy STDIO MCP calls to remote HTTP server."""
    
    def __init__(self, remote_url: str, api_key: str):
        self.remote_url = remote_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            headers={"X-Skyfi-Api-Key": api_key},
            timeout=30.0
        )
    
    async def handle_message(self, message: dict) -> dict:
        """Forward MCP message to HTTP server."""
        method = message.get("method", "")
        
        if method == "initialize":
            # Get manifest from remote
            response = await self.client.get(f"{self.remote_url}/mcp/manifest")
            manifest = response.json()
            
            return {
                "capabilities": {
                    "tools": manifest.get("tools", [])
                }
            }
        
        elif method == "tools/list":
            # Get tools from remote
            response = await self.client.get(f"{self.remote_url}/mcp/manifest")
            manifest = response.json()
            return {"tools": manifest.get("tools", [])}
        
        elif method == "tools/call":
            # Forward tool call to remote
            params = message.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            response = await self.client.post(
                f"{self.remote_url}/tools/{tool_name}",
                json={"tool": tool_name, "arguments": arguments}
            )
            
            result = response.json()
            return {
                "content": [{
                    "type": "text",
                    "text": result.get("result", "")
                }]
            }
        
        return {"error": f"Unknown method: {method}"}
    
    async def run(self):
        """Run the STDIO proxy."""
        async with stdio_server() as (read_stream, write_stream):
            while True:
                try:
                    # Read from STDIO
                    line = await read_stream.readline()
                    if not line:
                        break
                    
                    message = json.loads(line)
                    
                    # Forward to HTTP server
                    response = await self.handle_message(message)
                    
                    # Write response back
                    await write_stream.write(json.dumps(response).encode() + b'\n')
                    await write_stream.drain()
                    
                except Exception as e:
                    error_response = {
                        "error": {
                            "code": -32603,
                            "message": str(e)
                        }
                    }
                    await write_stream.write(json.dumps(error_response).encode() + b'\n')
                    await write_stream.drain()


async def main():
    """Run the proxy."""
    remote_url = os.getenv("MCP_REMOTE_URL", "https://skyfi-mcp.yourdomain.com")
    api_key = os.getenv("SKYFI_API_KEY", "")
    
    if not api_key:
        print("Error: SKYFI_API_KEY required", file=sys.stderr)
        sys.exit(1)
    
    proxy = MCPProxy(remote_url, api_key)
    await proxy.run()


if __name__ == "__main__":
    asyncio.run(main())