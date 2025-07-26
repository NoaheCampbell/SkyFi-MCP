"""MCP server that accepts API keys via headers."""
import logging
from typing import Any, Dict

from mcp import McpError, Server
from mcp.server import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    GetPromptResult, 
    Prompt,
    PromptMessage,
    TextContent,
    Tool,
    CallToolRequest,
    CallToolResult,
)

from ..auth.header_auth import header_auth
from ..auth import auth_manager
from ..skyfi.tools import register_skyfi_tools
from ..skyfi.handlers import handle_skyfi_tool
from ..osm.tools import register_osm_tools  
from ..osm.handlers import handle_osm_tool

logger = logging.getLogger(__name__)


class HeaderAwareServer(Server):
    """MCP server that extracts API keys from request headers."""
    
    def __init__(self):
        super().__init__("mcp-skyfi")
        self.tools = []
    
    async def initialize(self, params: InitializationOptions) -> None:
        """Initialize the server with header support."""
        logger.info("Initializing header-aware SkyFi MCP server")
        
        # Check if we have client info with headers
        client_info = params.client_info if hasattr(params, 'client_info') else {}
        logger.debug(f"Client info: {client_info}")
        
        # Register all tools
        skyfi_tools = await register_skyfi_tools()
        osm_tools = await register_osm_tools()
        self.tools = skyfi_tools + osm_tools
        
        logger.info(f"Registered {len(self.tools)} tools")
    
    async def handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool calls with header extraction."""
        try:
            # Extract API key from request context if available
            context = getattr(request, 'context', {})
            api_key = header_auth.extract_api_key_from_context(context)
            
            if api_key:
                # Set the API key for this request
                header_auth.set_context_api_key(api_key)
                auth_manager.set_api_key(api_key)
                logger.debug("API key set from request headers")
            
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
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )
        finally:
            # Clear context after request
            header_auth.clear_context()
    
    async def handle_list_tools(self) -> list[Tool]:
        """Return available tools."""
        # Filter out auth tools if using header auth
        return [
            tool for tool in self.tools 
            if tool.name not in ["skyfi_set_api_key", "skyfi_check_auth"]
        ]


async def run_header_server():
    """Run the header-aware MCP server."""
    logging.basicConfig(level=logging.INFO)
    
    async with HeaderAwareServer() as server:
        await stdio_server(
            server=server,
            initialization_options=InitializationOptions(
                server_name="mcp-skyfi",
                server_version="0.1.0",
                capabilities=NotificationOptions(prompts_changed=False)
            )
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_header_server())