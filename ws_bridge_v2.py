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
    """Bridge WebSocket to MCP stdio with proper initialization handling."""
    logger.info(f"New connection from {websocket.remote_address}")
    
    # Extract API key from headers if provided
    api_key = None
    try:
        if hasattr(websocket, 'request_headers') and 'Authorization' in websocket.request_headers:
            auth_header = websocket.request_headers['Authorization']
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:]
    except:
        pass
    
    # Start MCP server process
    env = os.environ.copy()
    if 'NGROK_DOMAIN' in os.environ:
        env['NGROK_DOMAIN'] = os.environ['NGROK_DOMAIN']
    if api_key:
        env['SKYFI_API_KEY'] = api_key
    # Pass through other important environment variables
    for key in ['WEATHER_API_KEY', 'SKYFI_API_KEY', 'DEBUG', 'MCP_LOG_LEVEL']:
        if key in os.environ:
            env[key] = os.environ[key]
    
    proc = await asyncio.create_subprocess_exec(
        'python', '-m', 'mcp_skyfi',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    
    # Track initialization state
    initialized = False
    pending_messages = []
    
    async def ws_to_stdin():
        nonlocal initialized, pending_messages
        try:
            async for message in websocket:
                logger.debug(f"WS -> MCP: {message}")
                
                # Parse the message to check if it's an initialize request
                try:
                    msg_data = json.loads(message)
                    if msg_data.get('method') == 'initialize':
                        # Send initialize immediately
                        proc.stdin.write(message.encode() + b'\n')
                        await proc.stdin.drain()
                        # Don't mark as initialized yet - wait for response
                    elif not initialized:
                        # Queue non-initialize messages until initialized
                        logger.info(f"Queueing message until initialization complete: {msg_data.get('method')}")
                        pending_messages.append(message)
                    else:
                        # Normal message flow after initialization
                        proc.stdin.write(message.encode() + b'\n')
                        await proc.stdin.drain()
                except json.JSONDecodeError:
                    # If not JSON, just pass through
                    if initialized:
                        proc.stdin.write(message.encode() + b'\n')
                        await proc.stdin.drain()
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error in ws_to_stdin: {e}")
        finally:
            proc.stdin.close()
    
    async def stdout_to_ws():
        nonlocal initialized, pending_messages
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode().strip()
                if decoded:
                    logger.debug(f"MCP -> WS: {decoded}")
                    await websocket.send(decoded)
                    
                    # Check if this is an initialize response
                    try:
                        msg_data = json.loads(decoded)
                        if (msg_data.get('id') == 1 and 
                            'result' in msg_data and 
                            'serverInfo' in msg_data['result']):
                            logger.info("Initialization complete, processing pending messages")
                            initialized = True
                            
                            # Send any pending messages
                            for pending in pending_messages:
                                logger.info(f"Sending pending message: {json.loads(pending).get('method')}")
                                proc.stdin.write(pending.encode() + b'\n')
                                await proc.stdin.drain()
                            pending_messages.clear()
                    except json.JSONDecodeError:
                        pass
                        
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
    port = int(os.environ.get('PORT', 8765))
    logger.info(f"Starting WebSocket server on port {port}")
    
    async with websockets.serve(
        lambda ws: handle_websocket(ws, "/"), 
        '0.0.0.0', 
        port,
        ping_interval=20,
        ping_timeout=10
    ):
        logger.info("WebSocket server started successfully")
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())