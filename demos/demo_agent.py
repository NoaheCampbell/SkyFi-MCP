#!/usr/bin/env python3
"""
Demo MCP Agent for SkyFi

This demonstrates how to properly connect to an MCP server over HTTP/SSE
with dynamic API key authentication via headers.
"""
import asyncio
import json
import os
import sys
from typing import Optional, Dict, Any
import httpx
import click
from datetime import datetime


class MCPDemoAgent:
    """Demo agent that connects to MCP server via HTTP/SSE."""
    
    def __init__(self, server_url: str, api_key: Optional[str] = None):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.session_id = None
        self.tools = {}
        
    async def connect(self):
        """Establish SSE connection to MCP server."""
        headers = {"Accept": "text/event-stream"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        print(f"🔌 Connecting to {self.server_url}/sse...")
        
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', f"{self.server_url}/sse", headers=headers) as response:
                if response.status_code != 200:
                    print(f"❌ Failed to connect: {response.status_code}")
                    return
                    
                print("✅ Connected to MCP server")
                
                # Send initialization
                await self._send_message({
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "0.1.0",
                        "capabilities": {}
                    },
                    "id": 1
                })
                
                # Process events
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            await self._handle_message(data)
                        except json.JSONDecodeError:
                            pass
                            
    async def _send_message(self, message: Dict[str, Any]):
        """Send a message to the server (would need WebSocket for bidirectional)."""
        # Note: SSE is unidirectional. In a real implementation,
        # you'd use WebSocket or a separate POST endpoint
        print(f"📤 Would send: {json.dumps(message, indent=2)}")
        
    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming messages from server."""
        if "result" in message:
            # Handle responses
            if message.get("id") == 1:
                # Initialization response
                print("✅ Initialized successfully")
                # Now list tools
                await self._send_message({
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 2
                })
            elif message.get("id") == 2:
                # Tool list response
                self.tools = {tool["name"]: tool for tool in message["result"]["tools"]}
                print(f"\n📦 Available tools ({len(self.tools)}):")
                for name, tool in self.tools.items():
                    print(f"  - {name}: {tool['description']}")
                    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Call a specific tool."""
        if tool_name not in self.tools:
            print(f"❌ Unknown tool: {tool_name}")
            return
            
        print(f"\n🔧 Calling tool: {tool_name}")
        print(f"   Arguments: {json.dumps(arguments, indent=2)}")
        
        await self._send_message({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 3
        })


class InteractiveMCPClient:
    """Interactive client for testing MCP servers."""
    
    def __init__(self, server_url: str, api_key: Optional[str] = None):
        self.server_url = server_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    async def test_connection(self):
        """Test basic connectivity."""
        print(f"\n🧪 Testing connection to {self.server_url}")
        
        # Test root endpoint
        try:
            response = await self.client.get(self.server_url)
            data = response.json()
            print(f"✅ Server info: {data['name']} v{data['version']}")
            print(f"   Transport: {data['transport']}")
            print(f"   Endpoints: {', '.join(data['endpoints'].keys())}")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
            
        # Test health endpoint
        try:
            response = await self.client.get(f"{self.server_url}/health")
            data = response.json()
            print(f"✅ Health check: {data['status']}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            
        return True
        
    async def list_tools(self):
        """List available tools via HTTP (simplified demo)."""
        # Note: This is a simplified version. Real MCP requires proper SSE/WebSocket
        print("\n📋 Listing available tools...")
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            print("🔑 Using API key authentication")
        else:
            print("⚠️  No API key provided - only public tools available")
            
        # This would normally be done via SSE/WebSocket MCP protocol
        print("\nTo see tools, the agent would:")
        print("1. Connect via SSE to /sse endpoint")
        print("2. Send 'initialize' message")
        print("3. Send 'tools/list' message")
        print("4. Receive tool list in response")
        
    async def demo_skyfi_search(self, location: str):
        """Demo searching for satellite imagery."""
        print(f"\n🛰️  Demo: Searching satellite imagery for '{location}'")
        
        if not self.api_key:
            print("❌ SkyFi tools require API key")
            return
            
        print("\nThe agent would:")
        print("1. Call 'skyfi_search_imagery' tool")
        print(f"2. With location: '{location}'")
        print("3. Receive available satellite passes")
        print("4. Display results to user")
        
    async def demo_weather_search(self, location: str):
        """Demo weather search (no API key needed)."""
        print(f"\n🌤️  Demo: Getting weather for '{location}'")
        print("\nThe agent would:")
        print("1. Call 'weather_get_current' tool")
        print(f"2. With location: '{location}'")
        print("3. Receive weather data")
        print("4. Display formatted weather to user")


@click.command()
@click.option(
    "--server-url",
    default="http://localhost:8000",
    help="MCP server URL"
)
@click.option(
    "--api-key",
    envvar="SKYFI_API_KEY",
    help="SkyFi API key (or set SKYFI_API_KEY env var)"
)
@click.option(
    "--demo",
    is_flag=True,
    help="Run interactive demo"
)
async def main(server_url: str, api_key: Optional[str], demo: bool):
    """Demo MCP Agent - Shows how to connect to MCP servers with proper authentication."""
    
    print("🤖 MCP Demo Agent")
    print("=" * 50)
    
    if demo:
        # Run interactive demo
        async with InteractiveMCPClient(server_url, api_key) as client:
            # Test connection
            if not await client.test_connection():
                return
                
            # List tools
            await client.list_tools()
            
            # Demo searches
            await client.demo_weather_search("Tokyo, Japan")
            await client.demo_skyfi_search("Mount Fuji, Japan")
            
            print("\n✨ Demo complete!")
            print("\nTo use this in production:")
            print("1. Implement proper SSE/WebSocket client")
            print("2. Handle MCP protocol messages")
            print("3. Parse tool responses")
            print("4. Build your agent logic on top")
            
    else:
        # Run SSE connection demo
        agent = MCPDemoAgent(server_url, api_key)
        try:
            await agent.connect()
        except KeyboardInterrupt:
            print("\n👋 Disconnected")


if __name__ == "__main__":
    asyncio.run(main())