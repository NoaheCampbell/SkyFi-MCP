#!/usr/bin/env python3
"""Minimal MCP server for testing."""
import asyncio
import os
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.server import Server
from mcp.types import Tool

# Create server
server = Server("skyfi-test")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="test_tool",
            description="A test tool",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list:
    """Handle tool calls."""
    return [{"type": "text", "text": f"Called {name}"}]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="skyfi-test",
                server_version="0.1.0",
                capabilities={}
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())