"""Public MCP server that accepts API key through tool calls."""
import os
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from ..skyfi.tools import register_skyfi_tools
from ..weather.tools import register_weather_tools
from ..osm.tools import register_osm_tools
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)

# Global storage for API keys per session
SESSION_API_KEYS = {}


class PublicSkyFiMCPServer:
    """MCP server that accepts API key through tool calls."""
    
    def __init__(self):
        """Initialize the public SkyFi MCP server."""
        self.server = Server("mcp-skyfi")
        self.setup_server()
        setup_logging(level=os.getenv("MCP_LOG_LEVEL", "INFO"))
    
    def setup_server(self) -> None:
        """Set up server handlers and tools."""
        
        # Register list_tools handler
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """Return all available tools."""
            tools = []
            
            # Always include set_api_key tool
            tools.append(Tool(
                name="set_api_key",
                description="Set your SkyFi API key for this session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "description": "Your SkyFi API key (get from app.skyfi.com)"
                        }
                    },
                    "required": ["api_key"]
                }
            ))
            
            # Include all tools (SkyFi tools will check for API key when called)
            tools.extend(await register_skyfi_tools())
            tools.extend(await register_weather_tools())
            tools.extend(await register_osm_tools())
            
            return tools
        
        # Register tool call handler
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[TextContent | ImageContent | EmbeddedResource]:
            """Handle tool calls."""
            logger.info(f"Tool called: {name} with arguments: {arguments}")
            
            # Handle set_api_key tool
            if name == "set_api_key":
                api_key = arguments.get("api_key", "").strip()
                if not api_key:
                    return [TextContent(
                        type="text",
                        text="Error: API key cannot be empty"
                    )]
                
                # Set the API key in environment for this session
                os.environ["SKYFI_API_KEY"] = api_key
                
                # Test if it's valid by trying to create a client
                try:
                    from ..skyfi.client import SkyFiClient
                    from ..skyfi.config import SkyFiConfig
                    config = SkyFiConfig(api_key=api_key)
                    # Just create the client to validate the format
                    client = SkyFiClient(config)
                    
                    return [TextContent(
                        type="text",
                        text=f"✓ API key set successfully! You can now use all SkyFi tools.\n\nYour key: {api_key[:20]}..."
                    )]
                except Exception as e:
                    return [TextContent(
                        type="text",
                        text=f"Error setting API key: {str(e)}"
                    )]
            
            # For SkyFi tools, check if API key is set
            if name.startswith("skyfi_") and not os.getenv("SKYFI_API_KEY"):
                return [TextContent(
                    type="text",
                    text="Please set your API key first using the 'set_api_key' tool.\nGet your API key from app.skyfi.com"
                )]
            
            # Import tool handlers dynamically
            if name.startswith("skyfi_"):
                from ..skyfi.handlers import handle_skyfi_tool
                return await handle_skyfi_tool(name, arguments or {})
            elif name.startswith("weather_"):
                from ..weather.handlers import handle_weather_tool
                return await handle_weather_tool(name, arguments or {})
            elif name.startswith("osm_"):
                from ..osm.handlers import handle_osm_tool
                return await handle_osm_tool(name, arguments or {})
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def run_stdio(self) -> None:
        """Run the server with STDIO transport."""
        logger.info("Starting public SkyFi MCP server")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-skyfi",
                    server_version="0.1.0",
                    capabilities={}
                ),
            )


async def main():
    """Run the public MCP server."""
    server = PublicSkyFiMCPServer()
    await server.run_stdio()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())