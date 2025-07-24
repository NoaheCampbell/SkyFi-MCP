#!/usr/bin/env python3
"""WebSocket bridge for remote MCP server."""
import asyncio
import json
import sys
import os

import websockets
from mcp.server.stdio import stdio_server


class WebSocketBridge:
    """Bridge STDIO to WebSocket for remote MCP."""
    
    def __init__(self, ws_url: str, api_key: str):
        self.ws_url = ws_url
        self.api_key = api_key
        self.ws = None
    
    async def connect(self):
        """Connect to remote WebSocket server."""
        headers = {"X-Skyfi-Api-Key": self.api_key}
        self.ws = await websockets.connect(self.ws_url, extra_headers=headers)
    
    async def run(self):
        """Run the bridge."""
        await self.connect()
        
        async with stdio_server() as (read_stream, write_stream):
            # Forward STDIO to WebSocket
            async def stdio_to_ws():
                while True:
                    line = await read_stream.readline()
                    if not line:
                        break
                    await self.ws.send(line.decode())
            
            # Forward WebSocket to STDIO
            async def ws_to_stdio():
                async for message in self.ws:
                    await write_stream.write(message.encode() + b'\n')
                    await write_stream.drain()
            
            # Run both directions concurrently
            await asyncio.gather(
                stdio_to_ws(),
                ws_to_stdio()
            )


async def main():
    """Run the WebSocket bridge."""
    ws_url = os.getenv("MCP_WS_URL", "wss://skyfi-mcp.yourdomain.com/ws")
    api_key = os.getenv("SKYFI_API_KEY", "")
    
    bridge = WebSocketBridge(ws_url, api_key)
    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())