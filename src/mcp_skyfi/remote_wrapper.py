#!/usr/bin/env python3
"""Remote wrapper that accepts environment variables from first message."""
import os
import sys
import json
import asyncio
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Read environment from first line, then run MCP server."""
    import asyncio
    
    # Create async reader for stdin
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_running_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    
    # Read first line
    first_line_bytes = await reader.readline()
    first_line = first_line_bytes.decode('utf-8').strip()
    
    logger.info(f"Received first line: {first_line[:50]}...")
    
    if first_line.startswith("ENV:"):
        # Parse and set environment variables
        try:
            env_json = first_line[4:]
            env_data = json.loads(env_json)
            for key, value in env_data.items():
                if value is not None and value != "":
                    os.environ[key] = str(value)
                    logger.info(f"Set {key}={value[:20]}...")
        except Exception as e:
            logger.error(f"Failed to parse environment: {e}")
    else:
        # Not an ENV line, we need to handle this properly
        # Put the line back by creating a new stdin that includes it
        remaining_data = first_line_bytes + await reader.read()
        
        # Create a pipe to feed data back
        read_fd, write_fd = os.pipe()
        os.write(write_fd, remaining_data)
        os.close(write_fd)
        
        # Replace stdin with our pipe
        os.dup2(read_fd, 0)
        os.close(read_fd)
    
    # Now import and run the actual MCP server
    logger.info("Starting MCP server...")
    from mcp_skyfi.servers.main import SkyFiMCPServer
    server = SkyFiMCPServer()
    await server.run_stdio()

if __name__ == "__main__":
    asyncio.run(main())