"""MCP SkyFi Server - Satellite imagery and geospatial tools."""
import asyncio
import sys
from typing import Optional

import click
from dotenv import load_dotenv

from .servers.main import SkyFiMCPServer


@click.command()
@click.option("--host", default="127.0.0.1", help="HTTP server host")
@click.option("--port", default=8080, help="HTTP server port")
@click.option("--transport", type=click.Choice(["stdio", "http"]), default="stdio", help="Transport type")
def main(host: str, port: int, transport: str) -> None:
    """Run the SkyFi MCP server."""
    load_dotenv()
    
    if transport == "stdio":
        server = SkyFiMCPServer()
        asyncio.run(server.run_stdio())
    else:
        # Use HTTP server
        import uvicorn
        from .servers.http_server import create_http_server
        
        app = create_http_server()
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()