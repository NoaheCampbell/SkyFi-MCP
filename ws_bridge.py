#!/usr/bin/env python3
import asyncio
import websockets
import subprocess
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_websocket(websocket, path):
    """Bridge WebSocket to MCP stdio."""
    logger.info(f"New connection from {websocket.remote_address}")
    
    # Extract API key from headers if provided
    api_key = None
    if 'Authorization' in websocket.request_headers:
        auth_header = websocket.request_headers['Authorization']
        if auth_header.startswith('Bearer '):
            api_key = auth_header[7:]
    
    # Start MCP server process
    env = os.environ.copy()
    env['NGROK_DOMAIN'] = 'skyfi-mcp.ngrok.dev'
    if api_key:
        env['SKYFI_API_KEY'] = api_key
    
    proc = await asyncio.create_subprocess_exec(
        'python', '-m', 'mcp_skyfi',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    
    async def ws_to_stdin():
        try:
            async for message in websocket:
                logger.debug(f"WS -> MCP: {message}")
                proc.stdin.write(message.encode() + b'\n')
                await proc.stdin.drain()
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error in ws_to_stdin: {e}")
        finally:
            proc.stdin.close()
    
    async def stdout_to_ws():
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode().strip()
                if decoded:
                    logger.debug(f"MCP -> WS: {decoded}")
                    await websocket.send(decoded)
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed during send")
        except Exception as e:
            logger.error(f"Error in stdout_to_ws: {e}")
    
    async def stderr_logger():
        while True:
            line = await proc.stderr.readline()
            if not line:
                break
            logger.error(f"MCP stderr: {line.decode().strip()}")
    
    # Run all tasks
    await asyncio.gather(
        ws_to_stdin(), 
        stdout_to_ws(),
        stderr_logger(),
        return_exceptions=True
    )
    
    # Clean up
    logger.info("Cleaning up MCP process")
    proc.terminate()
    await proc.wait()

async def main():
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting WebSocket server on port {port}")
    
    async with websockets.serve(
        handle_websocket, 
        '0.0.0.0', 
        port,
        ping_interval=20,
        ping_timeout=10
    ):
        logger.info("WebSocket server started successfully")
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())