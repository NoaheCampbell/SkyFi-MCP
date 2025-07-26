"""Public MCP server that accepts API keys from users."""
import logging
import os
from typing import Any, Dict

from mcp import Server
from mcp.server import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
    CallToolRequest,
    CallToolResult,
)

from ..skyfi.tools import register_skyfi_tools
from ..skyfi.handlers import handle_skyfi_tool
from ..osm.tools import register_osm_tools  
from ..osm.handlers import handle_osm_tool

logger = logging.getLogger(__name__)


class PublicSkyFiServer(Server):
    """Public MCP server where users provide their own API keys."""
    
    def __init__(self):
        super().__init__("skyfi-public")
        self.tools = []
        
        # Override config to not require API key on startup
        os.environ['SKYFI_API_KEY'] = 'PENDING_USER_AUTH'
    
    async def initialize(self, params: InitializationOptions) -> None:
        """Initialize the server."""
        logger.info("Initializing public SkyFi MCP server")
        
        # Register all tools
        skyfi_tools = await register_skyfi_tools()
        osm_tools = await register_osm_tools()
        self.tools = skyfi_tools + osm_tools
        
        # Make sure auth tools are at the beginning
        auth_tools = ['skyfi_check_auth', 'skyfi_set_api_key']
        self.tools.sort(key=lambda t: 0 if t.name in auth_tools else 1)
        
        logger.info(f"Registered {len(self.tools)} tools")
        logger.info("Server ready - users must set their API key using skyfi_set_api_key")
    
    async def handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool calls."""
        try:
            # Route to appropriate handler
            if request.params.name.startswith("skyfi_"):
                result = await handle_skyfi_tool(
                    request.params.name,
                    request.params.arguments or {}
                )
            elif request.params.name.startswith("osm_"):
                result = await handle_osm_tool(
                    request.params.name,
                    request.params.arguments or {}
                )
            else:
                raise ValueError(f"Unknown tool: {request.params.name}")
            
            return CallToolResult(content=result)
            
        except Exception as e:
            logger.error(f"Error in tool {request.params.name}: {e}", exc_info=True)
            
            # Special handling for auth errors
            if "API key not configured" in str(e) or "PENDING_USER_AUTH" in str(e):
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=(
                            "❌ No API key configured!\n\n"
                            "To use SkyFi tools, you must first set your API key:\n\n"
                            "1. Get your API key from https://app.skyfi.com\n"
                            "2. Use: skyfi_set_api_key with your key\n\n"
                            "Example: Use skyfi_set_api_key with api_key 'sk-your-key-here'"
                        )
                    )]
                )
            
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )
    
    async def handle_list_tools(self) -> list[Tool]:
        """Return available tools."""
        return self.tools


async def run_public_server():
    """Run the public MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting public SkyFi MCP server")
    logger.info("Users must provide their own API keys")
    
    async with PublicSkyFiServer() as server:
        await stdio_server(
            server=server,
            initialization_options=InitializationOptions(
                server_name="skyfi-public",
                server_version="1.0.0",
                capabilities=NotificationOptions(prompts_changed=False)
            )
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_public_server())