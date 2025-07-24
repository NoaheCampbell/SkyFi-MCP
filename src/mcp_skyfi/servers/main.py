"""Main MCP server implementation for SkyFi."""
import logging
import os
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from ..skyfi.tools import register_skyfi_tools
from ..weather.tools import register_weather_tools
from ..osm.tools import register_osm_tools
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)


class SkyFiMCPServer:
    """MCP server for SkyFi satellite imagery and geospatial tools."""
    
    def __init__(self):
        """Initialize the SkyFi MCP server."""
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
            
            # Register tools from each service
            tools.extend(await register_skyfi_tools())
            tools.extend(await register_weather_tools())
            tools.extend(await register_osm_tools())
            
            return tools
        
        # Register tool call handler
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[TextContent | ImageContent | EmbeddedResource]:
            """Handle tool calls."""
            logger.info(f"Tool called: {name} with arguments: {arguments}")
            
            # Import tool handlers dynamically to avoid circular imports
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
        logger.info("Starting SkyFi MCP server with STDIO transport")
        
        # Run the stdio server
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
    
    async def run_http(self, host: str, port: int) -> None:
        """Run the server with HTTP transport."""
        # Note: HTTP transport would require additional implementation
        # This is a placeholder for future enhancement
        raise NotImplementedError("HTTP transport not yet implemented")