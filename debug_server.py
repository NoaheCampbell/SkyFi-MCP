#!/usr/bin/env python3
"""Debug script to test server initialization."""
import os
import sys
import asyncio

# Set test environment
os.environ["SKYFI_API_KEY"] = "test-key"

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_skyfi.servers.main import SkyFiMCPServer

async def test_server():
    """Test server initialization."""
    print("Creating server...")
    server = SkyFiMCPServer()
    print("Server created successfully!")
    
    print("\nRegistering tools...")
    tools = await server.server.list_tools()
    print(f"Found {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}")
    
    print("\nServer is ready!")

if __name__ == "__main__":
    asyncio.run(test_server())