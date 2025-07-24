#!/usr/bin/env python3
"""Run the public MCP server that accepts API keys through tool calls."""
import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_skyfi.servers.public_server import main

if __name__ == "__main__":
    asyncio.run(main())