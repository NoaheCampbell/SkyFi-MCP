#!/usr/bin/env python3
"""
MCP SDK Demo - Production-ready example of connecting to MCP servers

This shows how a real agent/application would connect to the MCP server
with proper authentication and protocol handling.
"""
import asyncio
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import httpx
from datetime import datetime


@dataclass
class MCPTool:
    """Represents an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPClient:
    """
    Production-ready MCP client with proper authentication.
    
    This demonstrates the correct way to connect to an MCP server
    where API keys are passed via headers, not in configuration.
    """
    
    def __init__(self, server_url: str, api_key: Optional[str] = None):
        """
        Initialize MCP client.
        
        Args:
            server_url: Base URL of the MCP server (e.g., https://your-server.ngrok.io)
            api_key: Optional API key for authenticated tools
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        self.tools: Dict[str, MCPTool] = {}
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def connect(self):
        """Test connection and discover tools."""
        # Test connection
        response = await self.client.get(self.server_url)
        info = response.json()
        print(f"Connected to: {info['name']} v{info['version']}")
        
        # In a real implementation, you would:
        # 1. Establish SSE/WebSocket connection
        # 2. Send initialize message
        # 3. Receive and store session info
        # 4. Call tools/list to discover available tools
        
    async def close(self):
        """Close the client connection."""
        await self.client.aclose()
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            # This is the key part - API key goes in headers!
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers
        
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool.
        
        In a real implementation, this would:
        1. Send tool call request via SSE/WebSocket
        2. Wait for response
        3. Parse and return result
        """
        print(f"\nCalling tool: {tool_name}")
        print(f"Arguments: {json.dumps(arguments, indent=2)}")
        
        # Simulate API call with proper headers
        headers = self._get_headers()
        
        # This would be the actual protocol message
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }
        
        print(f"\nRequest headers: {json.dumps({k: v if k != 'Authorization' else 'Bearer ***' for k, v in headers.items()}, indent=2)}")
        print(f"Request body: {json.dumps(request_data, indent=2)}")
        
        # In real implementation, send via SSE/WebSocket
        # For demo, just show what would happen
        return {"demo": "This would return actual tool results"}


class SkyFiMCPAgent:
    """
    Example agent that uses the MCP client to interact with SkyFi.
    
    This shows how an application would use the MCP SDK.
    """
    
    def __init__(self, mcp_client: MCPClient):
        self.client = mcp_client
        
    async def search_satellite_imagery(self, location: str, date_range: Optional[tuple] = None):
        """Search for satellite imagery of a location."""
        args = {"location": location}
        
        if date_range:
            args["start_date"] = date_range[0]
            args["end_date"] = date_range[1]
        else:
            # Default to last 30 days
            args["start_date"] = "2024-01-01"
            args["end_date"] = "2024-12-31"
            
        result = await self.client.call_tool("skyfi_search_imagery", args)
        return result
        
    async def get_weather(self, location: str):
        """Get current weather for a location."""
        result = await self.client.call_tool("weather_get_current", {"location": location})
        return result
        
    async def find_nearby_places(self, lat: float, lon: float, category: str = "restaurant"):
        """Find nearby places using OSM."""
        result = await self.client.call_tool("osm_search_nearby", {
            "lat": lat,
            "lon": lon,
            "radius": 1000,
            "tags": [category]
        })
        return result


async def demo_enterprise_usage():
    """
    Demonstrate enterprise usage pattern where each user has their own API key.
    """
    print("=" * 60)
    print("ENTERPRISE USAGE DEMO")
    print("=" * 60)
    
    # In a real application, these would come from:
    # - User authentication system
    # - Environment variables
    # - Secure key management service
    users = [
        {"name": "Alice", "api_key": "alice-api-key-123"},
        {"name": "Bob", "api_key": "bob-api-key-456"},
        {"name": "Charlie", "api_key": None},  # No API key - limited access
    ]
    
    server_url = "https://skyfi-mcp.ngrok.io"  # Your production server
    
    for user in users:
        print(f"\n{'='*40}")
        print(f"User: {user['name']}")
        print(f"Has API Key: {'Yes' if user['api_key'] else 'No'}")
        print(f"{'='*40}")
        
        # Each user gets their own client instance with their API key
        async with MCPClient(server_url, api_key=user['api_key']) as client:
            agent = SkyFiMCPAgent(client)
            
            # Everyone can use weather (no API key required)
            print("\n📍 Checking weather in Tokyo...")
            await agent.get_weather("Tokyo, Japan")
            
            # Only users with API keys can use SkyFi
            if user['api_key']:
                print("\n🛰️ Searching satellite imagery...")
                await agent.search_satellite_imagery("Mount Fuji, Japan")
            else:
                print("\n❌ Cannot search satellite imagery (no API key)")


async def demo_web_app_usage():
    """
    Demonstrate web application usage pattern.
    """
    print("\n" + "=" * 60)
    print("WEB APPLICATION DEMO")
    print("=" * 60)
    
    # In a web app, the API key would be:
    # 1. Entered by user in a form
    # 2. Stored in session (not in code!)
    # 3. Passed to MCP client for each request
    
    class WebSession:
        def __init__(self):
            self.user_id = "user-123"
            self.api_key = None  # Set when user logs in
            
    session = WebSession()
    
    print("\n1. User visits website (no API key)")
    async with MCPClient("http://localhost:8000") as client:
        agent = SkyFiMCPAgent(client)
        print("   Available: Weather, OSM tools")
        await agent.get_weather("London, UK")
        
    print("\n2. User enters their API key")
    session.api_key = "user-provided-api-key"
    
    print("\n3. Now user has full access")
    async with MCPClient("http://localhost:8000", api_key=session.api_key) as client:
        agent = SkyFiMCPAgent(client)
        print("   Available: All tools including SkyFi")
        await agent.search_satellite_imagery("Big Ben, London")


async def main():
    """Run all demos."""
    print("🚀 MCP SDK Demo - Proper Authentication Patterns")
    print("=" * 60)
    print("\nThis demonstrates how to properly pass API keys via headers")
    print("instead of storing them in configuration files.\n")
    
    # Run demos
    await demo_enterprise_usage()
    await demo_web_app_usage()
    
    print("\n" + "=" * 60)
    print("✅ KEY TAKEAWAYS:")
    print("=" * 60)
    print("1. API keys are passed in HTTP headers, not config files")
    print("2. Each user/session gets their own MCP client instance")
    print("3. The server validates keys and provides appropriate tools")
    print("4. No API keys are stored in code or static configs")
    print("5. This follows the MCP philosophy for multi-tenant usage")


if __name__ == "__main__":
    asyncio.run(main())