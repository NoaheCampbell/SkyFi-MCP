"""HTTP/SSE server implementation for SkyFi MCP."""
import logging
import os
import json
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import anyio

from ..skyfi.tools import register_skyfi_tools
from ..skyfi.config import SkyFiConfig
from ..weather.tools import register_weather_tools
from ..osm.tools import register_osm_tools
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)


class SkyFiHTTPServer:
    """HTTP/SSE server for SkyFi MCP with header-based authentication."""
    
    def __init__(self):
        """Initialize the HTTP server."""
        self.mcp_server = Server("mcp-skyfi")
        self.app = FastAPI(title="SkyFi MCP Server")
        self.setup_middleware()
        self.setup_routes()
        self.setup_mcp_handlers()
        setup_logging(level=os.getenv("MCP_LOG_LEVEL", "INFO"))
    
    def setup_middleware(self):
        """Set up FastAPI middleware."""
        # Add CORS middleware for browser-based clients
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Set up HTTP routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "name": "SkyFi MCP Server",
                "version": "0.1.0",
                "transport": "sse",
                "endpoints": {
                    "sse": "/sse",
                    "health": "/health",
                    "tools_call": "/tools/call"
                }
            }
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return {"status": "healthy"}
        
        @self.app.post("/tools/call")
        async def call_tool_http(
            request: Request,
            authorization: Optional[str] = Header(None),
            x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
            x_skyfi_api_key: Optional[str] = Header(None, alias="X-Skyfi-Api-Key")
        ):
            """Direct HTTP endpoint for tool calls."""
            # Extract API key
            api_key = None
            if x_skyfi_api_key:
                api_key = x_skyfi_api_key
            elif x_api_key:
                api_key = x_api_key
            elif authorization and authorization.startswith("Bearer "):
                api_key = authorization[7:]
            
            if api_key:
                os.environ["SKYFI_API_KEY"] = api_key
            
            # Get request body
            body = await request.json()
            tool_name = body.get("name")
            arguments = body.get("arguments", {})
            
            # Import tool handlers
            from ..skyfi.tools import call_skyfi_tool
            from ..weather.tools import call_weather_tool
            from ..osm.tools import call_osm_tool
            
            # Call the appropriate tool
            try:
                if tool_name.startswith("skyfi_"):
                    if not api_key:
                        return {"error": "SkyFi API key required"}
                    result = await call_skyfi_tool(tool_name, arguments)
                elif tool_name.startswith("weather_"):
                    result = await call_weather_tool(tool_name, arguments)
                elif tool_name.startswith("osm_"):
                    result = await call_osm_tool(tool_name, arguments)
                else:
                    return {"error": f"Unknown tool: {tool_name}"}
                
                # Convert MCP response to JSON
                if result and isinstance(result, list) and len(result) > 0:
                    content = result[0]
                    if content.type == "text":
                        try:
                            return json.loads(content.text)
                        except:
                            return {"text": content.text}
                return {"result": str(result)}
                
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                return {"error": str(e)}
        
        @self.app.get("/sse")
        async def handle_sse(
            request: Request,
            authorization: Optional[str] = Header(None),
            x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
            x_skyfi_api_key: Optional[str] = Header(None, alias="X-Skyfi-Api-Key")
        ):
            """Handle SSE connection with authentication."""
            # Extract API key from various header formats
            api_key = None
            
            if x_skyfi_api_key:
                api_key = x_skyfi_api_key
            elif x_api_key:
                api_key = x_api_key
            elif authorization and authorization.startswith("Bearer "):
                api_key = authorization[7:]
            
            # Store API key in request state for use by tools
            if api_key:
                logger.info("API key provided via headers")
                os.environ["SKYFI_API_KEY"] = api_key
            else:
                logger.warning("No API key provided in headers")
            
            # Create SSE response
            async def event_generator():
                # Create memory streams for SSE transport
                read_stream, write_stream = anyio.create_memory_object_stream()
                
                # Create SSE transport
                transport = SseServerTransport(
                    request.scope,
                    request.receive,
                    request._send
                )
                
                # Run server in background
                async with anyio.create_task_group() as tg:
                    tg.start_soon(
                        self.mcp_server.run,
                        read_stream,
                        write_stream,
                        InitializationOptions(
                            server_name="mcp-skyfi",
                            server_version="0.1.0"
                        )
                    )
                    
                    # Stream events
                    async for message in transport:
                        if message["type"] == "http.response.body":
                            yield message["body"].decode()
            
            return EventSourceResponse(event_generator())
    
    def setup_mcp_handlers(self):
        """Set up MCP server handlers."""
        
        @self.mcp_server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """Return all available tools."""
            tools = []
            
            # Check if API key is available
            has_api_key = bool(os.getenv("SKYFI_API_KEY"))
            
            # Always register weather and OSM tools (no API key needed)
            tools.extend(await register_weather_tools())
            tools.extend(await register_osm_tools())
            
            # Only register SkyFi tools if API key is available
            if has_api_key:
                tools.extend(await register_skyfi_tools())
            else:
                logger.info("SkyFi tools not registered - no API key provided")
            
            return tools
        
        @self.mcp_server.call_tool()
        async def handle_call_tool(
            name: str, 
            arguments: Optional[Dict[str, Any]]
        ) -> List[TextContent | ImageContent | EmbeddedResource]:
            """Handle tool execution."""
            logger.info(f"Executing tool: {name} with arguments: {arguments}")
            
            # Import tool handlers
            from ..skyfi.tools import call_skyfi_tool
            from ..weather.tools import call_weather_tool
            from ..osm.tools import call_osm_tool
            
            # Route to appropriate handler
            if name.startswith("skyfi_"):
                # Check API key for SkyFi tools
                if not os.getenv("SKYFI_API_KEY"):
                    return [TextContent(
                        type="text",
                        text="Error: SkyFi API key required. Please provide via Authorization header."
                    )]
                return await call_skyfi_tool(name, arguments or {})
            elif name.startswith("weather_"):
                return await call_weather_tool(name, arguments or {})
            elif name.startswith("osm_"):
                return await call_osm_tool(name, arguments or {})
            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the HTTP server."""
        import uvicorn
        logger.info(f"Starting HTTP/SSE server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


# Create global server instance
http_server = SkyFiHTTPServer()
app = http_server.app