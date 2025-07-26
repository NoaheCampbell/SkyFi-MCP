#!/usr/bin/env python3
"""
WebSocket client for SkyFi MCP server.
This bridges local stdio to the remote WebSocket MCP server.
"""
import asyncio
import websockets
import sys
import json
import os

# Get the WebSocket URL from environment or use default
WS_URL = os.environ.get('SKYFI_WS_URL', 'wss://attempt1-copy.fly.dev')

async def bridge_stdio_to_websocket():
    """Bridge stdio to WebSocket connection."""
    print(f"Connecting to {WS_URL}...", file=sys.stderr)
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print(f"Connected to MCP server", file=sys.stderr)
            
            # Create tasks for bidirectional communication
            async def stdin_to_ws():
                """Forward stdin to WebSocket."""
                loop = asyncio.get_event_loop()
                reader = asyncio.StreamReader()
                protocol = asyncio.StreamReaderProtocol(reader)
                await loop.connect_read_pipe(lambda: protocol, sys.stdin)
                
                while True:
                    line = await reader.readline()
                    if not line:
                        break
                    
                    # Send the line without extra newline
                    data = line.decode().rstrip('\n')
                    if data:
                        await websocket.send(data)
            
            async def ws_to_stdout():
                """Forward WebSocket messages to stdout."""
                async for message in websocket:
                    # Write message with newline for MCP protocol
                    sys.stdout.write(message + '\n')
                    sys.stdout.flush()
            
            # Run both directions concurrently
            await asyncio.gather(stdin_to_ws(), ws_to_stdout())
            
    except websockets.exceptions.WebSocketException as e:
        print(f"WebSocket error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    try:
        asyncio.run(bridge_stdio_to_websocket())
    except KeyboardInterrupt:
        sys.exit(0)